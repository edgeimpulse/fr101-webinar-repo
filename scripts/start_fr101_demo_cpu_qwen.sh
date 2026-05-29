#!/usr/bin/env bash
set -euo pipefail
cd /home/onlogic/webinar
MODEL="models/fomo_ad_cpu.eim"

if [ ! -f "$MODEL" ]; then
  echo "Missing CPU model: $MODEL"
  echo "Copy Linux AARCH64 non-QNN .eim to /home/onlogic/webinar/models/fomo_ad_cpu.eim"
  exit 1
fi
chmod +x "$MODEL"

python3 app/fr101_web_demo_edge_llm.py \
  --model "$MODEL" \
  --model-mode CPU \
  --camera-device "${CAMERA_DEVICE:-/dev/video2}" \
  --width 640 --height 480 --fps 15 \
  --threshold "${THRESHOLD:-6.0}" \
  --bad-frames 3 \
  --gpio-chip gpiochip5 --gpio-line 0 \
  --dry-run \
  --qwen-url http://127.0.0.1:9876/v1/chat/completions \
  --host 0.0.0.0 --port 8080
