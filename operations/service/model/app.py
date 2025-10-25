import os, json, glob, collections
from typing import List, Dict, Any, Optional, Literal
from fastapi import FastAPI, Header
from pydantic import BaseModel

import torch
from transformers import AutoConfig, AutoTokenizer, AutoModelForSeq2SeqLM
from peft import PeftModel

# =========================
# Environment / Paths
# =========================
# Point this to your TRAINED, MERGED model directory (the "final_model" you saved).
FULL_MODEL_DIR   = os.environ.get("FULL_MODEL_DIR", "/models/full")

# Optional per-user adapters directory:
#   /adapters/<user_id>/current/{adapter_config.json, adapter_model.safetensors}
ADAPTERS_ROOT    = os.environ.get("ADAPTERS_ROOT", "/adapters")

# Device / precision
DEVICE_MAP       = os.environ.get("DEVICE_MAP", "auto")     # "auto" or "cpu"
DTYPE_STR        = os.environ.get("DTYPE", "bfloat16")      # "float16"|"bfloat16"|"float32"
LOAD_IN_8BIT     = os.getenv("LOAD_IN_8BIT", "false").lower() == "true"
LOAD_IN_4BIT     = os.getenv("LOAD_IN_4BIT", "false").lower() == "true"

TRUST_REMOTE_CODE = os.getenv("TRUST_REMOTE_CODE", "false").lower() == "true"

# ===== Generation defaults (aligned with your train/eval) =====
# Your test used beam search + no_repeat_ngram_size=3 and length similar to "long" preset (≈128).
MAX_NEW_TOKENS   = int(os.getenv("MAX_NEW_TOKENS", "128"))
NUM_BEAMS        = int(os.getenv("NUM_BEAMS", "4"))
NO_REPEAT_NGRAM  = int(os.getenv("NO_REPEAT_NGRAM", "3"))
LENGTH_PENALTY   = float(os.getenv("LENGTH_PENALTY", "1.0"))
EARLY_STOPPING   = os.getenv("EARLY_STOPPING", "true").lower() == "true"

# Cache at most N user-composed models in RAM (LRU)
MAX_COMPOSED_CACHE = int(os.getenv("MAX_COMPOSED_CACHE", "3"))

# =========================
# App
# =========================
app = FastAPI(title="Model Runtime (Seq2Seq merged + optional user LoRA)", version="1.2.0")

# =========================
# Base model load (merged, seq2seq)
# =========================
config = AutoConfig.from_pretrained(FULL_MODEL_DIR, trust_remote_code=TRUST_REMOTE_CODE)
tokenizer = AutoTokenizer.from_pretrained(FULL_MODEL_DIR, use_fast=True, trust_remote_code=TRUST_REMOTE_CODE)

dtype = getattr(torch, DTYPE_STR) if (not LOAD_IN_8BIT and not LOAD_IN_4BIT) else None
load_kwargs: Dict[str, Any] = dict(config=config, trust_remote_code=TRUST_REMOTE_CODE)

if LOAD_IN_8BIT:
    load_kwargs.update(dict(load_in_8bit=True, device_map=DEVICE_MAP))
elif LOAD_IN_4BIT:
    load_kwargs.update(dict(load_in_4bit=True, device_map=DEVICE_MAP))
else:
    load_kwargs.update(dict(device_map=DEVICE_MAP, torch_dtype=dtype))

_base_model = AutoModelForSeq2SeqLM.from_pretrained(FULL_MODEL_DIR, **load_kwargs)
_base_model.eval()

# =========================
# Per-user adapter composition (PEFT, seq2seq)
# =========================
_model_cache: Dict[str, AutoModelForSeq2SeqLM] = {"__base__": _base_model}
_loaded_user_path: Dict[str, str] = {}
_lru = collections.OrderedDict()

def _touch_lru(key: str):
    if key in _lru:
        _lru.move_to_end(key)
    else:
        _lru[key] = True
    # enforce capacity excluding "__base__"
    while len([k for k in _lru if k != "__base__"]) > MAX_COMPOSED_CACHE:
        for k in list(_lru.keys()):
            if k == "__base__":  # never evict base
                continue
            _lru.pop(k, None)
            _model_cache.pop(k, None)
            _loaded_user_path.pop(k, None)
            break

