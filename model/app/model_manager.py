import os, time, threading, json, shutil, glob, tempfile
from typing import Optional, Dict, Any
import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, AutoConfig
from peft import PeftModel
from .config import settings
from .storage import StorageClient
from .utils.lru import LRUCache
from .monitoring import SESSIONS, GEN_TOKENS, LOADED_MODELS
import gc


# ------------------------
# Helpers
# ------------------------
def _dtype_from_str(s: str):
    return {"float16": torch.float16, "bfloat16": torch.bfloat16, "float32": torch.float32}.get(s, torch.bfloat16)

def _has_any_safetensors(path: str) -> bool:
    return bool(glob.glob(os.path.join(path, "*.safetensors")))

def _user_local_adapter_dir(user_id: str) -> Optional[str]:
    """
    Look for /adapters/<user>/current containing adapter files.
    """
    if not settings.adapters_root:
        return None
    cand = os.path.join(settings.adapters_root, user_id, "current")
    return cand if os.path.isdir(cand) and _has_any_safetensors(cand) else None

# Make PEFT tolerant to “*_config” variants from your training
VALID_LORA_KEYS = {
    "r",
    "lora_alpha",
    "lora_dropout",
    "target_modules",
    "bias",
    "task_type",
    "inference_mode",
    "modules_to_save",
    "init_lora_weights",
    "fan_in_fan_out",
    "use_rslora",
    "alpha_pattern",
    "base_model_name_or_path",
    "peft_type",
}

def _find_adapter_config(adapter_dir: str) -> Optional[str]:
    for name in ("adapter_config.json", "config.json"):
        p = os.path.join(adapter_dir, name)
        if os.path.isfile(p):
            return p
    return None

def _first_lora_like_dict(d: dict) -> Optional[dict]:
    # check common blocks
    for k in ("lora_config", "corda_config", "eva_config"):
        v = d.get(k)
        if isinstance(v, dict) and any(x in v for x in ("r","lora_alpha","lora_dropout","target_modules")):
            return v
    # check any *_config
    for k, v in d.items():
        if isinstance(v, dict) and k.endswith("_config"):
            if any(x in v for x in ("r","lora_alpha","lora_dropout","target_modules")):
                return v
    return None

