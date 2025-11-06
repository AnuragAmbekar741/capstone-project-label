from fastapi import Request
from fastapi.responses import JSONResponse

import time
from fastapi import Request
from starlette.responses import Response
from .monitoring import REQ_COUNT, REQ_LATENCY, SESSIONS

async def require_user_header(request: Request, call_next):
    if request.url.path in ("/summarize", "/categorize", "/suggest", "/models/onload", "/models/offload"):
        if "x_user_id" not in request.headers:
            return JSONResponse({"detail": "Missing header x_user_id"}, status_code=422)
    return await call_next(request)

async def metrics_middleware(request: Request, call_next):
    route_path = request.url.path
    method = request.method
    start = time.perf_counter()

    # Track users seen on any routed call (not health/metrics)
    uid = request.headers.get("x_user_id") or request.headers.get("x-user-id")
    if uid:
        # adapter_version & loaded will be filled in by route handlers once known
        SESSIONS.touch(uid)

    try:
        resp: Response = await call_next(request)
        status = str(resp.status_code)
    except Exception:
        status = "500"
        REQ_COUNT.labels(route=route_path, method=method, status=status).inc()
        raise
    else:
        REQ_COUNT.labels(route=route_path, method=method, status=status).inc()
        REQ_LATENCY.labels(route=route_path, method=method).observe(time.perf_counter() - start)
        return resp