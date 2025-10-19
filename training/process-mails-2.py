# #!/usr/bin/env python3
# # -*- coding: utf-8 -*-
# """
# Build a clean email corpus from the Kaggle Enron CSV (2 columns: location, raw_email).

# Outputs:
#   - out/messages.jsonl   : one message per line (normalized headers + scrubbed body)
#   - out/threads.jsonl    : one thread per line (EmailSum-style: subject_norm + ordered messages)
#   - out/stats.json       : corpus & threading summary
#   - out/splits/          : (NEW) train/test (and optional val) JSONL pairs for training
#         ├─ train.jsonl
#         ├─ test.jsonl
#         ├─ val.jsonl        (only if --val_frac > 0)
#         └─ split_stats.json

# Usage examples:
#   python process-mails.py --csv data/raw/emails.csv --out_dir data/corpus --min_body_chars 40 --make_splits
#   python process-mails.py --csv data/raw/emails.csv --out_dir data/corpus --make_splits --train_frac 0.86 --test_frac 0.14 --val_frac 0.0
# """

# import csv
# import os
# import re
# import json
# import hashlib
# import argparse
# import sys
# from collections import defaultdict, Counter
# from datetime import datetime
# from typing import List, Dict, Any
# import random

# import email
# from email.utils import parsedate_to_datetime

# # allow very large CSV cells (raw emails)
# _max = sys.maxsize
# while True:
#     try:
#         csv.field_size_limit(_max)
#         break
#     except OverflowError:
#         _max = int(_max / 10)

# # ---------------------------
# # Utilities
# # ---------------------------
# EMAIL_RE  = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
# PHONE_RE  = re.compile(r"(?:(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4})")
# SIG_RE    = re.compile(r"(?is)(--\s*\n.*?$)|(^Sent from my .*?$)")
# QUOTE_RE  = re.compile(r"(?is)^>.*$", re.MULTILINE)
# HTML_TAGS = re.compile(r"(?is)<(script|style).*?>.*?</\1>|<[^>]+>")
# WS_MULTI  = re.compile(r"\s+")

# def html_to_text(s: str) -> str:
#     s = HTML_TAGS.sub(" ", s or "")
#     return WS_MULTI.sub(" ", s).strip()

# def scrub_text(text: str, drop_quoted_threshold: float = 0.6) -> str:
#     t = text or ""
#     t = EMAIL_RE.sub("<EMAIL>", t)
#     t = PHONE_RE.sub("<PHONE>", t)
#     t = SIG_RE.sub("", t)
#     quoted = len(QUOTE_RE.findall(t))
#     if quoted / max(1, len(t.splitlines())) > drop_quoted_threshold:
#         t = "\n".join([ln for ln in t.splitlines() if not ln.strip().startswith(">")])
#     return WS_MULTI.sub(" ", t).strip()

# def safe_parse_date(dt: str) -> str:
#     if not dt:
#         return ""
#     try:
#         return parsedate_to_datetime(dt).isoformat()
#     except Exception:
#         for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d-%b-%Y %H:%M:%S"):
#             try:
#                 return datetime.strptime(dt, fmt).isoformat()
#             except Exception:
#                 pass
#     return ""

# def unescape_newlines(s: str) -> str:
#     if s and "\\n" in s and "\n" not in s:
#         s = s.replace("\\r\\n", "\n").replace("\\n", "\n").replace("\\t", "\t")
#     return s or ""

# def norm_subject(subj: str) -> str:
#     s = (subj or "").lower()
#     s = re.sub(r"^(re|fwd|fw)\s*:\s*", "", s)
#     return WS_MULTI.sub(" ", s).strip()

# def body_hash(text: str) -> str:
#     return hashlib.sha256((text or "").encode("utf-8")).hexdigest()

# def normalize_ws(s: str) -> str:
#     return WS_MULTI.sub(" ", (s or "").strip())

# # ---------------------------
# # CSV → raw email parse
# # ---------------------------
# def iter_kaggle_two_col_csv(csv_path: str, body_col: int = 1):
#     with open(csv_path, "r", encoding="utf-8", newline="") as f:
#         reader = csv.reader(f)
#         _ = next(reader, None)  # header maybe present
#         for row in reader:
#             if len(row) <= body_col:
#                 continue
#             yield unescape_newlines(row[body_col])

