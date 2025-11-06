import time
from collections import OrderedDict
from threading import Lock
from typing import Any, Optional

class LRUCache:
    """
    A simple thread-safe LRU cache that also evicts items idle for `idle_seconds`.

    Stored values are expected to have:
      - .last_used (float seconds since epoch)
      - .unload() method (optional) for cleanup
    """
    def __init__(self, max_items: int = 8, idle_seconds: int = 1200):
        self._store: "OrderedDict[str, Any]" = OrderedDict()
        self.max_items = max_items
        self.idle_seconds = idle_seconds
        self._lock = Lock()

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key not in self._store:
                return None
            value = self._store.pop(key)
            self._store[key] = value  # move to end (most recently used)
            return value

    def put(self, key: str, value: Any) -> None:
        with self._lock:
            if key in self._store:
                self._store.pop(key)
            self._store[key] = value
            self._evict_if_needed_locked()

    def evict(self, key: str) -> None:
        with self._lock:
            if key in self._store:
                handle = self._store.pop(key)
                self._safe_unload(handle)

    def sweep_idle(self) -> None:
        """Evict any entries idle longer than idle_seconds."""
        now = time.time()
        to_remove = []
        with self._lock:
            for k, handle in list(self._store.items()):
                last_used = getattr(handle, "last_used", None)
                if last_used is None:
                    continue
                if now - last_used > self.idle_seconds:
                    to_remove.append(k)
            for k in to_remove:
                h = self._store.pop(k)
                self._safe_unload(h)

    # ---- internal helpers ----
    def _evict_if_needed_locked(self) -> None:
        while len(self._store) > self.max_items:
            _, handle = self._store.popitem(last=False)  # pop LRU
            self._safe_unload(handle)

    @staticmethod
    def _safe_unload(handle: Any) -> None:
        try:
            if hasattr(handle, "unload"):
                handle.unload()
        except Exception:
            # best-effort cleanup; avoid crashing sweeper
            pass
