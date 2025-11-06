import os
from pydantic import BaseModel, field_validator
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.getenv("ENV_FILE", ".env"))

class Settings(BaseModel):
    # --- Object store (for remote adapters fallback) ---
    object_store_impl: str = os.getenv("OBJECT_STORE_IMPL", "local")
    object_store_url: str | None = os.getenv("OBJECT_STORE_URL")
    adapter_bucket: str = os.getenv("ADAPTER_BUCKET", "./adapters")
    lora_layout: str = os.getenv("LORA_LAYOUT", "single_bucket")
    lora_object_key: str = os.getenv("LORA_OBJECT_KEY", "lora.safetensors")

    # --- Local roots (preferred) ---
    full_model_dir: str | None = os.getenv("FULL_MODEL_DIR")       # e.g., /models/full
    adapters_root: str | None = os.getenv("ADAPTERS_ROOT")         # e.g., /adapters

    # --- HF fallback (if full_model_dir not provided) ---
    base_model_path: str | None = os.getenv("BASE_MODEL_PATH") or None
    base_model_id: str = os.getenv("BASE_MODEL_ID", "t5-base")

    # --- Transformers cache/offline ---
    transformers_offline: int = int(os.getenv("TRANSFORMERS_OFFLINE", "0"))
    transformers_cache: str | None = os.getenv("TRANSFORMERS_CACHE")

    # --- Device / precision / quantization ---
    device_map: str = os.getenv("DEVICE_MAP", "auto")              # "auto" | "cpu"
    dtype_str: str = os.getenv("DTYPE", "bfloat16")                # "float16"|"bfloat16"|"float32"
    load_in_8bit: bool = os.getenv("LOAD_IN_8BIT", "false").lower() == "true"
    load_in_4bit: bool = os.getenv("LOAD_IN_4BIT", "false").lower() == "true"
    trust_remote_code: bool = os.getenv("TRUST_REMOTE_CODE", "false").lower() == "true"

    # --- Generation defaults ---
    generation_max_new_tokens_short: int = int(os.getenv("GEN_TOKENS_SHORT", "56"))
    generation_max_new_tokens_long: int = int(os.getenv("GEN_TOKENS_LONG", "128"))
    num_beams: int = int(os.getenv("NUM_BEAMS", "4"))
    no_repeat_ngram: int = int(os.getenv("NO_REPEAT_NGRAM", "3"))
    length_penalty: float = float(os.getenv("LENGTH_PENALTY", "1.0"))
    early_stopping: bool = os.getenv("EARLY_STOPPING", "true").lower() == "true"

    # --- Caching / eviction ---
    max_handles: int = int(os.getenv("MAX_HANDLES", "8"))          # per-user composed models
    idle_secs: int = int(os.getenv("IDLE_SECS", "1200"))
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    @field_validator("device_map")
    @classmethod
    def _dm(cls, v): return v

settings = Settings()
