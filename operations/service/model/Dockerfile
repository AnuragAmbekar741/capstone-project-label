FROM nvidia/cuda:12.8.1-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y python3 python3-pip && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY app.py /app/

# Use torch matching your GPU; wheels pull at build time
RUN pip3 install torch --index-url https://download.pytorch.org/whl/nightly/cu128
RUN pip3 install fastapi uvicorn[standard] transformers peft accelerate

# Optional: enable 8-bit/4-bit loading if desired
RUN pip3 install --no-cache-dir bitsandbytes

ENV FULL_MODEL_DIR=/models/full \
    ADAPTERS_ROOT=/adapters \
    DEVICE_MAP=auto \
    DTYPE=bfloat16 \
    LOAD_IN_8BIT=false \
    LOAD_IN_4BIT=false \
    NUM_BEAMS=4 \
    NO_REPEAT_NGRAM=3 \
    LENGTH_PENALTY=1.0 \
    EARLY_STOPPING=true \
    MAX_NEW_TOKENS=128 \
    MAX_COMPOSED_CACHE=3
EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
