from fastapi import APIRouter, Header, Request
from ..models import ThreadsPayload, SummarizeResult
from ..prompts import summarize_prompt
from ..config import settings

router = APIRouter()

def parse_summary_text(text: str) -> SummarizeResult:
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    summary = lines[0] if lines else text
    key_points, actions, dates = [], [], []
    for l in lines[1:]:
        if l.startswith(("-", "*")): key_points.append(l.lstrip("-* ").strip())
        if "by " in l.lower() or "due" in l.lower(): actions.append(l)
        if any(tok in l for tok in ["202", "Jan", "Feb", "Mar", "Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]):
            dates.append(l)
    return SummarizeResult(summary=summary, key_points=key_points, actions=actions, dates=dates)

@router.post("/summarize")
def summarize(payload: ThreadsPayload, request: Request, x_user_id: str = Header(...,convert_underscores=False)):
    orch = request.app.state.orchestrator
    handle = orch.get(x_user_id)
    results = []
    for t in payload.threads:
        prompt = summarize_prompt(t)
        max_new = settings.generation_max_new_tokens_long if (t.mode == "long") else settings.generation_max_new_tokens_short
        out = handle.generate(prompt, max_new_tokens=max_new)
        results.append(parse_summary_text(out))
    return [r.model_dump() for r in results]
