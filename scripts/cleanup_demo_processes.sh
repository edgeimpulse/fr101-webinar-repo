#!/usr/bin/env bash
set -euo pipefail
pkill -f fr101_web_demo_edge_llm.py || true
pkill -f fr101_web_demo_compare.py || true
pkill -f fr101_web_demo_camera_first.py || true
sleep 1
ss -ltnp | grep ':8080' || true
fuser -v /dev/video2 || true