# def parse_rfc822(raw: str) -> Dict[str, Any]:
#     msg = email.message_from_string(raw)
#     mid  = msg.get("Message-ID", "")
#     subj = (msg.get("Subject") or "").strip()
#     date = safe_parse_date(msg.get("Date", ""))
#     frm  = msg.get("From", "")
#     to   = msg.get("To", "")
#     cc   = msg.get("Cc", "")
#     bcc  = msg.get("Bcc", "")
#     irt  = msg.get("In-Reply-To", "")
#     refs = msg.get("References", "")

#     body_txt = ""
#     if msg.is_multipart():
#         for part in msg.walk():
#             ctype = (part.get_content_type() or "").lower()
#             if ctype == "text/plain":
#                 payload = part.get_payload(decode=True)
#                 if payload:
#                     body_txt += payload.decode(errors="ignore")
#         if not body_txt:
#             for part in msg.walk():
#                 payload = part.get_payload(decode=True)
#                 if isinstance(payload, bytes) and payload:
#                     body_txt = payload.decode(errors="ignore")
#                     break
#     else:
#         payload = msg.get_payload(decode=True)
#         if isinstance(payload, bytes):
#             body_txt = payload.decode(errors="ignore")
#         elif isinstance(payload, str):
#             body_txt = payload

#     if "<html" in (body_txt or "").lower() or "</p>" in (body_txt or "").lower():
#         body_txt = html_to_text(body_txt)

#     body_txt = scrub_text(body_txt)

#     return {
#         "message_id": mid or "",
#         "subject": subj,
#         "subject_norm": norm_subject(subj),
#         "date_iso": date,
#         "from": frm,
#         "to": to,
#         "cc": cc,
#         "bcc": bcc,
#         "in_reply_to": irt,
#         "references": refs,
#         "body_text": body_txt
#     }

# # ---------------------------
# # Threading
# # ---------------------------
# def build_threads(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
#     buckets = defaultdict(list)
#     for m in messages:
#         buckets[m["subject_norm"]].append(m)

#     threads = []
#     for subj_norm, msgs in buckets.items():
#         msgs.sort(key=lambda x: x.get("date_iso", "") or "")
#         participants = sorted({x.get("from","").strip() for x in msgs if x.get("from")})
#         threads.append({
#             "thread_id": f"thr::{subj_norm}" if subj_norm else f"thr::(no_subject):::{hashlib.md5((msgs[0].get('message_id','') + (msgs[0].get('date_iso',''))).encode()).hexdigest()[:10]}",
#             "subject_norm": subj_norm,
#             "n_messages": len(msgs),
#             "participants": participants,
#             "start_ts": msgs[0].get("date_iso",""),
#             "end_ts": msgs[-1].get("date_iso",""),
#             "messages": [
#                 {
#                     "id": m.get("message_id",""),
#                     "from": m.get("from",""),
#                     "to": m.get("to",""),
#                     "date": m.get("date_iso",""),
#                     "in_reply_to": m.get("in_reply_to",""),
#                     "references": m.get("references",""),
#                     "text": m.get("body_text","")
#                 } for m in msgs
#             ]
#         })
#     return [t for t in threads if t["n_messages"] >= 1]

# # ---------------------------
# # Pair building (EmailSum-style)
# # ---------------------------
# def mk_context(messages: List[Dict[str,Any]], max_msgs: int, max_chars: int) -> str:
#     tail = messages[-max_msgs:]
#     chunks = []
#     for m in tail:
#         who = m.get("from","") or "Unknown"
#         txt = normalize_ws(m.get("text","") or "")
#         if not txt: continue
#         # drop quoted lines for compact context
#         lines = [ln for ln in txt.splitlines() if not ln.strip().startswith(">")]
#         txt = normalize_ws("\n".join(lines))
#         if txt:
#             chunks.append(f"[MSG] {who}: {txt}")
#     ctx = "\n".join(chunks)
#     if len(ctx) > max_chars:
#         ctx = ctx[-max_chars:]
#     return ctx.strip()

# def key_sentences(text: str, k: int = 2) -> List[str]:
#     sents = re.split(r"(?<=[.!?])\s+", text or "")
#     sents = [s.strip() for s in sents if s.strip()]
#     sents.sort(key=len, reverse=True)
#     return sents[:k]

