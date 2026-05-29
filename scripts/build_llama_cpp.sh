#!/usr/bin/env bash
set -euo pipefail

cd /home/onlogic
if [ ! -d llama.cpp ]; then
  git clone https://github.com/ggerganov/llama.cpp.git
fi
cd llama.cpp
cmake -B build -DLLAMA_CURL=ON
cmake --build build -j"${JOBS:-2}"
/home/onlogic/llama.cpp/build/bin/llama-server --help | head
