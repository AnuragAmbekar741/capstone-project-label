from fastapi import APIRouter, Header, Request
from ..models import ThreadsPayload, SuggestResult, Suggestion
from ..prompts import suggest_prompt

router = APIRouter()

def parse_suggestions(text: str) -> SuggestResult:
    lines = [l.strip("-* ").strip() for l in text.splitlines() if l.strip()]
    suggs = []
    for l in lines[:3]:
        if l:
            suggs.append(Suggestion(text=l, tone="neutral"))
    if len(lines) >= 4:
        draft = " ".join(lines[3:])[:600]
        suggs.append(Suggestion(text=draft, tone="formal"))
    if not suggs:
        suggs = [Suggestion(text=text[:200], tone="neutral")]
    return SuggestResult(suggestions=suggs)

@router.post("/suggest")
def suggest(payload: ThreadsPayload, request: Request, x_user_id: str = Header(..., convert_underscores=False)):
    orch = request.app.state.orchestrator
    handle = orch.get(x_user_id)
    results = []
    for t in payload.threads:
        prompt = suggest_prompt(t)
        out = handle.generate(prompt, max_new_tokens=96)
        results.append(parse_suggestions(out))
    return [r.model_dump() for r in results]