# def weak_summary(thread: Dict[str,Any]) -> str:
#     subject = thread.get("subject_norm","") or ""
#     last_txt = (thread["messages"][-1].get("text","") or "").strip()
#     ks = key_sentences(last_txt, k=2)
#     out = " ".join(([subject] if subject else []) + ks)
#     out = out.strip() or " ".join(last_txt.split()[:30])
#     return normalize_ws(out)[:512]

# def build_and_write_splits(threads: List[Dict[str,Any]],
#                            out_dir: str,
#                            train_frac: float,
#                            test_frac: float,
#                            val_frac: float,
#                            max_msgs: int,
#                            max_ctx_chars: int,
#                            seed: int):
#     assert abs(train_frac + test_frac + val_frac - 1.0) < 1e-6, "fractions must sum to 1.0"
#     splits_dir = os.path.join(out_dir, "splits")
#     os.makedirs(splits_dir, exist_ok=True)

#     rng = random.Random(seed)
#     f_train = open(os.path.join(splits_dir, "train.jsonl"), "w", encoding="utf-8")
#     f_test  = open(os.path.join(splits_dir, "test.jsonl"),  "w", encoding="utf-8")
#     f_val   = open(os.path.join(splits_dir, "val.jsonl"),   "w", encoding="utf-8") if val_frac > 0 else None

#     n_total = n_train = n_test = n_val = 0
#     for thr in threads:
#         msgs = thr.get("messages", [])
#         if not msgs: continue
#         ctx = mk_context(msgs, max_msgs=max_msgs, max_chars=max_ctx_chars)
#         if len(ctx) < 40:  # skip ultra-short
#             continue
#         tgt = weak_summary(thr)
#         if not tgt:
#             continue

#         r = rng.random()
#         dest = f_train
#         if r > train_frac:
#             if r <= train_frac + val_frac and f_val:
#                 dest = f_val; n_val += 1
#             else:
#                 dest = f_test; n_test += 1
#         else:
#             n_train += 1

#         rec = {
#             "thread_id": thr.get("thread_id",""),
#             "input_text": ctx,
#             "target_text": tgt
#         }
#         dest.write(json.dumps(rec, ensure_ascii=False) + "\n")
#         n_total += 1

#     f_train.close(); f_test.close()
#     if f_val: f_val.close()

#     stats = {
#         "pairs_total": n_total,
#         "train": n_train,
#         "test": n_test,
#         "val": n_val if val_frac > 0 else 0,
#         "config": {
#             "train_frac": train_frac, "test_frac": test_frac, "val_frac": val_frac,
#             "max_ctx_msgs": max_msgs, "max_ctx_chars": max_ctx_chars, "seed": seed
#         }
#     }
#     with open(os.path.join(splits_dir, "split_stats.json"), "w", encoding="utf-8") as f:
#         json.dump(stats, f, indent=2, ensure_ascii=False)

# # ---------------------------
# # Pipeline
# # ---------------------------
# def build_corpus(csv_path: str,
#                  out_dir: str,
#                  min_body_chars: int = 20,
#                  drop_empty_subjects: bool = False,
#                  make_splits: bool = False,
#                  train_frac: float = 0.86,
#                  test_frac: float = 0.14,
#                  val_frac: float = 0.0,
#                  max_ctx_msgs: int = 6,
#                  max_ctx_chars: int = 2000,
#                  seed: int = 42):
#     os.makedirs(out_dir, exist_ok=True)
#     msg_out = open(os.path.join(out_dir, "messages.jsonl"), "w", encoding="utf-8")
#     dedup = set()
#     messages = []

#     total_rows = 0
#     kept = 0
#     for raw in iter_kaggle_two_col_csv(csv_path, body_col=1):
#         total_rows += 1
#         if not raw or len(raw) < 10:
#             continue
#         try:
#             rec = parse_rfc822(raw)
#             if not rec["subject"]:
#                 rec["subject"] = " ".join((rec["body_text"] or "").split()[:10])
#                 rec["subject_norm"] = norm_subject(rec["subject"])

#             if len(rec["body_text"]) < min_body_chars:
#                 continue
#             if drop_empty_subjects and not rec["subject_norm"]:
#                 continue