def _sanitize_peft_config(adapter_dir: str) -> None:
    """
    Create a PEFT-clean adapter_config.json containing ONLY keys accepted by LoraConfig.
    Unknown keys like 'corda_config'/'eva_config' are removed.
    """
    cfg_path = _find_adapter_config(adapter_dir)
    if not cfg_path:
        return

    try:
        with open(cfg_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except Exception:
        return

    # Start with a clean dict
    clean = {}

    # keep explicit meta if present
    if isinstance(raw, dict):
        if isinstance(raw.get("base_model_name_or_path"), str):
            clean["base_model_name_or_path"] = raw["base_model_name_or_path"]

    # ensure peft_type / task_type
    clean["peft_type"] = "LORA"
    clean.setdefault("task_type", "SEQ_2_SEQ_LM")
    clean.setdefault("inference_mode", True)

    # find a nested LoRA-like block and lift valid keys
    nested = _first_lora_like_dict(raw) or raw  # also allow top-level if it already has valid keys
    if isinstance(nested, dict):
        for k, v in nested.items():
            if k in VALID_LORA_KEYS:
                clean[k] = v

    # if some valid keys were directly on top-level raw, keep them
    for k, v in raw.items():
        if k in VALID_LORA_KEYS:
            clean[k] = v

    # minimal defaults if missing
    clean.setdefault("r", 8)
    clean.setdefault("lora_alpha", 8)
    clean.setdefault("lora_dropout", 0.0)

    # write back the sanitized config
    with open(cfg_path, "w", encoding="utf-8") as f:
        json.dump(clean, f, indent=2)

def _compose_base_load_kwargs(config):
    kw: Dict[str, Any] = dict(config=config, trust_remote_code=settings.trust_remote_code)
    if settings.load_in_8bit:
        kw.update(load_in_8bit=True, device_map=settings.device_map)
    elif settings.load_in_4bit:
        kw.update(load_in_4bit=True, device_map=settings.device_map)
    else:
        kw.update(device_map=settings.device_map, torch_dtype=_dtype_from_str(settings.dtype_str))
    return kw

# ------------------------
# Model handles
# ------------------------
class ModelHandle:
    def __init__(self, model, tokenizer, user_id: str, adapter_dir: Optional[str] = None):
        self.user_id = user_id
        self.model = model
        self.tokenizer = tokenizer
        self.adapter_dir = adapter_dir   # for cleanup if temp
        self.last_used = time.time()
        self.lock = threading.Lock()

    def unload(self):
        # Drop reference to the composed model; allow GC
        self.model = None
        # Remove tmp adapter dir if we downloaded it
        if self.adapter_dir and os.path.isdir(self.adapter_dir) and self.adapter_dir.startswith("/tmp/"):
            try: shutil.rmtree(self.adapter_dir)
            except Exception: pass
        self.adapter_dir = None
        self.last_used = time.time()

    def generate(self, text: str, max_new_tokens: int) -> str:
        from .config import settings as S
        self.last_used = time.time()
        with torch.inference_mode():
            with self.lock:
                inputs = self.tokenizer(text, return_tensors="pt", truncation=True).to(self.model.device)
                gen = self.model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,
                    num_beams=S.num_beams,
                    no_repeat_ngram_size=S.no_repeat_ngram,
                    length_penalty=S.length_penalty,
                    early_stopping=S.early_stopping,
                    pad_token_id=self.tokenizer.pad_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                )
                decoded = self.tokenizer.decode(gen[0], skip_special_tokens=True).strip()
                try:
                    tokens = gen.shape[-1]  # generated length
                except Exception:
                    tokens = 0
                GEN_TOKENS.labels(user_id=self.user_id, route="generate").inc(tokens)
                return decoded

