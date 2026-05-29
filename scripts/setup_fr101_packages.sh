#!/usr/bin/env bash
set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
  echo "Run as root: su root; ./scripts/setup_fr101_packages.sh"
  exit 1
fi

apt update
apt install -y \
  git cmake build-essential pkg-config wget curl unzip \
  python3 python3-pip python3-dev python3-opencv python3-flask python3-numpy \
  v4l-utils gpiod python3-libgpiod \
  portaudio19-dev libportaudio2 libportaudiocpp0 \
  libcurl4-openssl-dev

python3 -m pip install --upgrade pip setuptools wheel || true
python3 -m pip install -r /home/onlogic/webinar/requirements.txt || true
