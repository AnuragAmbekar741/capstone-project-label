#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# python train.py --mails C:/Users/kunal/Desktop/college/capstone/jsonfiles/ --model_out_dir C:/Users/kunal/Desktop/college/capstone/model_tf_base/
# accelerate launch train.py --corpus_dir "C:/Users/kunal/Desktop/college/capstone/training/mail-data/" --model_out_dir "C:/Users/kunal/Desktop/college/capstone/training/model_tf_base/" --train
# accelerate launch train.py --corpus_dir "C:/Users/kunal/Desktop/college/capstone/training/mail-data/" --model_out_dir "C:/Users/kunal/Desktop/college/capstone/training/model_tf_base/" --base_model C:/Users/kunal/Desktop/college/capstone/training/model_tf_base/final_model --version_mode long --test

"""
EmailSum-style training on Enron threads:
- Builds EmailSum-style .source/.target (one thread per line; messages joined by " ||| ")
- Supports two presets: short (≈56) and long (≈128) outputs, like the EmailSum README.
- Train / Evaluate / Test in one script; saves checkpoints and a final model.

References:
- EmailSum repository README: one thread per line with "|||" separators + short/long configs.
"""

import os, sys, re, json, math, random, argparse, logging
from datetime import datetime
from typing import Dict, Any, Iterable, List, Tuple

import torch
from torch.utils.data import Dataset

from transformers import (
    AutoTokenizer, AutoModelForSeq2SeqLM,
    DataCollatorForSeq2Seq, Seq2SeqTrainer, Seq2SeqTrainingArguments, TrainerCallback
)

# Optional: PEFT (LoRA)
try:
    from peft import LoraConfig, get_peft_model, TaskType
    PEFT_OK = True
except Exception:
    PEFT_OK = False

# Optional: ROUGE
try:
    from evaluate import load as load_metric
    EVAL_OK = True
except Exception:
    EVAL_OK = False

os.environ.setdefault("TOKENIZERS_PARALLELISM", "true")

# torch.set_num_threads(12)


# ---------------------------
# Logging
# ---------------------------
def setup_logger(log_dir: str, log_name: str) -> str:
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, log_name)
    fmt = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s", datefmt="%H:%M:%S")
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(logging.INFO)

    fh = logging.FileHandler(log_path, mode="w", encoding="utf-8")
    fh.setFormatter(fmt)
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(fmt)

    root.addHandler(ch); root.addHandler(fh)
    logging.info("Logging to %s", log_path)
    return log_path


# ---------------------------
# EmailSum-style formatting
# ---------------------------
WS = re.compile(r"\s+")
def _nw(s: str) -> str: return WS.sub(" ", (s or "").strip())

def join_thread_messages_email_sum(thread: Dict[str, Any]) -> str:
    """
    Build a single 'source' line for EmailSum:
    emails are concatenated with ' ||| ' in chronological order.
    """
    msgs = thread.get("messages", []) or []
    parts = []
    for m in msgs:
        txt = _nw(m.get("text") or m.get("body_text") or "")
        if txt:
            parts.append(txt)
    return " ||| ".join(parts)

def weak_target_summary(thread: Dict[str, Any], max_len_chars: int = 512) -> str:
    """
    Weak summary if you don't have gold refs (EmailSum did semi-supervised with W3C).
    We use subject + salient sentences from the last message.
    """
    subject = _nw(thread.get("subject_norm", "") or thread.get("subject", ""))
    last = ""
    msgs = thread.get("messages", [])
    if msgs:
        last = _nw(msgs[-1].get("text") or msgs[-1].get("body_text") or "")
    sents = re.split(r"(?<=[.!?])\s+", last)
    sents = [s.strip() for s in sents if s.strip()]
    sents.sort(key=len, reverse=True)
    tgt = " ".join(([subject] if subject else []) + sents[:2]).strip()
    if not tgt:
        tgt = " ".join(last.split()[:30])
    return _nw(tgt)[:max_len_chars]


# ---------------------------
# Data loading
# ---------------------------
def stream_jsonl(path: str):
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip(): continue
            try:
                yield json.loads(line)
            except Exception:
                continue

