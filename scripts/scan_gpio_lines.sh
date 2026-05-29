#!/usr/bin/env bash
set -euo pipefail
CHIP="${1:-gpiochip5}"
SECONDS="${2:-1}"
echo "Scanning ${CHIP} lines 0-7"
for LINE in 0 1 2 3 4 5 6 7; do
  echo "${CHIP} line ${LINE}: ON"
  gpioset "${CHIP}" "${LINE}=1"
  sleep "${SECONDS}"
  echo "${CHIP} line ${LINE}: OFF"
  gpioset "${CHIP}" "${LINE}=0"
  sleep "${SECONDS}"
done
