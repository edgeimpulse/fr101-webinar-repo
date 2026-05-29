#!/usr/bin/env bash
set -euo pipefail
MODEL="/home/onlogic/webinar/llm/qwen/qwen2.5-0.5b-instruct-q4_k_m.gguf"

if [ ! -f "$MODEL" ]; then
  echo "Missing Qwen model: $MODEL"
  echo "Run: ./scripts/download_qwen.sh, or SCP the GGUF to this path."
  exit 1
fi

/home/onlogic/llama.cpp/build/bin/llama-server \
  -m "$MODEL" \
  --host 0.0.0.0 \
  --port 9876 \
  -c 2048 \
  -n 180 \
  --no-warmup