#             key = rec["message_id"].strip() or body_hash(rec["body_text"])
#             if key in dedup:
#                 continue
#             dedup.add(key)

#             messages.append(rec)
#             msg_out.write(json.dumps(rec, ensure_ascii=False) + "\n")
#             kept += 1
#         except Exception:
#             continue
#     msg_out.close()

#     threads = build_threads(messages)
#     with open(os.path.join(out_dir, "threads.jsonl"), "w", encoding="utf-8") as f:
#         for t in threads:
#             f.write(json.dumps(t, ensure_ascii=False) + "\n")

#     by_sender = Counter([m.get("from","") for m in messages if m.get("from")])
#     by_subject_empty = sum(1 for m in messages if not m.get("subject_norm"))
#     stats = {
#         "rows_in": total_rows,
#         "messages_kept": kept,
#         "unique_threads": len(threads),
#         "avg_msgs_per_thread": round(sum(t["n_messages"] for t in threads)/max(1,len(threads)), 2),
#         "empty_subject_msgs": by_subject_empty,
#         "top_senders": by_sender.most_common(10),
#     }
#     with open(os.path.join(out_dir, "stats.json"), "w", encoding="utf-8") as f:
#         json.dump(stats, f, ensure_ascii=False, indent=2)

#     print(json.dumps(stats, indent=2, ensure_ascii=False))

#     # NEW: build train/test(/val) after threads are created
#     if make_splits:
#         # Normalize fractions (in case user gives only train & test)
#         total_frac = train_frac + test_frac + val_frac
#         if abs(total_frac - 1.0) > 1e-6:
#             # scale to sum to 1
#             train_frac = train_frac/total_frac
#             test_frac  = test_frac/total_frac
#             val_frac   = val_frac/total_frac

#         build_and_write_splits(
#             threads=threads,
#             out_dir=out_dir,
#             train_frac=train_frac,
#             test_frac=test_frac,
#             val_frac=val_frac,
#             max_msgs=max_ctx_msgs,
#             max_ctx_chars=max_ctx_chars,
#             seed=seed
#         )

# # ---------------------------
# # CLI
# # ---------------------------
# def parse_args():
#     ap = argparse.ArgumentParser()
#     ap.add_argument("--csv", required=True, help="Path to Kaggle CSV (two columns: location, raw_email)")
#     ap.add_argument("--out_dir", required=True, help="Output directory for corpus JSONL files")
#     ap.add_argument("--min_body_chars", type=int, default=20, help="Drop messages with too-short bodies")
#     ap.add_argument("--drop_empty_subjects", action="store_true", help="Drop messages with empty normalized subject")

#     # NEW: split/pairs options
#     ap.add_argument("--make_splits", action="store_true", help="Also write train/test (and optional val) pairs in out_dir/splits")
#     ap.add_argument("--train_frac", type=float, default=0.86, help="Train fraction (default 0.86)")
#     ap.add_argument("--test_frac",  type=float, default=0.14, help="Test fraction (default 0.14)")
#     ap.add_argument("--val_frac",   type=float, default=0.0,  help="Validation fraction (default 0.0)")
#     ap.add_argument("--max_ctx_msgs", type=int, default=6, help="Max messages from thread tail for context")
#     ap.add_argument("--max_ctx_chars", type=int, default=2000, help="Max characters for the context string")
#     ap.add_argument("--seed", type=int, default=42, help="Random seed for splits")
#     return ap.parse_args()

# if __name__ == "__main__":
#     args = parse_args()
#     build_corpus(
#         csv_path=args.csv,
#         out_dir=args.out_dir,
#         min_body_chars=args.min_body_chars,
#         drop_empty_subjects=args.drop_empty_subjects,
#         make_splits=args.make_splits,
#         train_frac=args.train_frac,
#         test_frac=args.test_frac,
#         val_frac=args.val_frac,
#         max_ctx_msgs=args.max_ctx_msgs,
#         max_ctx_chars=args.max_ctx_chars,
#         seed=args.seed
#     )


#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build a clean email corpus from the Kaggle Enron CSV (2 columns: location, raw_email).

Outputs (root):
  - out/messages.jsonl
  - out/threads.jsonl
  - out/stats.json

