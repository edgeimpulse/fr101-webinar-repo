#!/usr/bin/env bash
set -euo pipefail
curl http://127.0.0.1:9876/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "system", "content": "You are an industrial maintenance assistant. The word crack means a physical crack in concrete, metal, plastic, or a machine component. Do not discuss cybersecurity or software vulnerabilities."},
      {"role": "user", "content": "A local Edge Impulse visual anomaly model detected a possible physical surface crack. Score: 0.87. Threshold: 0.80. The alert was confirmed across 3 consecutive frames. Write a short operator note with likely meaning, immediate check, escalation recommendation, and evidence to log."}
    ],
    "temperature": 0.2,
    "max_tokens": 140
  }'
