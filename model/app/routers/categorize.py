from fastapi import APIRouter, Header, Request
from ..models import ThreadsPayload, CategorizeResult
from ..prompts import categorize_prompt

router = APIRouter()

def parse_labels(text: str) -> CategorizeResult:
    import json
    try:
        j = json.loads(text)
        labels = j.get("labels", [])
        rationale = j.get("rationale")
        if isinstance(labels, list):
            return CategorizeResult(labels=[str(x) for x in labels], rationale=rationale)
    except Exception:
        pass
    labels = []
    low = text.lower()
    labels.append("spam:yes" if "spam" in low else "spam:no")
    labels.append("priority:high" if any(x in low for x in ["urgent", "asap", "friday"]) else "priority:normal")
    labels.append("topic:general")
    return CategorizeResult(labels=labels, rationale=text[:200])

@router.post("/categorize")
def categorize(payload: ThreadsPayload, request: Request, x_user_id: str = Header(..., convert_underscores=False)):
    orch = request.app.state.orchestrator
    handle = orch.get(x_user_id)
    results = []
    for t in payload.threads:
        prompt = categorize_prompt(t)
        out = handle.generate(prompt, max_new_tokens=64)
        results.append(parse_labels(out))
    return [r.model_dump() for r in results]
