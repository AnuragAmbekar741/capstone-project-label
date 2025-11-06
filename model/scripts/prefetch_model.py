# scripts/prefetch_model.py
import os, argparse
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model_id", default="t5-base")
    ap.add_argument("--out_dir", default="./models/t5-base")
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    print(f"Downloading {args.model_id} -> {args.out_dir}")
    AutoModelForSeq2SeqLM.from_pretrained(args.model_id).save_pretrained(args.out_dir)
    AutoTokenizer.from_pretrained(args.model_id).save_pretrained(args.out_dir)
    print("Done.")

if __name__ == "__main__":
    main()