NEW (thread-level splits that keep the same schemas as root):
  - out/splits/train/messages.jsonl
  - out/splits/train/threads.jsonl
  - out/splits/train/stats.json
  - out/splits/test/messages.jsonl
  - out/splits/test/threads.jsonl
  - out/splits/test/stats.json
  - (optional) out/splits/val/...

Usage:
  python process-mails.py --csv data/raw/emails.csv --out_dir data/corpus --min_body_chars 40 --make_splits
  # Fractions can be adjusted; they are normalized to sum to 1.0 if needed.
"""

import csv
import os
import re
import json
import hashlib
import argparse
import sys
import random
from collections import defaultdict, Counter
from datetime import datetime
from typing import List, Dict, Any

import email
from email.utils import parsedate_to_datetime

# Increase CSV field size limit for very large cells
_max = sys.maxsize
while True:
    try:
        csv.field_size_limit(_max)
        break
    except OverflowError:
        _max = int(_max / 10)

# ---------------------------
# Utilities
# ---------------------------
EMAIL_RE  = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE  = re.compile(r"(?:(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4})")
SIG_RE    = re.compile(r"(?is)(--\s*\n.*?$)|(^Sent from my .*?$)")
QUOTE_RE  = re.compile(r"(?is)^>.*$", re.MULTILINE)
HTML_TAGS = re.compile(r"(?is)<(script|style).*?>.*?</\1>|<[^>]+>")
WS_MULTI  = re.compile(r"\s+")

def html_to_text(s: str) -> str:
    s = HTML_TAGS.sub(" ", s or "")
    return WS_MULTI.sub(" ", s).strip()

def scrub_text(text: str, drop_quoted_threshold: float = 0.6) -> str:
    t = text or ""
    t = EMAIL_RE.sub("<EMAIL>", t)
    t = PHONE_RE.sub("<PHONE>", t)
    t = SIG_RE.sub("", t)
    quoted = len(QUOTE_RE.findall(t))
    if quoted / max(1, len(t.splitlines())) > drop_quoted_threshold:
        t = "\n".join([ln for ln in t.splitlines() if not ln.strip().startswith(">")])
    return WS_MULTI.sub(" ", t).strip()

def safe_parse_date(dt: str) -> str:
    if not dt:
        return ""
    try:
        return parsedate_to_datetime(dt).isoformat()
    except Exception:
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d-%b-%Y %H:%M:%S"):
            try:
                return datetime.strptime(dt, fmt).isoformat()
            except Exception:
                pass
    return ""

def unescape_newlines(s: str) -> str:
    if s and "\\n" in s and "\n" not in s:
        s = s.replace("\\r\\n", "\n").replace("\\n", "\n").replace("\\t", "\t")
    return s or ""

def norm_subject(subj: str) -> str:
    s = (subj or "").lower()
    s = re.sub(r"^(re|fwd|fw)\s*:\s*", "", s)
    return WS_MULTI.sub(" ", s).strip()

def body_hash(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()

def normalize_ws(s: str) -> str:
    return WS_MULTI.sub(" ", (s or "").strip())

# ---------------------------
# CSV → raw email parse
# ---------------------------
def iter_kaggle_two_col_csv(csv_path: str, body_col: int = 1):
    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        _ = next(reader, None)  # header (maybe)
        for row in reader:
            if len(row) <= body_col:
                continue
            yield unescape_newlines(row[body_col])

def parse_rfc822(raw: str) -> Dict[str, Any]:
    msg = email.message_from_string(raw)
    mid  = msg.get("Message-ID", "")
    subj = (msg.get("Subject") or "").strip()
    date = safe_parse_date(msg.get("Date", ""))
    frm  = msg.get("From", "")
    to   = msg.get("To", "")
    cc   = msg.get("Cc", "")
    bcc  = msg.get("Bcc", "")
    irt  = msg.get("In-Reply-To", "")
    refs = msg.get("References", "")

    body_txt = ""
    if msg.is_multipart():
        for part in msg.walk():
            ctype = (part.get_content_type() or "").lower()
            if ctype == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    body_txt += payload.decode(errors="ignore")
        if not body_txt:
            for part in msg.walk():
                payload = part.get_payload(decode=True)
                if isinstance(payload, bytes) and payload:
                    body_txt = payload.decode(errors="ignore")
                    break
    else:
        payload = msg.get_payload(decode=True)
        if isinstance(payload, bytes):
            body_txt = payload.decode(errors="ignore")
        elif isinstance(payload, str):
            body_txt = payload

    if "<html" in (body_txt or "").lower() or "</p>" in (body_txt or "").lower():
        body_txt = html_to_text(body_txt)

    body_txt = scrub_text(body_txt)

    return {
        "message_id": mid or "",
        "subject": subj,
        "subject_norm": norm_subject(subj),
        "date_iso": date,
        "from": frm,
        "to": to,
        "cc": cc,
        "bcc": bcc,
        "in_reply_to": irt,
        "references": refs,
        "body_text": body_txt
    }

# ---------------------------
# Threading
# ---------------------------
def build_threads(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    buckets = defaultdict(list)
    for m in messages:
        buckets[m["subject_norm"]].append(m)

    threads = []
    for subj_norm, msgs in buckets.items():
        msgs.sort(key=lambda x: x.get("date_iso", "") or "")
        participants = sorted({x.get("from","").strip() for x in msgs if x.get("from")})
        threads.append({
            "thread_id": f"thr::{subj_norm}" if subj_norm else f"thr::(no_subject):::{hashlib.md5((msgs[0].get('message_id','') + (msgs[0].get('date_iso',''))).encode()).hexdigest()[:10]}",
            "subject_norm": subj_norm,
            "n_messages": len(msgs),
            "participants": participants,
            "start_ts": msgs[0].get("date_iso",""),
            "end_ts": msgs[-1].get("date_iso",""),
            "messages": [
                {
                    "id": m.get("message_id",""),
                    "from": m.get("from",""),
                    "to": m.get("to",""),
                    "date": m.get("date_iso",""),
                    "in_reply_to": m.get("in_reply_to",""),
                    "references": m.get("references",""),
                    "text": m.get("body_text","")
                } for m in msgs
            ]
        })
    return [t for t in threads if t["n_messages"] >= 1]

# ---------------------------
# Split helpers (thread-level; preserve schemas)
# ---------------------------
def split_threads(threads: List[Dict[str,Any]],
                  train_frac: float,
                  test_frac: float,
                  val_frac: float,
                  seed: int = 42):
    # normalize fractions to sum to 1.0
    total = train_frac + test_frac + val_frac
    if total <= 0:
        raise ValueError("At least one split fraction must be > 0.")
    train_frac, test_frac, val_frac = (train_frac/total, test_frac/total, val_frac/total)

    rng = random.Random(seed)
    shuffled = threads[:]
    rng.shuffle(shuffled)

    n = len(shuffled)
    n_train = int(round(n * train_frac))
    n_val   = int(round(n * val_frac))
    n_test  = n - n_train - n_val

    train = shuffled[:n_train]
    val   = shuffled[n_train:n_train+n_val]
    test  = shuffled[n_train+n_val:]

    # sizes adjust if rounding issues
    return train, val, test

def write_split(out_dir_split: str,
                threads_split: List[Dict[str,Any]],
                messages_all: List[Dict[str,Any]]):
    """
    Write threads.jsonl and messages.jsonl for a split,
    preserving the original schemas.
    """
    os.makedirs(out_dir_split, exist_ok=True)

    # threads.jsonl (verbatim thread objects)
    thr_path = os.path.join(out_dir_split, "threads.jsonl")
    with open(thr_path, "w", encoding="utf-8") as f:
        for t in threads_split:
            f.write(json.dumps(t, ensure_ascii=False) + "\n")

    # Collect message_ids present in this split
    msg_ids = set()
    for t in threads_split:
        for m in t.get("messages", []):
            mid = (m.get("id","") or "").strip()
            if mid:
                msg_ids.add(mid)

    # Filter original messages.jsonl objects by message_id
    msg_path = os.path.join(out_dir_split, "messages.jsonl")
    kept = 0
    with open(msg_path, "w", encoding="utf-8") as f:
        for m in messages_all:
            mid = (m.get("message_id","") or "").strip()
            if mid and mid in msg_ids:
                f.write(json.dumps(m, ensure_ascii=False) + "\n")
                kept += 1

    # stats.json for the split
    stats = {
        "threads": len(threads_split),
        "messages": kept
    }
    with open(os.path.join(out_dir_split, "stats.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)

# ---------------------------
# Pipeline
# ---------------------------
def build_corpus(csv_path: str,
                 out_dir: str,
                 min_body_chars: int = 20,
                 drop_empty_subjects: bool = False,
                 make_splits: bool = False,
                 train_frac: float = 0.86,
                 test_frac: float = 0.14,
                 val_frac: float = 0.0,
                 seed: int = 42):
    os.makedirs(out_dir, exist_ok=True)
    msg_out = open(os.path.join(out_dir, "messages.jsonl"), "w", encoding="utf-8")
    dedup = set()
    messages = []

    total_rows = 0
    kept = 0
    for raw in iter_kaggle_two_col_csv(csv_path, body_col=1):
        total_rows += 1
        if not raw or len(raw) < 10:
            continue
        try:
            rec = parse_rfc822(raw)
            if not rec["subject"]:
                rec["subject"] = " ".join((rec["body_text"] or "").split()[:10])
                rec["subject_norm"] = norm_subject(rec["subject"])

            if len(rec["body_text"]) < min_body_chars:
                continue
            if drop_empty_subjects and not rec["subject_norm"]:
                continue

            key = rec["message_id"].strip() or body_hash(rec["body_text"])
            if key in dedup:
                continue
            dedup.add(key)

            messages.append(rec)
            msg_out.write(json.dumps(rec, ensure_ascii=False) + "\n")
            kept += 1
        except Exception:
            continue
    msg_out.close()

    threads = build_threads(messages)
    with open(os.path.join(out_dir, "threads.jsonl"), "w", encoding="utf-8") as f:
        for t in threads:
            f.write(json.dumps(t, ensure_ascii=False) + "\n")

    by_sender = Counter([m.get("from","") for m in messages if m.get("from")])
    by_subject_empty = sum(1 for m in messages if not m.get("subject_norm"))
    stats = {
        "rows_in": total_rows,
        "messages_kept": kept,
        "unique_threads": len(threads),
        "avg_msgs_per_thread": round(sum(t["n_messages"] for t in threads)/max(1,len(threads)), 2),
        "empty_subject_msgs": by_subject_empty,
        "top_senders": by_sender.most_common(10),
    }
    with open(os.path.join(out_dir, "stats.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    print(json.dumps(stats, indent=2, ensure_ascii=False))

    # --- NEW: make thread-level splits that keep base schemas ---
    if make_splits:
        train_split, val_split, test_split = split_threads(
            threads=threads,
            train_frac=train_frac,
            test_frac=test_frac,
            val_frac=val_frac,
            seed=seed
        )
        splits_root = os.path.join(out_dir, "splits")
        # train
        write_split(os.path.join(splits_root, "train"), train_split, messages)
        # test
        write_split(os.path.join(splits_root, "test"), test_split, messages)
        # val (optional)
        if val_split:
            write_split(os.path.join(splits_root, "val"), val_split, messages)

# ---------------------------
# CLI
# ---------------------------
def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True, help="Path to Kaggle CSV (two columns: location, raw_email)")
    ap.add_argument("--out_dir", required=True, help="Output directory for corpus JSONL files")
    ap.add_argument("--min_body_chars", type=int, default=20, help="Drop messages with too-short bodies")
    ap.add_argument("--drop_empty_subjects", action="store_true", help="Drop messages with empty normalized subject")

    # Thread-level split options
    ap.add_argument("--make_splits", action="store_true", help="Write train/test(/val) folders with messages.jsonl & threads.jsonl")
    ap.add_argument("--train_frac", type=float, default=0.86)
    ap.add_argument("--test_frac",  type=float, default=0.14)
    ap.add_argument("--val_frac",   type=float, default=0.0)
    ap.add_argument("--seed", type=int, default=42)
    return ap.parse_args()

if __name__ == "__main__":
    args = parse_args()
    build_corpus(
        csv_path=args.csv,
        out_dir=args.out_dir,
        min_body_chars=args.min_body_chars,
        drop_empty_subjects=args.drop_empty_subjects,
        make_splits=args.make_splits,
        train_frac=args.train_frac,
        test_frac=args.test_frac,
        val_frac=args.val_frac,
        seed=args.seed
    )