def pick_split_paths(corpus_dir: str, split: str) -> str:
    """
    Prefer EmailSum-style split folders if present:
       <corpus_dir>/splits/<split>/threads.jsonl
    else fallback to <corpus_dir>/threads.jsonl (and split randomly later).
    """
    p_split = os.path.join(corpus_dir, "splits", split, "threads.jsonl")
    if os.path.exists(p_split):
        return p_split
    return os.path.join(corpus_dir, "threads.jsonl")

def prepare_email_sum_files(threads_path: str,
                            out_dir: str,
                            build_targets: bool,
                            split_name: str,
                            seed: int = 42,
                            rand_split: Tuple[float,float,float] = (0.86, 0.07, 0.07),
                            limit: int = 0) -> Tuple[str, str]:
    """
    Build *.source / *.target in out_dir/email_sum/<split_name>/ from threads.jsonl.

    If threads_path is the root threads.jsonl (no pre-splits), we randomly split here
    using rand_split for train/val/test with the given seed.
    """
    split_dir = os.path.join(out_dir, "email_sum", split_name)
    os.makedirs(split_dir, exist_ok=True)
    src_path = os.path.join(split_dir, f"{split_name}.source")
    tgt_path = os.path.join(split_dir, f"{split_name}.target")

    # If we detect root threads.jsonl and asked for a split other than 'train',
    # we may need to subsample; but to keep deterministic behavior, we simply
    # consume in order and assign by RNG when called for each split.
    rng = random.Random(seed)

    # When building 'train/val/test' from one file, we let the caller pass the same
    # threads_path but different split_name; we write only the matching portion each time.
    want = split_name  # "train" | "val" | "test"
    train_p, val_p, test_p = rand_split
    total_frac = train_p + val_p + test_p
    train_p, val_p, test_p = (train_p/total_frac, val_p/total_frac, test_p/total_frac)

    n_kept = 0
    with open(src_path, "w", encoding="utf-8") as wsrc, \
         open(tgt_path, "w", encoding="utf-8") as wtgt:
        for i, thr in enumerate(stream_jsonl(threads_path), start=1):
            # if we're reading pre-split folders (splits/<split>/threads.jsonl), accept all
            pre_split = "splits" in threads_path.replace("\\","/").split("/")
            if not pre_split:
                r = rng.random()
                assign = "train"
                if r > train_p:
                    assign = "val" if r <= train_p + val_p else "test"
                if assign != want:
                    continue

            src = join_thread_messages_email_sum(thr)
            if len(src) < 40:
                continue

            tgt = weak_target_summary(thr) if build_targets else ""
            wsrc.write(src + "\n")
            if build_targets:
                wtgt.write(tgt + "\n")
            n_kept += 1
            if limit and n_kept >= limit:
                break

    logging.info("Built %s: %d examples", split_name, n_kept)
    return src_path, (tgt_path if build_targets else "")


# ---------------------------
# Dataset
# ---------------------------
class EmailSumDataset(Dataset):
    def __init__(self, src_path: str, tgt_path: str, tokenizer, max_input_len: int, max_target_len: int):
        self.tok = tokenizer
        self.max_in = max_input_len
        self.max_out = max_target_len

        with open(src_path, "r", encoding="utf-8") as f:
            self.sources = [ln.rstrip("\n") for ln in f]
        if tgt_path and os.path.exists(tgt_path):
            with open(tgt_path, "r", encoding="utf-8") as f:
                self.targets = [ln.rstrip("\n") for ln in f]
        else:
            self.targets = [""] * len(self.sources)

        assert len(self.sources) == len(self.targets), "source/target size mismatch"

    def __len__(self): return len(self.sources)

    def __getitem__(self, idx):
        x = self.sources[idx]
        y = self.targets[idx]
        enc = self.tok(x, max_length=self.max_in, truncation=True, padding=False)
        with self.tok.as_target_tokenizer():
            lab = self.tok(y, max_length=self.max_out, truncation=True, padding=False)["input_ids"]
        enc["labels"] = lab
        return {k: torch.tensor(v) for k, v in enc.items()}


