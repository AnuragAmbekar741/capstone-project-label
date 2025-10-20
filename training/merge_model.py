# merge_lora.py
import os, argparse, json
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from peft import PeftModel
import torch

#python merge_model.py --adapter_dir "C:/Users/kunal/Desktop/college/capstone/training/model_tf_base/final_model" --out_dir "C:/Users/kunal/Desktop/college/capstone/training/model_tf_base/full_model" --dtype fp16

def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base_model", default="t5-base", help="HF id or path of the original backbone (e.g., google/flan-t5-large)")
    ap.add_argument("--adapter_dir", required=True, help="Folder with adapter_config.json (your trained LoRA)")--adpater
    ap.add_argument("--out_dir", required=True, help="Destination folder for the merged *full* model")
    ap.add_argument("--dtype", default="auto", choices=["auto","fp32","fp16","bf16"])
    return ap.parse_args()

def pick_dtype(name):
    if name == "auto":
        return torch.float16 if torch.cuda.is_available() else None
    return {"fp32": torch.float32, "fp16": torch.float16, "bf16": torch.bfloat16}[name]

def main():
    args = parse_args()
    os.makedirs(args.out_dir, exist_ok=True)

    dtype = pick_dtype(args.dtype)
    tok = AutoTokenizer.from_pretrained(args.base_model, use_fast=True)
    base = AutoModelForSeq2SeqLM.from_pretrained(args.base_model, torch_dtype=dtype)

    # Load adapters into a *fresh* base model
    peft_model = PeftModel.from_pretrained(base, args.adapter_dir)

    # Merge adapters into base weights (returns a plain HF model)
    merged = peft_model.merge_and_unload()

    # Save as a regular HF model folder
    merged.save_pretrained(args.out_dir, safe_serialization=True)
    tok.save_pretrained(args.out_dir)

    # Write a tiny provenance note
    meta = {
        "merged_from": {
            "base_model": args.base_model,
            "adapter_dir": os.path.abspath(args.adapter_dir)
        }
    }
    with open(os.path.join(args.out_dir, "MERGE_PROVENANCE.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print(f"Saved merged full model to: {args.out_dir}")

if __name__ == "__main__":
    main()
