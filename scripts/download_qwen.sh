#!/usr/bin/env bash
set -euo pipefail

mkdir -p /home/onlogic/webinar/llm/qwen
cd /home/onlogic/webinar/llm/qwen

URL="https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/qwen2.5-0.5b-instruct-q4_k_m.gguf"
OUT="qwen2.5-0.5b-instruct-q4_k_m.gguf"

# Force IPv4 on FR101 networks where IPv6 to Hugging Face times out.
wget -4 --tries=10 --timeout=30 --continue -O "$OUT" "$URL" || \
curl -4 -L --retry 10 --connect-timeout 30 -o "$OUT" "$URL"

ls -lh "$OUT"
