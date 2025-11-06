# Privacy-Preserving Email LLM API

FastAPI-based service that serves **summarize**, **categorize**, and **suggest** endpoints over email threads.
It loads a shared base model (**t5-base**) and per-user **LoRA adapters** from object storage on demand.
Adapters are cached in-memory and can be explicitly offloaded to guarantee user isolation.

## Features
- Per-user adapter isolation via LoRA/PEFT
- EmailSum-style thread shaping (`message1 ||| message2 ||| ...`)
- Endpoints:
  - `POST /summarize`
  - `POST /categorize`
  - `POST /suggest`
  - `POST /models/onload`
  - `POST /models/offload`
- Scales locally (Docker Compose) or in Kubernetes without code changes

## Quickstart (local)
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export OBJECT_STORE_IMPL=local
export ADAPTER_BUCKET=./adapters
uvicorn llm_api.main:app --host 0.0.0.0 --port 8080 --reload