# ------------------------
# Orchestrator
# ------------------------
class ModelOrchestrator:
    """
    - Loads a merged base model from FULL_MODEL_DIR if provided; else falls back to HF (BASE_MODEL_*).
    - Composes per-user models by applying LoRA adapters from:
        1) local ADAPTERS_ROOT/<user>/current, or
        2) remote object store (downloaded to /tmp/<user>_adapter_xxx) as fallback.
    - Caches composed user models with LRU + idle eviction.
    """
    
    def __init__(self):
        # Transformers envs
        if settings.transformers_cache:
            os.environ["TRANSFORMERS_CACHE"] = settings.transformers_cache
        if settings.transformers_offline:
            os.environ["TRANSFORMERS_OFFLINE"] = str(settings.transformers_offline)

        # Prefer merged full model dir (like your app.py)
        if settings.full_model_dir and os.path.isdir(settings.full_model_dir):
            cfg = AutoConfig.from_pretrained(settings.full_model_dir, trust_remote_code=settings.trust_remote_code)
            self.tokenizer = AutoTokenizer.from_pretrained(settings.full_model_dir, use_fast=True, trust_remote_code=settings.trust_remote_code)
            load_kwargs = _compose_base_load_kwargs(cfg)
            base = AutoModelForSeq2SeqLM.from_pretrained(settings.full_model_dir, **load_kwargs)
        else:
            # Fallback to HF path or ID
            src = settings.base_model_path if (settings.base_model_path and os.path.isdir(settings.base_model_path)) else settings.base_model_id
            cfg = AutoConfig.from_pretrained(src, trust_remote_code=settings.trust_remote_code, local_files_only=os.path.isdir(src) if isinstance(src,str) else False)
            self.tokenizer = AutoTokenizer.from_pretrained(src, use_fast=True, trust_remote_code=settings.trust_remote_code, local_files_only=os.path.isdir(src) if isinstance(src,str) else False)
            load_kwargs = _compose_base_load_kwargs(cfg)
            base = AutoModelForSeq2SeqLM.from_pretrained(src, **load_kwargs)

        base.eval()
        self.base_config = cfg
        self.base_model_dir = settings.full_model_dir
        self.base = base
        self.cache = LRUCache(settings.max_handles, settings.idle_secs)
        self.storage = StorageClient()
        self._user_version: dict[str, str] = {}   # user_id -> remote_version
        self._user_tmpdir: dict[str, str] = {}    # user_id -> downloaded tmp dir (if any)

        # Keep base as a special handle
        self.base_handle = ModelHandle(self.base, self.tokenizer, "__base__", adapter_dir=None)
        self.cache.put("__base__", self.base_handle)

        # Track adapter source path per user to detect changes
        self._loaded_user_path: Dict[str, str] = {}

    def _compose_user_model(self, adapter_dir: str):
        load_kwargs = _compose_base_load_kwargs(self.base_config)
        base_src = self.base_model_dir or settings.base_model_path or settings.base_model_id
        base = AutoModelForSeq2SeqLM.from_pretrained(base_src, **load_kwargs)
        base.eval()
        _sanitize_peft_config(adapter_dir)
        user_model = PeftModel.from_pretrained(base, adapter_dir, is_trainable=False)
        user_model.eval()
        return user_model
    
    def _download_if_stale(self, user_id: str) -> tuple[str, bool]:
        """
        Check remote version; download when changed. Returns (adapter_dir, changed?)
        """
        ver = self.storage.remote_version(user_id)
        changed = (self._user_version.get(user_id) != ver)
        if not changed:
            # already have latest → use previous dir if exists (local adapters_root users return local path upstream)
            d = self._user_tmpdir.get(user_id)
            return (d if d else "", False)
        # new version → download fresh dir
        d = self.storage.download_adapter_folder(user_id, ver)
        # cleanup old tmp if present
        old = self._user_tmpdir.get(user_id)
        if old and old.startswith("/tmp/") and os.path.isdir(old):
            try: shutil.rmtree(old)
            except Exception: pass
        self._user_version[user_id] = ver
        self._user_tmpdir[user_id] = d
        return d, True

    def _ensure_user_model(self, user_id: str) -> ModelHandle:
        # Always source from object storage (as you requested)
        adapter_dir, changed = self._download_if_stale(user_id)

        existing = self.cache.get(user_id)
        if existing and not changed:
            return existing

        try:
            model = self._compose_user_model(adapter_dir)
            handle = ModelHandle(model, self.tokenizer, user_id, adapter_dir=adapter_dir)
            SESSIONS.touch(user_id, adapter_version=self._user_version.get(user_id), loaded=True)
            LOADED_MODELS.set(len(self.cache._store))
        except Exception as e:
            print(f"[WARN] Failed to attach LoRA adapter for {user_id}: {e}")
            handle = ModelHandle(self.base, self.tokenizer, user_id, adapter_dir=adapter_dir)
            SESSIONS.touch(user_id, adapter_version=self._user_version.get(user_id), loaded=False)

        self.cache.put(user_id, handle)
        return handle

    # Public API
    def get(self, user_id: str) -> ModelHandle:
        h = self.cache.get(user_id)
        if h:
            return h
        return self._ensure_user_model(user_id)

    def offload(self, user_id: str):
        # Remove handle from cache (this calls handle.unload(), which deletes tmp dir)
        self.cache.evict(user_id)

        # Drop our bookkeeping references
        d = self._user_tmpdir.pop(user_id, None)
        self._user_version.pop(user_id, None)

        # Force Python GC
        gc.collect()

        # If using CUDA, free cached blocks
        try:
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            pass

        log.info("[offload] user=%s offloaded; tmp=%s", user_id, d)

    def sweep(self):
        self.cache.sweep_idle()