# ---------------------------
# Train / Eval / Test
# ---------------------------
def build_datasets_emailsum(corpus_dir: str,
                            work_dir: str,
                            version_mode: str,
                            seed: int,
                            use_gold_targets: bool,
                            limit_train: int = 0,
                            limit_val: int = 0,
                            limit_test: int = 0):
    # presets per EmailSum README
    if version_mode == "short":
        max_out = 56    # they use 56 for short summaries
    else:
        version_mode = "long"
        max_out = 128   # they use 128 for long summaries

    # prefer split folders if present; else: random split from root threads.jsonl
    paths = {}
    for split in ("train", "val", "test"):
        tp = pick_split_paths(corpus_dir, split)
        src, tgt = prepare_email_sum_files(
            threads_path=tp,
            out_dir=work_dir,
            build_targets=True,  # weak targets for all splits unless you have gold refs
            split_name=split,
            seed=seed
        )
        paths[split] = (src, tgt)

    return paths, max_out


def compute_rouge(preds: List[str], refs: List[str]) -> Dict[str, float]:
    if not EVAL_OK:
        logging.warning("`evaluate` not installed; skipping ROUGE. pip install evaluate rouge-score")
        return {}
    rouge = load_metric("rouge")
    res = rouge.compute(predictions=preds, references=refs, use_stemmer=True)
    return {
        "rouge1_f": round(res["rouge1"] * 100, 2),
        "rouge2_f": round(res["rouge2"] * 100, 2),
        "rougeL_f": round(res["rougeL"] * 100, 2),
    }


