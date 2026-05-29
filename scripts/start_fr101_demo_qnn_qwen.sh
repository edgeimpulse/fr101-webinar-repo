#!/usr/bin/env bash
set -euo pipefail
cd /home/onlogic/webinar
MODEL="models/fomo_ad_qnn.eim"

if [ ! -f "$MODEL" ]; then
  echo "Missing QNN model: $MODEL"
  echo "Copy Linux AARCH64 QNN .eim to /home/onlogic/webinar/models/fomo_ad_qnn.eim"
  exit 1
fi
if [ ! -f ./qairt-env.sh ]; then
  echo "Missing qairt-env.sh. Run scripts/fetch_qnn_libs_fr101_disk.sh first."
  exit 1
fi
source ./qairt-env.sh

if ldd "$MODEL" | grep "not found"; then
  echo "Missing QNN dependencies. Check qairt-env.sh and qairt-runtime."
  exit 1
fi
chmod +x "$MODEL"

python3 app/fr101_web_demo_edge_llm.py \
  --model "$MODEL" \
  --model-mode QNN \
  --camera-device "${CAMERA_DEVICE:-/dev/video2}" \
  --width 640 --height 480 --fps 15 \
  --threshold "${THRESHOLD:-6.0}" \
  --bad-frames 3 \
  --gpio-chip gpiochip5 --gpio-line 0 \
  --dry-run \
  --qwen-url http://127.0.0.1:9876/v1/chat/completions \
  --host 0.0.0.0 --port 8080
