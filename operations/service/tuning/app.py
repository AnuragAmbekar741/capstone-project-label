# services/ftn/app.py
import os, json, time, shutil, tempfile
from typing import List, Dict, Any
from fastapi import FastAPI
from pydantic import BaseModel

ADAPTERS_ROOT = os.environ.get("ADAPTERS_ROOT", "/adapters")

app = FastAPI(title="User Fine-Tune Service", version="0.1.0")

class FineTuneRequest(BaseModel):
    user_id: str
    task: str  # "summarize" | "classify" | "both"
    examples: List[Dict[str, Any]]
    lora_rank: int = 8
    steps: int = 200

@app.post("/run")
def run_ftn(req: FineTuneRequest):
    # Pseudocode: train PEFT/LoRA on your task head(s) with the small examples.
    # In this skeleton we just produce a dummy adapter file to show plumbing.
    stamp = time.strftime("%Y%m%d-%H%M%S")
    out_dir = os.path.join(ADAPTERS_ROOT, req.user_id, stamp)
    os.makedirs(out_dir, exist_ok=True)
    adapter_path = os.path.join(out_dir, "adapter.safetensors")
    with open(adapter_path, "wb") as f:
        f.write(b"\x00\x01dummy")  # replace with real adapter export

    # Atomically update `current` symlink
    current = os.path.join(ADAPTERS_ROOT, req.user_id, "current")
    if os.path.islink(current) or os.path.exists(current):
        os.remove(current)
    os.symlink(out_dir, current)

    meta = {"user_id": req.user_id, "adapter_dir": out_dir, "n_examples": len(req.examples)}
    with open(os.path.join(out_dir, "meta.json"), "w") as f:
        json.dump(meta, f)

    return {"ok": True, "adapter": adapter_path}
