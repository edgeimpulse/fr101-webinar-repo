# Webinar Runbook

## 1. Cleanup

```bash
cd /home/onlogic/webinar
./scripts/cleanup_demo_processes.sh
```

## 2. Start Qwen

```bash
cd /home/onlogic/webinar
./scripts/start_qwen.sh
```

Test:

```bash
./scripts/test_qwen_prompt.sh
```

## 3. Test camera

```bash
v4l2-ctl --list-devices
python3 scripts/test_kiyo_camera.py --device /dev/video2 --output kiyo_test.jpg
```

## 4. Start stable CPU demo

```bash
./scripts/start_fr101_demo_cpu_qwen.sh
```

Open browser:

```text
http://192.168.1.58:8080
```

## 5. Talk track

- The Edge Impulse model is the always-on inspection layer.
- The repeated threshold prevents one-frame false triggers.
- GPIO/DIO dry-run proves the physical action path.
- Qwen 0.5B runs locally as a triggered operator-note model.
- QNN is the accelerator path, but runtime validation is part of rightsizing.

## 6. Troubleshooting

| Symptom | Fix |
|---|---|
| Port 8080 in use | `pkill -f fr101_web_demo` |
| Camera cannot open | `v4l2-ctl --list-devices`; update `CAMERA_DEVICE` |
| model_missing | Copy `.eim` into `models/` and `chmod +x` |
| Qwen gives cybersecurity answer | Use the grounded system prompt in this repo |
| QNN not found libraries | `source qairt-env.sh`; check `ldd` |
| QNN classify -3 | Use CPU live path; re-export QNN model and validate separately |