def run(args):

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = setup_logger(args.model_out_dir, f"train_emailsum_{args.version_mode}_{timestamp}.log")
    log_file = open(log_path, "a", buffering=1, encoding="utf-8")
    logging.getLogger("transformers").addHandler(logging.FileHandler(log_path, mode="a", encoding="utf-8"))
    logging.getLogger("transformers").setLevel(logging.INFO)
    logging.getLogger("transformers.trainer").addHandler(logging.FileHandler(log_path, mode="a", encoding="utf-8"))
    logging.getLogger("transformers.trainer").setLevel(logging.INFO)
    sys.stdout = sys.__stdout__  # reset any redirection (safety)
    sys.stderr = sys.__stderr__
    sys.stdout = log_file
    sys.stderr = log_file
    logging.info("Args: %s", vars(args))
    logging.info("CUDA available: %s | device_count=%s",
                 torch.cuda.is_available(), torch.cuda.device_count())

    # 1) Build EmailSum-style files & datasets
    paths, max_out_len = build_datasets_emailsum(
        corpus_dir=args.corpus_dir,
        work_dir=args.tmp_out_dir,
        version_mode=args.version_mode,
        seed=args.seed,
        use_gold_targets=False,
        limit_train=args.limit_train,
        limit_val=args.limit_val,
        limit_test=args.limit_test
    )

    tok = AutoTokenizer.from_pretrained(args.base_model, use_fast=True)
    model = AutoModelForSeq2SeqLM.from_pretrained(args.base_model)

    if PEFT_OK and str(args.use_lora).lower() == "true":
        lora_cfg = LoraConfig(
            r=args.lora_r, lora_alpha=args.lora_alpha, lora_dropout=args.lora_dropout,
            bias="none", task_type=TaskType.SEQ_2_SEQ_LM
        )
        model = get_peft_model(model, lora_cfg)
        model.print_trainable_parameters()
    else:
        logging.info("LoRA disabled or PEFT not available; full fine-tuning.")

    # IMPORTANT if you enable gradient checkpointing
    if str(args.grad_checkpoint).lower() == "true":
        model.config.use_cache = False
        try: model.gradient_checkpointing_enable()
        except: pass
        try: model.enable_input_require_grads()
        except: pass

    # Build datasets
    train_ds = EmailSumDataset(paths["train"][0], paths["train"][1], tok, args.max_input_len, max_out_len)
    val_ds   = EmailSumDataset(paths["val"][0],   paths["val"][1],   tok, args.max_input_len, max_out_len)
    test_ds  = EmailSumDataset(paths["test"][0],  paths["test"][1],  tok, args.max_input_len, max_out_len)

    data_collator = DataCollatorForSeq2Seq(tok, model=model)

    # 2) Trainer args (EmailSum trains normally; we keep step-ckpts + resume)
    training_args = Seq2SeqTrainingArguments(
        output_dir=os.path.join(args.model_out_dir, "hf_ckpts"),
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.eval_batch_size,
        gradient_accumulation_steps=args.grad_accum,
        learning_rate=args.lr,
        warmup_steps=args.warmup_steps,

        eval_strategy="steps",
        eval_steps=max(500, args.eval_steps),
        logging_steps=50,

        save_strategy="steps",
        save_steps=max(500, args.save_steps),
        save_total_limit=3,
        save_safetensors=True,

        dataloader_num_workers=args.num_workers,     # use multiple workers
        dataloader_pin_memory=True,                  # faster H2D copies
        dataloader_persistent_workers=True,

        predict_with_generate=True,
        generation_max_length=max_out_len,
        fp16=torch.cuda.is_available(),
        bf16=False,
        report_to=[],
        gradient_checkpointing=(str(args.grad_checkpoint).lower() == "true"),
        load_best_model_at_end=True,
        metric_for_best_model="loss",
        greater_is_better=False,
    )

    trainer = Seq2SeqTrainer(
        model=model,
        args=training_args,
        train_dataset=train_ds if args.train else None,
        eval_dataset=val_ds if (args.train or args.eval) else None,
        data_collator=data_collator,
        tokenizer=tok
    )

    # 3) Train (resume if a ckpt exists)
    if args.train:
        ckpt_dir = training_args.output_dir
        last_ckpt = None
        if os.path.isdir(ckpt_dir):
            # HuggingFace helper to find last checkpoint dir if any
            try:
                from transformers.trainer_utils import get_last_checkpoint
                last_ckpt = get_last_checkpoint(ckpt_dir)
            except Exception:
                last_ckpt = None

        if last_ckpt:
            logging.info("Resuming from checkpoint: %s", last_ckpt)
            trainer.train(resume_from_checkpoint=last_ckpt)
        else:
            logging.info("Starting fresh training.")
            trainer.train()

        # save final
        final_dir = os.path.join(args.model_out_dir, "final_model")
        os.makedirs(final_dir, exist_ok=True)
        trainer.save_model(final_dir)
        tok.save_pretrained(final_dir)
        logging.info("Saved final model to %s", final_dir)

    # 4) Evaluate on dev (ROUGE)
    if args.eval:
        logging.info("Evaluating on validation set…")
        # Avoid very long/VRAM-heavy gen in eval; we already set generation_max_length
        out = trainer.predict(val_ds, metric_key_prefix="val")
        metrics = {}
        if EVAL_OK:
            preds = tok.batch_decode(out.predictions, skip_special_tokens=True)
            refs = [t for t in val_ds.targets]
            metrics = compute_rouge(preds, refs)
            logging.info("VAL ROUGE: %s", metrics)
        eval_report = {
            "n_val": len(val_ds),
            "hf_metrics": {k: float(v) for k,v in (out.metrics or {}).items()},
            "rouge": metrics
        }
        os.makedirs(args.model_out_dir, exist_ok=True)
        with open(os.path.join(args.model_out_dir, f"eval_val_{args.version_mode}.json"), "w", encoding="utf-8") as f:
            json.dump(eval_report, f, indent=2, ensure_ascii=False)
        logging.info("Wrote %s", f.name)

    # 5) Test (ROUGE)
    if args.test:
        logging.info("Testing on test set…")
        print("testing")
        # Use best (already loaded by load_best_model_at_end when training); otherwise current model.
        gen_kwargs = dict(max_new_tokens=max_out_len, num_beams=4, no_repeat_ngram_size=3)
        preds = []
        for i in range(0, len(test_ds), 4):
            batch = [test_ds.sources[j] for j in range(i, min(i+4, len(test_ds)))]
            enc = tok(batch, return_tensors="pt", padding=True, truncation=True, max_length=args.max_input_len).to(trainer.model.device)
            with torch.no_grad():
                out = trainer.model.generate(**enc, **gen_kwargs)
            preds.extend(tok.batch_decode(out, skip_special_tokens=True))
        refs = [t for t in test_ds.targets]
        metrics = compute_rouge(preds, refs) if EVAL_OK else {}
        test_report = {
            "n_test": len(test_ds),
            "rouge": metrics
        }
        with open(os.path.join(args.model_out_dir, f"eval_test_{args.version_mode}.json"), "w", encoding="utf-8") as f:
            json.dump(test_report, f, indent=2, ensure_ascii=False)
        # Save raw predictions to inspect/human-judge
        out_dir_preds = os.path.join(args.model_out_dir, "preds")
        os.makedirs(out_dir_preds, exist_ok=True)
        with open(os.path.join(out_dir_preds, f"test_{args.version_mode}.jsonl"), "w", encoding="utf-8") as w:
            for src, ref, pr in zip(test_ds.sources, refs, preds):
                w.write(json.dumps({"source": src, "reference": ref, "prediction": pr}, ensure_ascii=False) + "\n")
        logging.info("Test ROUGE: %s", metrics)
        logging.info("Wrote predictions to %s", out_dir_preds)


