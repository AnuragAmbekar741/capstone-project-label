import time
from llm_api.utils.lru import LRUCache

class Dummy:
    def __init__(self): self.unloaded = False; self.last_used = time.time()
    def unload(self): self.unloaded = True

def test_lru_put_get_evict():
    c = LRUCache(max_items=2, idle_seconds=9999)
    a, b, d = Dummy(), Dummy(), Dummy()
    c.put("a", a); c.put("b", b)
    assert c.get("a") is a
    c.put("d", d)  # evicts LRU ("b")
    assert c.get("b") is None
    assert b.unloaded is True

def test_lru_idle_sweep():
    c = LRUCache(max_items=10, idle_seconds=0)  # immediate idle
    a = Dummy()
    a.last_used -= 10
    c.put("a", a)
    c.sweep_idle()
    assert c.get("a") is None
