from fastapi import APIRouter, Header, Request
from ..models import OnOffloadRequest
from ..monitoring import SESSIONS

router = APIRouter()

@router.post("/models/onload")
def onload(req: OnOffloadRequest, request: Request, x_user_id: str = Header(..., convert_underscores=False)):
    orch = request.app.state.orchestrator
    h = orch.get(req.x_user_id)
    source = "base" if (h.adapter_dir is None) else "adapter"
    # Enrich session
    ver = getattr(orch, "_user_version", {}).get(req.x_user_id)
    SESSIONS.touch(req.x_user_id, adapter_version=ver, loaded=(source == "adapter"))
    return {"status": "ok", "loaded_for": req.x_user_id, "source": source, "adapter_dir": h.adapter_dir}

@router.post("/models/offload")
def offload(req: OnOffloadRequest, request: Request, x_user_id: str = Header(..., convert_underscores=False)):
    orch = request.app.state.orchestrator
    orch.offload(req.x_user_id)
    # mark in sessions
    SESSIONS.mark_offloaded(req.x_user_id)
    return {"status": "ok", "offloaded_for": req.x_user_id}

@router.post("/models/refresh")
def refresh(req: OnOffloadRequest, request: Request, x_user_id: str = Header(..., convert_underscores=False)):
    """
    Forces a version check and reload from object storage for this user.
    """
    orch = request.app.state.orchestrator
    orch.offload(req.x_user_id)       # drop current
    orch.get(req.x_user_id)           # re-download with latest version
    return {"status": "ok", "reloaded_for": req.x_user_id}
