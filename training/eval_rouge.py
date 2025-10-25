#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Evaluate a merged/full HF seq2seq model directly from threads.jsonl
(created by your earlier pipeline), without test.source/test.target files.

Each line in threads.jsonl should be a JSON object with:
  - messages: list of { "from"|"frm", "text" } (names are configurable)
  - reference summary in one of: "summary", "target", "reference" (configurable)

Outputs:
  <out_dir>/eval_threads.json   # ROUGE (if references found) + run info
  <out_dir>/preds_threads.jsonl # {"source","reference"(opt),"prediction"} per example

Run (Windows example):
  accelerate launch eval_rouge_from_threads.py ^
    --model_dir "C:\...\model_tf_base\full_model" ^
    --threads_jsonl "C:\...\mail-data\splits\test\threads.jsonl" ^
    --out_dir "C:\...\runs\eval_full_model" ^
    --max_input_len 1024 --max_new_tokens 128 --num_beams 4
"""

import os, json, argparse
from typing import List, Tuple, Dict, Any
from tqdm import tqdm

import torch
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, DataCollatorForSeq2Seq

def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model_dir", required=True, help="Path to merged/full model (folder with config.json).")
    ap.add_argument("--corpus_dir", required=True, help="Path to threads.jsonl to evaluate on.")
    ap.add_argument("--out_dir", required=True, help="Where to write metrics/preds.")
    # decoding / batching
    ap.add_argument("--max_input_len", type=int, default=1024)
    ap.add_argument("--max_new_tokens", type=int, default=128)
    ap.add_argument("--num_beams", type=int, default=4)
    ap.add_argument("--no_repeat_ngram_size", type=int, default=3)
    ap.add_argument("--length_penalty", type=float, default=1.0)
    ap.add_argument("--eval_batch_size", type=int, default=2)
    ap.add_argument("--num_workers", type=int, default=4)
    ap.add_argument("--limit", type=int, default=0, help="Evaluate first N examples (0 = all).")
    ap.add_argument("--device", choices=["auto","cuda","cpu"], default="auto")
    # field names (so you can adapt to your JSON structure)
    ap.add_argument("--messages_field", default="messages")
    ap.add_argument("--sender_field", default="from", help='Use "frm" if your JSONL uses that key.')
    ap.add_argument("--text_field", default="text")
    ap.add_argument("--reference_field", default="", help='One of {"summary","target","reference"}; leave empty to auto-detect.')
    ap.add_argument("--max_ctx_chars", type=int, default=8000, help="Trim long threads from the end (recent turns).")
    return ap.parse_args()

args = parse_args()
os.makedirs(args.out_dir, exist_ok=True)
os.environ.setdefault("TOKENIZERS_PARALLELISM", "true")

# --------- IO helpers ---------

def stream_jsonl(path: str):
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except Exception:
                continue

def normalize_ws(s: str) -> str:
    return " ".join((s or "").split())

def build_source_from_thread(obj: Dict[str, Any]) -> str:
    msgs = obj.get(args.messages_field, []) or []
    turns = []
    sender_key = args.sender_field
    text_key = args.text_field
    for m in msgs:
        who = normalize_ws(m.get(sender_key) or m.get("frm") or m.get("sender") or "Unknown")
        txt = normalize_ws(m.get(text_key) or "")
        if txt:
            turns.append(f"[MSG] {who}: {txt}")
    ctx = "\n".join(turns)
    if len(ctx) > args.max_ctx_chars:
        ctx = ctx[-args.max_ctx_chars:]
    return ctx

def extract_reference(obj: Dict[str, Any]) -> str:
    # explicit
    if args.reference_field:
        return obj.get(args.reference_field, "") or ""
    # auto-detect common keys
    for k in ("summary", "target", "reference", "ref"):
        if k in obj and obj[k]:
            return str(obj[k])
    return ""

# --------- Dataset ---------

class ThreadsEvalSet(Dataset):
    def __init__(self, rows: List[Dict[str, Any]], tokenizer, max_in: int):
        self.rows = rows
        self.tok = tokenizer
        self.max_in = max_in
    def __len__(self): return len(self.rows)
    def __getitem__(self, idx):
        obj = self.rows[idx]
        source = build_source_from_thread(obj)
        ref = extract_reference(obj)
        enc = self.tok(source, truncation=True, max_length=self.max_in, padding=False)
        return {"input_ids": enc["input_ids"],
                "attention_mask": enc["attention_mask"],
                "source": source,
                "reference": ref}

def collate_fn_factory(tok, model):
    base = DataCollatorForSeq2Seq(tok, model=model, pad_to_multiple_of=8)
    def collate(batch):
        refs = [b["reference"] for b in batch]
        srcs = [b["source"] for b in batch]
        x = [{"input_ids": b["input_ids"], "attention_mask": b["attention_mask"]} for b in batch]
        out = base(x)
        out["references"] = refs
        out["sources"] = srcs
        return out
    return collate

# --------- Model ---------

def load_model_tokenizer(model_dir: str):
    tok = AutoTokenizer.from_pretrained(model_dir, use_fast=True)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_dir)
    device = args.device
    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    model = model.to(device).eval()
    model.config.use_cache = True
    return tok, model, device

tokenizer, model, DEVICE = load_model_tokenizer(args.model_dir)

# --------- Build dataset ---------

rows = list(stream_jsonl(args.corpus_dir))
if args.limit and args.limit > 0:
    rows = rows[:args.limit]

dataset = ThreadsEvalSet(rows, tokenizer, args.max_input_len)
loader = DataLoader(
    dataset,
    batch_size=args.eval_batch_size,
    shuffle=False,
    num_workers=args.num_workers,
    pin_memory=(DEVICE=="cuda"),
    persistent_workers=True if args.num_workers>0 else False,
    collate_fn=collate_fn_factory(tokenizer, model),
)

# --------- Generation ---------

def run_generate():
    preds, refs, srcs = [], [], []
    gen_kwargs = dict(
        max_new_tokens=args.max_new_tokens,
        num_beams=args.num_beams,
        no_repeat_ngram_size=args.no_repeat_ngram_size,
        length_penalty=args.length_penalty,
        do_sample=False,
    )
    with torch.no_grad():
        for batch in tqdm(loader, desc="Generating"):
            outs = model.generate(
                input_ids=batch["input_ids"].to(model.device),
                attention_mask=batch["attention_mask"].to(model.device),
                **gen_kwargs
            )
            for i in range(outs.size(0)):
                preds.append(tokenizer.decode(outs[i], skip_special_tokens=True))
            refs.extend(batch["references"])
            srcs.extend(batch["sources"])
    return preds, refs, srcs

preds, refs, srcs = run_generate()

# --------- Save preds ---------

pred_path = os.path.join(args.out_dir, "preds_threads.jsonl")
os.makedirs(args.out_dir, exist_ok=True)
with open(pred_path, "w", encoding="utf-8") as f:
    for s, r, p in zip(srcs, refs, preds):
        rec = {"source": s, "prediction": p}
        if r:
            rec["reference"] = r
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")

# --------- ROUGE (if references present) ---------

have_refs = any(bool(r) for r in refs)
metrics_file = os.path.join(args.out_dir, "eval_threads.json")

if have_refs:
    try:
        import evaluate
        rouge = evaluate.load("rouge")
        refs_clean = [r if r else "" for r in refs]
        metrics = rouge.compute(
            predictions=preds,
            references=refs_clean,
            use_stemmer=True,
            rouge_types=["rouge1","rouge2","rougeL","rougeLsum"]
        )
        metrics_pct = {k: round(v*100.0, 2) for k,v in metrics.items()}
        result = {
            "n_eval": len(preds),
            "device": DEVICE,
            "gen_params": {
                "max_input_len": args.max_input_len,
                "max_new_tokens": args.max_new_tokens,
                "num_beams": args.num_beams,
                "no_repeat_ngram_size": args.no_repeat_ngram_size,
                "length_penalty": args.length_penalty
            },
            "rouge": metrics_pct
        }
    except Exception as e:
        result = {"n_eval": len(preds), "device": DEVICE,
                  "error": f"ROUGE computation failed: {e}"}
else:
    result = {"n_eval": len(preds), "device": DEVICE,
              "note": "No reference summaries found; skipped ROUGE."}

with open(metrics_file, "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2)

print("\n== Done ==")
print(json.dumps(result, indent=2))
print(f"Predictions: {pred_path}")
print(f"Metrics:     {metrics_file}")