# ---------------------------
# CLI
# ---------------------------
def parse_args():
    ap = argparse.ArgumentParser(description="Train/Eval/Test EmailSum-style model on Enron threads")
    # Data
    ap.add_argument("--corpus_dir", required=True, help="Folder with threads.jsonl (and optionally splits/train|val|test/threads.jsonl)")
    ap.add_argument("--tmp_out_dir", default="runs/email_sum_cache", help="Where to write *.source/*.target")
    ap.add_argument("--model_out_dir", required=True, help="Where to save checkpoints, reports, and final model")

    # Task preset like EmailSum
    ap.add_argument("--version_mode", choices=["short","long"], default="long", help="EmailSum preset: short(56) or long(128)")

    # Model / Tokenization
    # ap.add_argument("--base_model", default="google/flan-t5-large", help="Seq2seq model id (EmailSum used T5; BART also works)")
    ap.add_argument("--base_model", default="t5-base", help="Seq2seq model id (EmailSum used T5; BART also works)")
    ap.add_argument("--max_input_len", type=int, default=1024, help="Max encoder tokens")

    # Train schedule
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--batch_size", type=int, default=4)
    ap.add_argument("--eval_batch_size", type=int, default=4, help="per-device eval batch size")
    ap.add_argument("--grad_accum", type=int, default=2)
    ap.add_argument("--lr", type=float, default=5e-5)
    ap.add_argument("--warmup_steps", type=int, default=1000)
    ap.add_argument("--save_steps", type=int, default=1000)
    ap.add_argument("--eval_steps", type=int, default=1000)
    ap.add_argument("--grad_checkpoint", default="false")
    ap.add_argument("--num_workers", type=int, default=12, help="DataLoader workers for train/eval")

    # What to run
    ap.add_argument("--train", action="store_true", help="Run training")
    ap.add_argument("--eval", action="store_true", help="Evaluate on validation set")
    ap.add_argument("--test", action="store_true", help="Test on test set")

    # Limits (debug)
    ap.add_argument("--limit_train", type=int, default=0)
    ap.add_argument("--limit_val", type=int, default=0)
    ap.add_argument("--limit_test", type=int, default=0)

    # LoRA
    ap.add_argument("--use_lora", default="true")
    ap.add_argument("--lora_r", type=int, default=8)
    ap.add_argument("--lora_alpha", type=int, default=16)
    ap.add_argument("--lora_dropout", type=float, default=0.05)
    

    # Misc
    ap.add_argument("--seed", type=int, default=42)
    return ap.parse_args()


if __name__ == "__main__":
    args = parse_args()
    os.makedirs(args.tmp_out_dir, exist_ok=True)
    os.makedirs(args.model_out_dir, exist_ok=True)
    run(args)
