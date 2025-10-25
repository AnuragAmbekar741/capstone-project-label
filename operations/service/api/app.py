# services/api/app.py
from typing import List, Optional, Literal, Dict, Any
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
import httpx, os

MODEL_URL = os.environ.get("MODEL_URL", "http://localhost:8000")

app = FastAPI(title="operations", version="0.0.1")

# ---------- Schemas (same as before) ----------
class EmailPart(BaseModel):
    id: Optional[str] = None
    timestamp: Optional[str] = None
    sender: Optional[str] = None
    recipients: Optional[List[str]] = None
    subject: Optional[str] = None
    body: str

class EmailThread(BaseModel):
    thread_id: Optional[str] = None
    messages: List[EmailPart]

class SummarizeRequest(BaseModel):
    text: Optional[str] = None
    thread: Optional[EmailThread] = None
    max_tokens: int = 128
    style: Literal["tldr", "key_points", "actions"] = "tldr"

class SummaryResponse(BaseModel):
    summary: str
    meta: Dict[str, Any] = {}

class ClassifyRequest(BaseModel):
    text: Optional[str] = None
    thread: Optional[EmailThread] = None

class ClassifyResponse(BaseModel):
    labels: List[str]
    scores: Dict[str, float]

class BatchSummarizeRequest(BaseModel):
    items: List[SummarizeRequest]

class BatchClassifyRequest(BaseModel):
    items: List[ClassifyRequest]

class FormatEmailRequest(BaseModel):
    id: Optional[str] = None
    date: Optional[str] = None
    from_: Optional[str] = Field(None, alias="from")
    to: Optional[List[str]] = None
    cc: Optional[List[str]] = None
    subject: Optional[str] = None
    body_html: Optional[str] = None
    body_text: Optional[str] = None
    in_reply_to: Optional[str] = None
    references: Optional[List[str]] = None
    prior: Optional[List[EmailPart]] = None

class FormatThreadRequest(BaseModel):
    parts: List[FormatEmailRequest]

class FormatResponse(BaseModel):
    thread: EmailThread

# ---------- Helpers ----------
def _strip_quotes(text: str) -> str:
    keep = []
    for line in text.splitlines():
        s = line.strip()
        if s.startswith(">"): continue
        if s.startswith("On ") and ("wrote:" in s or "sent:" in s): break
        keep.append(line)
    out = "\n".join(keep).strip()
    return out or text.strip()

def _to_turns(parts: List[EmailPart]):
    turns = []
    for p in parts:
        turns.append({
            "author": p.sender or "unknown",
            "timestamp": p.timestamp,
            "text": _strip_quotes(p.body),
            "subject": p.subject
        })
    return turns

# ---------- API endpoints ----------
@app.get("/health")
def health(): return {"ok": True}

@app.post("/format/email", response_model=FormatResponse)
def format_email(req: FormatEmailRequest):
    body = req.body_text or req.body_html or ""
    part = EmailPart(
        id=req.id, timestamp=req.date, sender=req.from_,
        recipients=req.to or [], subject=req.subject, body=body
    )
    return {"thread": EmailThread(thread_id=req.id or "local", messages=(req.prior or []) + [part])}

@app.post("/format/thread", response_model=FormatResponse)
def format_thread(req: FormatThreadRequest):
    parts = []
    for r in req.parts:
        body = r.body_text or r.body_html or ""
        parts.append(EmailPart(id=r.id, timestamp=r.date, sender=r.from_,
                               recipients=r.to or [], subject=r.subject, body=body))
    tid = req.parts[0].id if req.parts else "local"
    return {"thread": EmailThread(thread_id=tid, messages=parts)}

async def _post_to_model(path: str, payload: dict, user_id: str):
    headers = {"x_user_id": user_id}
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post(f"{MODEL_URL}{path}", json=payload, headers=headers)
        if r.status_code != 200:
            raise HTTPException(r.status_code, r.text)
        return r.json()

@app.post("/summarize", response_model=SummaryResponse)
async def summarize(req: SummarizeRequest, x_user_id: str = Header(..., convert_underscores=False)):
    payload = req.dict()
    if req.thread: payload["turns"] = _to_turns(req.thread.messages)
    return await _post_to_model("/summarize", payload, x_user_id)

@app.post("/classify", response_model=ClassifyResponse)
async def classify(req: ClassifyRequest, x_user_id: str = Header(..., convert_underscores=False)):
    payload = req.dict()
    if req.thread: payload["turns"] = _to_turns(req.thread.messages)
    return await _post_to_model("/classify", payload, x_user_id)

@app.post("/batch/summarize", response_model=List[SummaryResponse])
async def batch_summarize(req: BatchSummarizeRequest, x_user_id: str = Header(..., convert_underscores=False)):
    items = []
    for item in req.items:
        d = item.dict()
        if item.thread: d["turns"] = _to_turns(item.thread.messages)
        items.append(d)
    return await _post_to_model("/batch/summarize", {"items": items}, x_user_id)

@app.post("/batch/classify", response_model=List[ClassifyResponse])
async def batch_classify(req: BatchClassifyRequest, x_user_id: str = Header(..., convert_underscores=False)):
    items = []
    for item in req.items:
        d = item.dict()
        if item.thread: d["turns"] = _to_turns(item.thread.messages)
        items.append(d)
    return await _post_to_model("/batch/classify", {"items": items}, x_user_id)

# ---- Fine-tune submission (hands off to ftn via model or directly via queue) ----
class FineTuneRequest(BaseModel):
    user_id: str
    task: Literal["summarize", "classify", "both"] = "both"
    examples: List[Dict[str, Any]]  # [{"turns":[...], "summary": "..."} or {"turns":[...], "labels":[...]}]
    lora_rank: int = 8
    steps: int = 200

@app.post("/tuning/submit")
async def submit_ftn(req: FineTuneRequest):
    # Forward to model (which enqueues) or directly to ftn with Redis; keeping it simple:
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{MODEL_URL}/tuning/submit", json=req.dict())
    return r.json()