def _user_adapter_dir(user_id: str) -> Optional[str]:
    cand = os.path.join(ADAPTERS_ROOT, user_id, "current")
    return cand if glob.glob(os.path.join(cand, "*.safetensors")) else None

def _build_with_user_adapter(adapter_dir: str) -> AutoModelForSeq2SeqLM:
    # Recreate the same base settings then apply LoRA on top (seq2seq).
    if LOAD_IN_8BIT:
        base = AutoModelForSeq2SeqLM.from_pretrained(
            FULL_MODEL_DIR, load_in_8bit=True, device_map=DEVICE_MAP, trust_remote_code=TRUST_REMOTE_CODE, config=config
        )
    elif LOAD_IN_4BIT:
        base = AutoModelForSeq2SeqLM.from_pretrained(
            FULL_MODEL_DIR, load_in_4bit=True, device_map=DEVICE_MAP, trust_remote_code=TRUST_REMOTE_CODE, config=config
        )
    else:
        base = AutoModelForSeq2SeqLM.from_pretrained(
            FULL_MODEL_DIR, device_map=DEVICE_MAP, torch_dtype=dtype, trust_remote_code=TRUST_REMOTE_CODE, config=config
        )
    base.eval()
    user_model = PeftModel.from_pretrained(base, adapter_dir)
    user_model.eval()
    return user_model

def _get_model_for_user(user_id: str) -> AutoModelForSeq2SeqLM:
    udir = _user_adapter_dir(user_id)
    if not udir:
        _touch_lru("__base__")
        return _model_cache["__base__"]

    path_changed = (_loaded_user_path.get(user_id) != udir)
    if (user_id in _model_cache) and (not path_changed):
        _touch_lru(user_id)
        return _model_cache[user_id]

    user_model = _build_with_user_adapter(udir)
    _model_cache[user_id] = user_model
    _loaded_user_path[user_id] = udir
    _touch_lru(user_id)
    return user_model

# =========================
# Helpers
# =========================
def _join_turns(turns: List[Dict[str, Any]]) -> str:
    lines = []
    for t in (turns or []):
        author = t.get("author", "unknown")
        subject = t.get("subject")
        timestamp = t.get("timestamp", "")
        text = t.get("text", "")
        subj_part = f" [{subject}]" if subject else ""
        lines.append(f"{author}{subj_part} @ {timestamp}: {text}")
    return "\n".join(lines)

@torch.inference_mode()
def _generate_summary(model, prompt: str, max_new_tokens: int) -> str:
    # Deterministic, beam search—matches your eval/test style.
    inputs = tokenizer(prompt, return_tensors="pt", truncation=True).to(model.device)
    gen = model.generate(
        **inputs,
        max_new_tokens=max_new_tokens,
        num_beams=NUM_BEAMS,
        no_repeat_ngram_size=NO_REPEAT_NGRAM,
        length_penalty=LENGTH_PENALTY,
        early_stopping=EARLY_STOPPING,
        pad_token_id=tokenizer.pad_token_id,
        eos_token_id=tokenizer.eos_token_id,
    )
    return tokenizer.decode(gen[0], skip_special_tokens=True)

@torch.inference_mode()
def _generate_json(model, prompt: str, max_new_tokens: int = 128) -> str:
    inputs = tokenizer(prompt, return_tensors="pt", truncation=True).to(model.device)
    gen = model.generate(
        **inputs,
        max_new_tokens=max_new_tokens,
        num_beams=NUM_BEAMS,
        no_repeat_ngram_size=NO_REPEAT_NGRAM,
        length_penalty=LENGTH_PENALTY,
        early_stopping=EARLY_STOPPING,
        pad_token_id=tokenizer.pad_token_id,
        eos_token_id=tokenizer.eos_token_id,
    )
    return tokenizer.decode(gen[0], skip_special_tokens=True)

