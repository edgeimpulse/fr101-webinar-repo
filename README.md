# FR101 Industrial Edge AI Webinar Demo


This demo is intended to illustrate the possibilties of SLMs on QC6490 based devices running in combination with accelerated Edge Impulse models, specifically here we are showcasing the initial [FOMO-AD GMM based](https://docs.edgeimpulse.com/studio/projects/learning-blocks/blocks/visual-anomaly-detection-fomo-ad) Public project available [here](https://studio.edgeimpulse.com/studio/745013). The demo is tested on  onlogic FR101 but can be run on any 6490 based device locally or on [Device Cloud](https://docs.edgeimpulse.com/tutorials/topics/inference/run-qualcomm-device-cloud#run-on-qualcomm-device-cloud)


The point of the demo is not only that a model can run on edge hardware. It shows how a practical factory-floor system separates the work:
the vision model runs continuously for low-latency inspection
the SLM and VLM run only when triggered
the agentic layer calls bounded tools for status, thresholds, snapshots, notes, VLM summaries and light control
the operator stays in the loop through web UI, Telegram, CLI or MCP/OpenCode
The 24 V stack light is used as a simple visual maintenance cue. It turns model output into a physical signal that an operator can see and act on.
All core inference runs locally on the FR101. Telegram is only an operator messaging interface; no cloud LLM inference is required for the demo.


## Architecture
<img width="1672" height="941" alt="image" src="https://github.com/user-attachments/assets/67200990-c80b-4767-8e31-0376bf8e8af4" />

USB Camera
  -> Edge Impulse INT8 QNN FOMO-AD model
  -> Qualcomm NPU / DSP acceleration
  -> live anomaly heatmap
  -> repeated threshold confirmation
  -> FR101 GPIO / DIO output
  -> 24 V stack light maintenance cue
  -> [Qwen 0.5B](https://docs.edgeimpulse.com/projects/expert-network/integrating-slms-on-linux#offline-slms-for-edge-ai-development-part-1-direct-inference-with-a-qwen-lora-adapter) local SLM operator note
  -> optional [SmolVLM2](https://huggingface.co/HuggingFaceTB/SmolVLM2-500M-Video-Instruct) visual inspection summary
  -> Telegram / CLI / OpenCode operator control


<img width="500" height="500" alt="Qq6aevFxXeuAsNc_ONLOGIC" src="https://github.com/user-attachments/assets/1692562e-8c40-4b79-adae-7898ce310ab0" />



## QNN Low latency model - always on

<img width="1672" height="941" alt="image" src="https://github.com/user-attachments/assets/03f6700c-0769-4bec-9dc5-e3f10af5516b" />


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

## ENABLE GPIO:

export FR101_ALLOW_LIGHT_CONTROL=true

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




## What is [edge impulse](edgeimpulse.com)?
<img width="960" height="540" alt="Intro" src="https://github.com/user-attachments/assets/8b7b68d3-a16c-4e83-8ec2-84363f1873bb" />
<img width="960" height="540" alt="Intro (1)" src="https://github.com/user-attachments/assets/6fe6fbb8-a974-43ea-b22d-42c91be368a3" />
<img width="960" height="540" alt="Intro (2)" src="https://github.com/user-attachments/assets/1f2f604f-38e1-4496-b6f7-af77f67a461d" />
<img width="960" height="540" alt="Intro (3)" src="https://github.com/user-attachments/assets/69991fd2-8a64-477a-bdd8-e9b55631a876" />


