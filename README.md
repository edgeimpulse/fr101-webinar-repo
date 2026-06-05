# FR101 Industrial Edge AI Webinar Demo


This demo is intended to illustrate the possibilties of SLMs on QC6490 based devices running in combination with accelerated Edge Impulse models. The demo is tested on  onlogic FR101 but can be run on any 6490 based device locally or on [Device Cloud](https://docs.edgeimpulse.com/tutorials/topics/inference/run-qualcomm-device-cloud#run-on-qualcomm-device-cloud)


<img width="1378" height="1145" alt="image" src="https://github.com/user-attachments/assets/2a7494b8-80cf-4182-a9cc-13e0aae333b8" />


After the FOMO-AD model triggers on a threshold the reult can passed to be analysed by the SLM for the operator:

<img width="1378" height="1145" alt="image" src="https://github.com/user-attachments/assets/697e47c4-973e-4ea7-bab7-6d99ccbf1913" />

This cascading can further be enhanced and extened to [VLMs](https://www.edgeimpulse.com/blog/coming-soon-in-edge-ai-model-cascading-with-vlms/)

<img width="2056" height="1145" alt="image" src="https://github.com/user-attachments/assets/b0437eb4-9ae5-484d-8a7a-167eadaacbba" />

Telegram interaction 

<img width="1080" height="2640" alt="image" src="https://github.com/user-attachments/assets/3be4786c-f1aa-464b-a6e0-5f2a2bec0d9f" />
<img width="1080" height="2640" alt="image" src="https://github.com/user-attachments/assets/265b9f46-a7db-4550-bd48-26c55d21747e" />
<img width="1080" height="2640" alt="image" src="https://github.com/user-attachments/assets/7611db78-247e-48de-abcc-746b7a68200f" />


Demo stack for the OnLogic FR101 / Qualcomm QCS6490 webinar.

Flow:

```text
Razer Kiyo camera
  -> Edge Impulse crack / FOMO-AD .eim
  -> repeated anomaly threshold
  -> GPIO / DIO dry-run or output
  -> local Qwen 0.5B / 500M operator note
```

## Recommended live path

Use CPU `.eim` + local Qwen for the stable demo:

```bash
cd /home/onlogic/webinar
./scripts/start_qwen.sh
```

In another terminal:

```bash
cd /home/onlogic/webinar
./scripts/start_fr101_demo_cpu_qwen.sh
```

Open:

```text
http://192.168.1.58:8080
```

## Model files to copy manually

Large `.eim` and `.gguf` files are not included.

```bash
models/fomo_ad_cpu.eim
models/fomo_ad_qnn.eim
llm/qwen/qwen2.5-0.5b-instruct-q4_k_m.gguf
```

## Camera

The Razer Kiyo has appeared as `/dev/video2` on the FR101. Check with:

```bash
v4l2-ctl --list-devices
```

If the node changes, run with:

```bash
CAMERA_DEVICE=/dev/videoX ./scripts/start_fr101_demo_cpu_qwen.sh
```

## Threshold

The Visual GMM project metadata showed `min_anomaly_score: 6.0`. The app defaults to `6.0`, but you can override:

```bash
THRESHOLD=0.8 ./scripts/start_fr101_demo_cpu_qwen.sh
```

## QNN path

After installing QAIRT:

```bash
source ./qairt-env.sh
ldd models/fomo_ad_qnn.eim | grep "not found" || true
./scripts/start_fr101_demo_qnn_qwen.sh
```

If the QNN model initializes but `classify()` returns error `-3`, use CPU as the live fallback and treat QNN as runtime-validation evidence.