# =========================
# Schemas
# =========================
class SummarizePayload(BaseModel):
    text: Optional[str] = None
    turns: Optional[List[Dict[str, Any]]] = None
    max_tokens: int = MAX_NEW_TOKENS
    style: Literal["tldr","key_points","actions"] = "tldr"

class ClassifyPayload(BaseModel):
    text: Optional[str] = None
    turns: Optional[List[Dict[str, Any]]] = None

class BatchSummarizePayload(BaseModel):
    items: List[SummarizePayload]

class BatchClassifyPayload(BaseModel):
    items: List[ClassifyPayload]

# =========================
# Endpoints
# =========================
@app.get("/health")
def health():
    return {
        "ok": True,
        "merged_model_dir": FULL_MODEL_DIR,
        "adapters_root": ADAPTERS_ROOT,
        "device_map": DEVICE_MAP,
        "dtype": DTYPE_STR,
        "int8": LOAD_IN_8BIT,
        "int4": LOAD_IN_4BIT,
        "num_beams": NUM_BEAMS,
        "no_repeat_ngram": NO_REPEAT_NGRAM,
        "length_penalty": LENGTH_PENALTY,
        "early_stopping": EARLY_STOPPING,
        "cache_keys": list(_model_cache.keys()),
        "cache_limit": MAX_COMPOSED_CACHE,
    }

@app.post("/summarize")
def summarize(p: SummarizePayload, x_user_id: str = Header(..., convert_underscores=False)):
    model = _get_model_for_user(x_user_id)
    text = p.text or _join_turns(p.turns or [])
    style_instr = {
        "tldr": "Write a concise TL;DR.",
        "key_points": "List the key points as short bullets.",
        "actions": "List action items with owners and dates if present."
    }[p.style]

    prompt = (
        "Summarize the following email/thread. Focus on decisions, dates, and next steps.\n\n"
        f"Style: {p.style} — {style_instr}\n\n"
        f"{text}\n\nSummary:"
    )
    return {
        "summary": _generate_summary(model, prompt, max_new_tokens=p.max_tokens),
        "meta": {"mode": "thread" if p.turns else "single"}
    }

@app.post("/classify")
def classify(p: ClassifyPayload, x_user_id: str = Header(..., convert_underscores=False)):
    model = _get_model_for_user(x_user_id)
    text = p.text or _join_turns(p.turns or [])
    prompt = (
        "Read the email/thread and output JSON with labels and scores.\n"
        "Labels must include: one priority label (priority:high or priority:normal) and one or more category labels from "
        "{category:finance, category:meetings, category:recruiting, category:support, category:sales, category:general}.\n\n"
        "Return strict JSON only. Example: {\"labels\":[\"priority:normal\",\"category:meetings\"],\"scores\":{\"priority:normal\":0.7,\"category:meetings\":0.8}}\n\n"
        f"Email/Thread:\n{text}\n\nJSON:"
    )
    raw = _generate_json(model, prompt, max_new_tokens=128)
    try:
        data = json.loads(raw)
    except Exception:
        data = {
            "labels": ["category:general", "priority:normal"],
            "scores": {"category:general": 0.55, "priority:normal": 0.6},
            "raw": raw
        }
    return data

@app.post("/batch/summarize")
def batch_summarize(p: BatchSummarizePayload, x_user_id: str = Header(..., convert_underscores=False)):
    return [summarize(item, x_user_id) for item in p.items]

@app.post("/batch/classify")
def batch_classify(p: BatchClassifyPayload, x_user_id: str = Header(..., convert_underscores=False)):
    return [classify(item, x_user_id) for item in p.items]

@app.post("/admin/evict")
def admin_evict(user_id: Optional[str] = None):
    if not user_id:
        for k in list(_model_cache.keys()):
            if k != "__base__":
                _model_cache.pop(k, None)
                _lru.pop(k, None)
                _loaded_user_path.pop(k, None)
        return {"ok": True, "cleared": "all"}
    if user_id in _model_cache:
        _model_cache.pop(user_id, None)
        _lru.pop(user_id, None)
        _loaded_user_path.pop(user_id, None)
        return {"ok": True, "cleared": user_id}
    return {"ok": True, "cleared": "none"}
