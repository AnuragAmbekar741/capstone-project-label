import time
import threading
from typing import Dict, Optional
from dataclasses import dataclass, asdict

from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, CONTENT_TYPE_LATEST, generate_latest

# -------- Metrics --------
REGISTRY = CollectorRegistry()

REQ_COUNT = Counter(
    "email_llm_requests_total",
    "Total HTTP requests",
    ["route", "method", "status"],
    registry=REGISTRY,
)

REQ_LATENCY = Histogram(
    "email_llm_request_seconds",
    "HTTP request latency in seconds",
    ["route", "method"],
    registry=REGISTRY,
)

GEN_TOKENS = Counter(
    "email_llm_generated_tokens_total",
    "Total tokens generated",
    ["user_id", "route"],
    registry=REGISTRY,
)

ACTIVE_USERS = Gauge(
    "email_llm_active_users",
    "Number of active users (sessions loaded)",
    registry=REGISTRY,
)

LOADED_MODELS = Gauge(
    "email_llm_loaded_models",
    "Number of currently loaded user models",
    registry=REGISTRY,
)

# -------- Session registry --------
@dataclass
class UserSession:
    user_id: str
    first_seen: float
    last_seen: float
    adapter_version: Optional[str] = None
    loaded: bool = False  # True if adapter/model attached in cache

class UserSessionRegistry:
    """
    Tracks logged-in users (via any request that includes x_user_id).
    Not a security/session system; just an in-process view for ops.
    """
    def __init__(self):
        self._lock = threading.Lock()
        self._sessions: Dict[str, UserSession] = {}

    def touch(self, user_id: str, adapter_version: Optional[str] = None, loaded: Optional[bool] = None):
        now = time.time()
        with self._lock:
            s = self._sessions.get(user_id)
            if s is None:
                s = UserSession(user_id=user_id, first_seen=now, last_seen=now)
                self._sessions[user_id] = s
            else:
                s.last_seen = now
            if adapter_version is not None:
                s.adapter_version = adapter_version
            if loaded is not None:
                s.loaded = loaded
        self._update_gauges()

    def mark_offloaded(self, user_id: str):
        with self._lock:
            s = self._sessions.get(user_id)
            if s:
                s.loaded = False
        self._update_gauges()

    def list(self):
        with self._lock:
            return [asdict(v) for v in self._sessions.values()]

    def active_count(self) -> int:
        with self._lock:
            return sum(1 for v in self._sessions.values() if v.loaded)

    def _update_gauges(self):
        ACTIVE_USERS.set(len(self._sessions))

# Singleton-ish instances
SESSIONS = UserSessionRegistry()

# -------- Helpers for FastAPI integration --------
def prometheus_response():
    from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
    from .monitoring import REGISTRY
    return CONTENT_TYPE_LATEST, generate_latest(REGISTRY)

