import asyncio
from fastapi import FastAPI
from fastapi.responses import JSONResponse,Response
from .logging import setup_logging
from .config import settings
from .model_manager import ModelOrchestrator
from .routers import summarize as summarize_router
from .routers import categorize as categorize_router
from .routers import suggest as suggest_router
from .routers import models_ctrl as models_ctrl_router
import os
from .monitoring import prometheus_response, LOADED_MODELS, SESSIONS
import psutil
import torch


log = setup_logging(settings.log_level)

from .middleware import require_user_header

app = FastAPI(title="Privacy-Preserving Email LLM API", default_response_class=JSONResponse)

app.state.router_mode = os.getenv("ROUTER_MODE", "inproc")  # "per_user" or "inproc"
app.middleware("http")(require_user_header)
# Single orchestrator per process
orch = ModelOrchestrator()
app.state.orchestrator = ModelOrchestrator()

# Include routers (no per-router state)
app.include_router(summarize_router.router)
app.include_router(categorize_router.router)
app.include_router(suggest_router.router)
app.include_router(models_ctrl_router.router)


@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/admin/debug")
def admin_debug():
    orch = app.state.orchestrator
    def handle_info(uid, h):
        return {
            "user_id": uid,
            "model_id": hex(id(h.model)),
            "tokenizer_id": hex(id(h.tokenizer)),
            "adapter_dir": getattr(h, "adapter_dir", None),
        }
    items = []
    for uid, h in orch.cache._store.items():
        items.append(handle_info(uid, h))
    base = getattr(orch, "base_handle", None)
    return {
        "base": handle_info("__base__", base) if base else None,
        "handles": items,
        "versions": getattr(orch, "_user_version", {}),
        "tmpdirs": getattr(orch, "_user_tmpdir", {}),
    }

@app.get("/metrics")
def metrics():
    ctype, data = prometheus_response()
    return Response(content=data, media_type=ctype)

@app.get("/admin/models")
def admin_models():
    orch = app.state.orchestrator
    LOADED_MODELS.set(len(orch.cache._store))
    return {
        "loaded_users": [k for k in orch.cache._store.keys() if k != "__base__"],
        "versions": getattr(orch, "_user_version", {}),
        "tmpdirs": getattr(orch, "_user_tmpdir", {}),
    }

@app.get("/admin/sessions")
def admin_sessions():
    return {"sessions": SESSIONS.list(), "active": SESSIONS.active_count()}

@app.get("/admin/memory")
def admin_memory():
    """
    Display current CPU + GPU memory usage (human-readable in GB).
    Also shows whether GPU is available and in use.
    """
    info = {}

    # ---- CPU (system) memory ----
    process = psutil.Process(os.getpid())
    rss_gb = process.memory_info().rss / (1024 ** 3)
    vms_gb = process.memory_info().vms / (1024 ** 3)

    sysmem = psutil.virtual_memory()
    total_gb = sysmem.total / (1024 ** 3)
    used_gb = sysmem.used / (1024 ** 3)
    free_gb = sysmem.available / (1024 ** 3)

    info["cpu_memory"] = {
        "process_rss_gb": round(rss_gb, 3),
        "process_vms_gb": round(vms_gb, 3),
        "system_total_gb": round(total_gb, 3),
        "system_used_gb": round(used_gb, 3),
        "system_free_gb": round(free_gb, 3),
    }

    # ---- GPU (VRAM) memory ----
    if torch.cuda.is_available():
        device = torch.cuda.current_device()
        name = torch.cuda.get_device_name(device)
        total = torch.cuda.get_device_properties(device).total_memory / (1024 ** 3)
        allocated = torch.cuda.memory_allocated(device) / (1024 ** 3)
        reserved = torch.cuda.memory_reserved(device) / (1024 ** 3)

        info["gpu"] = {
            "device": name,
            "allocated_gb": round(allocated, 3),
            "reserved_gb": round(reserved, 3),
            "total_gb": round(total, 3),
            "percent_used": round((allocated / total) * 100, 2),
        }
        info["using_gpu"] = True
    else:
        info["gpu"] = None
        info["using_gpu"] = False

    # Indicate which device models are using
    device_type = "cuda" if torch.cuda.is_available() else "cpu"
    info["models_device"] = device_type

    return JSONResponse(info)

# Background task to sweep idle models
async def sweeper():
    while True:
        try:
            orch.sweep()
        except Exception as e:
            log.exception("sweep error: %s", e)
        await asyncio.sleep(30)

@app.on_event("startup")
async def on_start():
    asyncio.create_task(sweeper())
