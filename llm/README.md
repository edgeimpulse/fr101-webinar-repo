# Local Qwen / optional VLM models

The demo uses local Qwen 0.5B / 500M as the operator-note model via llama.cpp.

Expected file:

```bash
/home/onlogic/webinar/llm/qwen/qwen2.5-0.5b-instruct-q4_k_m.gguf
```

Download on the FR101:

```bash
./scripts/download_qwen.sh
```

Or download on your laptop and SCP the `.gguf` into `llm/qwen/`.

Optional VLM support is included in the app, but Qwen-only is the recommended live webinar path.
