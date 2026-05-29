#!/usr/bin/env python3
"""
FR101 Industrial Edge AI webinar demo.

Razer Kiyo camera -> Edge Impulse crack/FOMO-AD .eim -> repeated threshold
-> GPIO/DIO output -> local Qwen operator note. Optional VLM endpoint support
is included, but Qwen is the reliable local LLM path for the live webinar.

Tested flow:
  CPU .eim: stable live fallback
  QNN .eim: QAIRT path must be sourced; model init can work even if classify
            needs model/runtime validation
  Qwen 0.5B GGUF: served by llama.cpp on port 9876
"""

import argparse
import base64
import json
import signal
import subprocess
import threading
import time
from collections import deque
from pathlib import Path
from statistics import mean
from typing import Any, Deque, Dict, List, Optional, Tuple

import cv2
import requests
from flask import Flask, Response, jsonify, render_template_string, request
from edge_impulse_linux.image import ImageImpulseRunner


HTML_PAGE = """
<!doctype html>
<html>
<head>
    <title>FR101 Crack Detection Demo</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 32px; background: #f7f7f7; color: #111; }
        .layout { display: grid; grid-template-columns: 2fr 1fr; gap: 24px; align-items: start; }
        .card { background: white; padding: 20px; border-radius: 14px; box-shadow: 0 2px 10px rgba(0,0,0,0.08); margin-bottom: 18px; }
        img { width: 100%; border-radius: 10px; background: #222; min-height: 360px; object-fit: contain; }
        h1, h2 { margin-top: 0; }
        .metric { margin: 12px 0; }
        .label { color: #555; font-size: 14px; }
        .value { font-weight: bold; font-size: 24px; }
        .normal { color: #147a32; }
        .warn { color: #b25b00; }
        .alarm { color: #b00020; }
        .loading { color: #555; }
        button { font-size: 16px; padding: 10px 14px; margin: 6px 4px 6px 0; border: 0; border-radius: 8px; cursor: pointer; background: #111; color: white; }
        button.secondary { background: #666; }
        input { font-size: 16px; padding: 8px; width: 90px; }
        code { background: #eee; padding: 2px 5px; border-radius: 5px; word-break: break-all; }
        .small { font-size: 13px; color: #666; }
        .eventbox, .textbox { overflow: auto; background: #111; color: #eee; padding: 10px; border-radius: 8px; font-family: monospace; font-size: 12px; white-space: pre-wrap; }
        .eventbox { height: 180px; }
        .textbox { min-height: 90px; max-height: 220px; }
        table { width: 100%; border-collapse: collapse; font-size: 14px; }
        td, th { border-bottom: 1px solid #ddd; padding: 8px; text-align: left; }
        .badge { display: inline-block; padding: 4px 8px; border-radius: 999px; background: #eee; font-size: 13px; margin-left: 8px; }
    </style>
</head>
<body>
    <h1>FR101 Crack Detection Demo <span id="modeBadge" class="badge">loading</span></h1>
    <p>Razer Kiyo camera → Edge Impulse crack/FOMO-AD model → repeated threshold → GPIO/DIO output → local Qwen operator note.</p>

    <div class="layout">
        <div>
            <div class="card">
                <h2>Live Camera</h2>
                <img src="/video_feed" />
                <p class="small">The stream shows the latest annotated inference frame when the model is running. If no grid cells are returned, a red frame border is used on confirmed anomaly.</p>
            </div>

            <div class="card">
                <h2>Performance summary</h2>
                <table>
                    <tr><th>Metric</th><th>Current run</th></tr>
                    <tr><td>Model mode</td><td id="tableMode">-</td></tr>
                    <tr><td>Latest inference</td><td id="tableLatest">-</td></tr>
                    <tr><td>Average inference</td><td id="tableAvg">-</td></tr>
                    <tr><td>Min / max inference</td><td id="tableMinMax">-</td></tr>
                    <tr><td>Frames classified</td><td id="tableCount">-</td></tr>
                    <tr><td>Trigger rule</td><td id="tableRule">-</td></tr>
                    <tr><td>Visual anomaly cells</td><td id="tableCells">-</td></tr>
                    <tr><td>Last Qwen latency</td><td id="tableQwenLatency">-</td></tr>
                    <tr><td>Last VLM latency</td><td id="tableVlmLatency">-</td></tr>
                </table>
            </div>

            <div class="card">
                <h2>Qwen operator note</h2>
                <button onclick="runQwen()">Generate operator note</button>
                <pre id="qwenResult" class="textbox">-</pre>
            </div>

            <div class="card">
                <h2>Optional VLM result</h2>
                <button onclick="runVlm()">Run VLM on current frame</button>
                <pre id="vlmResult" class="textbox">-</pre>
            </div>
        </div>

        <div>
            <div class="card">
                <h2>Status</h2>
                <div class="metric"><div class="label">Model state</div><div id="modelState" class="value loading">Loading...</div></div>
                <div class="metric"><div class="label">Detection state</div><div id="state" class="value">Loading...</div></div>
                <div class="metric"><div class="label">Anomaly / crack score</div><div id="score" class="value">-</div></div>
                <div class="metric"><div class="label">Threshold</div><div><input id="thresholdInput" type="number" step="0.01" value="0.8"><button onclick="setThreshold()">Set</button></div></div>
                <div class="metric"><div class="label">Consecutive frames above threshold</div><div id="history" class="value">-</div></div>
                <div class="metric"><div class="label">Inference time</div><div id="inference" class="value">-</div></div>
                <div class="metric"><div class="label">GPIO output</div><div id="gpio" class="value">-</div></div>
                <h3>Manual output test</h3>
                <button onclick="lightOn()">Light ON</button><button class="secondary" onclick="lightOff()">Light OFF</button>
                <h3>Demo config</h3>
                <p class="small">
                    Camera: <code id="cameraDevice">-</code><br>
                    GPIO: <code id="gpioLine">-</code><br>
                    Model: <code id="modelPath">-</code><br>
                    Qwen: <code id="qwenUrl">-</code><br>
                    VLM: <code id="vlmUrl">-</code>
                </p>
            </div>
            <div class="card"><h2>Events</h2><pre id="events" class="eventbox"></pre></div>
        </div>
    </div>

<script>
function formatMs(value) { if (value === null || value === undefined) return '-'; return value.toFixed(2) + ' ms'; }
async function getStatus() {
    const res = await fetch('/status');
    const data = await res.json();
    document.getElementById('modeBadge').textContent = data.model_mode;
    document.getElementById('tableMode').textContent = data.model_mode;
    const modelState = document.getElementById('modelState');
    modelState.textContent = data.model_state;
    modelState.className = 'value ' + (data.model_state === 'ready' ? 'normal' : (data.model_state === 'error' ? 'alarm' : 'loading'));
    const state = document.getElementById('state');
    state.textContent = data.confirmed ? 'CRACK / ANOMALY CONFIRMED' : (data.above_threshold ? 'Above threshold' : 'Normal');
    state.className = 'value ' + (data.confirmed ? 'alarm' : (data.above_threshold ? 'warn' : 'normal'));
    document.getElementById('score').textContent = data.anomaly_score === null ? '-' : Number(data.anomaly_score).toFixed(4);
    document.getElementById('thresholdInput').value = data.threshold;
    document.getElementById('history').textContent = data.history.join(', ');
    document.getElementById('inference').textContent = formatMs(data.inference_ms);
    document.getElementById('gpio').textContent = data.output_on ? 'ON' : 'OFF';
    document.getElementById('cameraDevice').textContent = data.camera_device;
    document.getElementById('gpioLine').textContent = data.gpio_chip + ' line ' + data.gpio_line;
    document.getElementById('modelPath').textContent = data.model_path;
    document.getElementById('qwenUrl').textContent = data.qwen_url;
    document.getElementById('vlmUrl').textContent = data.vlm_url;
    document.getElementById('tableLatest').textContent = formatMs(data.inference_ms);
    document.getElementById('tableAvg').textContent = formatMs(data.inference_avg_ms);
    document.getElementById('tableMinMax').textContent = formatMs(data.inference_min_ms) + ' / ' + formatMs(data.inference_max_ms);
    document.getElementById('tableCount').textContent = data.inference_count;
    document.getElementById('tableRule').textContent = data.bad_frames + ' frames >= ' + data.threshold;
    document.getElementById('tableCells').textContent = data.visual_cell_count;
    document.getElementById('tableQwenLatency').textContent = formatMs(data.qwen_latency_ms);
    document.getElementById('tableVlmLatency').textContent = formatMs(data.vlm_latency_ms);
    document.getElementById('qwenResult').textContent = data.qwen_result || '-';
    document.getElementById('vlmResult').textContent = data.vlm_result || '-';
}
async function getEvents() { const res = await fetch('/events'); const data = await res.json(); document.getElementById('events').textContent = JSON.stringify(data.slice(-10), null, 2); }
async function setThreshold() { const value = parseFloat(document.getElementById('thresholdInput').value); await fetch('/set_threshold', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({threshold: value}) }); await getStatus(); }
async function lightOn() { await fetch('/light_on', {method: 'POST'}); await getStatus(); }
async function lightOff() { await fetch('/light_off', {method: 'POST'}); await getStatus(); }
async function runQwen() { document.getElementById('qwenResult').textContent = 'Running Qwen...'; await fetch('/run_qwen', {method: 'POST'}); await getStatus(); await getEvents(); }
async function runVlm() { document.getElementById('vlmResult').textContent = 'Running VLM...'; await fetch('/run_vlm', {method: 'POST'}); await getStatus(); await getEvents(); }
setInterval(getStatus, 500); setInterval(getEvents, 1500); getStatus(); getEvents();
</script>
</body>
</html>
"""


class DigitalOutput:
    def __init__(self, chip: str, line: int, active_low: bool = False, dry_run: bool = True) -> None:
        self.chip = chip
        self.line = line
        self.active_low = active_low
        self.dry_run = dry_run
        self.state = False
        self.lock = threading.Lock()

    def _physical_value(self, logical_on: bool) -> int:
        if self.active_low:
            return 0 if logical_on else 1
        return 1 if logical_on else 0

    def set(self, logical_on: bool) -> None:
        with self.lock:
            value = self._physical_value(logical_on)
            self.state = logical_on
            if self.dry_run:
                print(f"[DIO:DRY_RUN] {self.chip} line {self.line} logical_on={logical_on} physical={value}")
                return
            subprocess.run(["gpioset", self.chip, f"{self.line}={value}"], check=True)

    def on(self) -> None:
        self.set(True)

    def off(self) -> None:
        self.set(False)

    def is_on(self) -> bool:
        with self.lock:
            return self.state


def extract_visual_anomaly_cells(result: Dict[str, Any]) -> List[Dict[str, float]]:
    """Extract grid/cell data from EI visual anomaly results, when available."""
    body = result.get("result", result)
    if not isinstance(body, dict):
        return []

    grid = body.get("visual_anomaly_grid") or body.get("anomaly_grid") or body.get("heatmap")
    if not isinstance(grid, list):
        return []

    cells: List[Dict[str, float]] = []
    for cell in grid:
        if not isinstance(cell, dict):
            continue
        score = None
        for key in ("value", "score", "anomaly", "anomaly_score"):
            value = cell.get(key)
            if isinstance(value, (int, float)):
                score = float(value)
                break
        if score is None:
            continue

        if all(isinstance(cell.get(k), (int, float)) for k in ("x", "y", "width", "height")):
            cells.append({"x": float(cell["x"]), "y": float(cell["y"]), "width": float(cell["width"]), "height": float(cell["height"]), "score": score})
        elif all(isinstance(cell.get(k), (int, float)) for k in ("x0", "y0", "x1", "y1")):
            cells.append({"x": float(cell["x0"]), "y": float(cell["y0"]), "width": float(cell["x1"] - cell["x0"]), "height": float(cell["y1"] - cell["y0"]), "score": score})
    return cells


def extract_anomaly_score(result: Dict[str, Any]) -> Optional[float]:
    body = result.get("result", result)
    if not isinstance(body, dict):
        return None

    direct = body.get("anomaly")
    if isinstance(direct, (int, float)):
        return float(direct)

    # Some EI anomaly outputs include a list under result["anomaly"]
    if isinstance(direct, list):
        scores = [float(v.get("value", v.get("score"))) for v in direct if isinstance(v, dict) and isinstance(v.get("value", v.get("score")), (int, float))]
        if scores:
            return max(scores)

    cells = extract_visual_anomaly_cells(result)
    if cells:
        return max(float(cell["score"]) for cell in cells)

    classification = body.get("classification")
    if isinstance(classification, dict):
        for key in ("anomaly", "defect", "fault", "crack"):
            value = classification.get(key)
            if isinstance(value, (int, float)):
                return float(value)

    bounding_boxes = body.get("bounding_boxes")
    if isinstance(bounding_boxes, list):
        scores = []
        for box in bounding_boxes:
            if not isinstance(box, dict):
                continue
            label = str(box.get("label", "")).lower()
            value = box.get("value")
            if isinstance(value, (int, float)) and any(token in label for token in ("anomaly", "defect", "fault", "crack")):
                scores.append(float(value))
        if scores:
            return max(scores)

    return None


def scale_cells_to_frame(cells: List[Dict[str, float]], frame_width: int, frame_height: int, model_width: int, model_height: int) -> List[Dict[str, float]]:
    """Scale cells when they appear to be in model input coordinates instead of frame coordinates."""
    if not cells:
        return []

    max_x = max(cell["x"] + cell["width"] for cell in cells)
    max_y = max(cell["y"] + cell["height"] for cell in cells)
    if max_x <= model_width + 2 and max_y <= model_height + 2:
        sx = frame_width / float(model_width)
        sy = frame_height / float(model_height)
        return [{"x": c["x"] * sx, "y": c["y"] * sy, "width": c["width"] * sx, "height": c["height"] * sy, "score": c["score"]} for c in cells]
    return cells


def draw_visual_anomaly_overlay(frame_bgr: Any, result: Dict[str, Any], threshold: float, model_width: int, model_height: int, confirmed: bool) -> Tuple[Any, int]:
    """Draw visual anomaly grid. If grid is unavailable, draw a whole-frame red border on confirmed anomaly."""
    output = frame_bgr.copy()
    overlay = frame_bgr.copy()
    frame_height, frame_width = output.shape[:2]
    cells = scale_cells_to_frame(extract_visual_anomaly_cells(result), frame_width, frame_height, model_width, model_height)

    if not cells:
        if confirmed:
            cv2.rectangle(output, (4, 4), (frame_width - 5, frame_height - 5), (0, 0, 255), 5)
            cv2.putText(output, "ANOMALY CONFIRMED", (18, 42), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2, cv2.LINE_AA)
        return output, 0

    hot_count = 0
    for cell in cells:
        x = max(0, min(frame_width - 1, int(round(cell["x"]))))
        y = max(0, min(frame_height - 1, int(round(cell["y"]))))
        width = max(1, int(round(cell["width"])))
        height = max(1, int(round(cell["height"])))
        x2 = max(0, min(frame_width - 1, x + width))
        y2 = max(0, min(frame_height - 1, y + height))
        score = float(cell["score"])

        if score >= threshold:
            hot_count += 1
            color = (0, 0, 255)
            alpha = 0.35
            thickness = 2
        else:
            color = (0, 191, 255)
            alpha = 0.12
            thickness = 1

        cv2.rectangle(overlay, (x, y), (x2, y2), color, -1)
        cv2.rectangle(output, (x, y), (x2, y2), color, thickness)
        if score >= threshold:
            cv2.putText(output, f"{score:.2f}", (x + 3, max(14, y + 14)), cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1, cv2.LINE_AA)

    cv2.addWeighted(overlay, 0.25, output, 0.75, 0, output)
    return output, hot_count


def is_confirmed_anomaly(score_history: Deque[bool], required_bad_frames: int) -> bool:
    if len(score_history) < required_bad_frames:
        return False
    return all(list(score_history)[-required_bad_frames:])


def open_camera(device: str, width: int, height: int, fps: int) -> cv2.VideoCapture:
    camera = cv2.VideoCapture(device, cv2.CAP_V4L2)
    if not camera.isOpened():
        raise RuntimeError(f"Could not open camera device: {device}")
    camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    camera.set(cv2.CAP_PROP_FPS, fps)
    camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    print(f"[CAMERA] Opened {device} requested={width}x{height}@{fps} actual={camera.get(cv2.CAP_PROP_FRAME_WIDTH)}x{camera.get(cv2.CAP_PROP_FRAME_HEIGHT)}@{camera.get(cv2.CAP_PROP_FPS)}")
    return camera


def encode_frame_to_base64_jpeg(frame_bgr: Any) -> str:
    ok, jpeg = cv2.imencode(".jpg", frame_bgr)
    if not ok:
        raise RuntimeError("Could not encode frame to JPEG")
    return base64.b64encode(jpeg.tobytes()).decode("utf-8")


def call_llama_chat(url: str, messages: List[Dict[str, Any]], max_tokens: int, temperature: float, timeout: int) -> str:
    payload = {"messages": messages, "temperature": temperature, "max_tokens": max_tokens, "stream": False}
    response = requests.post(url, json=payload, timeout=timeout)
    response.raise_for_status()
    data = response.json()
    if "choices" in data and data["choices"]:
        return str(data["choices"][0].get("message", {}).get("content", "")).strip()
    if "content" in data:
        return str(data["content"]).strip()
    return json.dumps(data)


class DemoState:
    def __init__(self, args: argparse.Namespace) -> None:
        self.args = args
        self.output = DigitalOutput(args.gpio_chip, args.gpio_line, args.active_low, args.dry_run)
        self.lock = threading.Lock()
        self.latest_frame = None
        self.latest_jpeg = None
        self.display_jpeg = None
        self.model_state = "not_started"
        self.model_error = None
        self.anomaly_score = None
        self.inference_ms = None
        self.above_threshold = False
        self.confirmed = False
        self.threshold = args.threshold
        self.history: Deque[bool] = deque(maxlen=args.bad_frames)
        self.last_trigger_time = 0.0
        self.light_until = 0.0
        self.stop_requested = False
        self.events: List[Dict[str, Any]] = []
        self.inference_times: Deque[float] = deque(maxlen=args.perf_window)
        self.qwen_result = None
        self.qwen_latency_ms = None
        self.vlm_result = None
        self.vlm_latency_ms = None
        self.last_auto_llm_time = 0.0
        self.visual_cell_count = 0
        self.hot_visual_cell_count = 0
        self.model_width = args.model_width_hint
        self.model_height = args.model_height_hint

    def snapshot(self) -> Dict[str, Any]:
        with self.lock:
            times = list(self.inference_times)
            return {
                "model_mode": self.args.model_mode,
                "model_state": self.model_state,
                "model_error": self.model_error,
                "anomaly_score": self.anomaly_score,
                "inference_ms": self.inference_ms,
                "inference_avg_ms": mean(times) if times else None,
                "inference_min_ms": min(times) if times else None,
                "inference_max_ms": max(times) if times else None,
                "inference_count": len(times),
                "above_threshold": self.above_threshold,
                "confirmed": self.confirmed,
                "threshold": self.threshold,
                "bad_frames": self.args.bad_frames,
                "history": list(self.history),
                "output_on": self.output.is_on(),
                "camera_device": self.args.camera_device,
                "gpio_chip": self.args.gpio_chip,
                "gpio_line": self.args.gpio_line,
                "model_path": self.args.model,
                "dry_run": self.args.dry_run,
                "qwen_url": self.args.qwen_url,
                "vlm_url": self.args.vlm_url,
                "qwen_result": self.qwen_result,
                "qwen_latency_ms": self.qwen_latency_ms,
                "vlm_result": self.vlm_result,
                "vlm_latency_ms": self.vlm_latency_ms,
                "visual_cell_count": self.visual_cell_count,
                "hot_visual_cell_count": self.hot_visual_cell_count,
            }

    def add_event(self, event: Dict[str, Any]) -> None:
        with self.lock:
            self.events.append(event)
            self.events = self.events[-100:]


def camera_loop(state: DemoState) -> None:
    args = state.args
    camera = None
    try:
        camera = open_camera(args.camera_device, args.width, args.height, args.fps)
        state.add_event({"time": time.time(), "event": "camera_ready", "device": args.camera_device})
        while not state.stop_requested:
            ok, frame_bgr = camera.read()
            if not ok or frame_bgr is None:
                print("[WARN] Failed to read camera frame")
                state.add_event({"time": time.time(), "event": "camera_frame_failed"})
                time.sleep(0.2)
                continue
            ok_jpeg, jpeg = cv2.imencode(".jpg", frame_bgr)
            with state.lock:
                state.latest_frame = frame_bgr.copy()
                if ok_jpeg:
                    state.latest_jpeg = jpeg.tobytes()
                    if state.model_state not in ("ready", "error") or state.display_jpeg is None:
                        state.display_jpeg = jpeg.tobytes()
            time.sleep(0.03)
    except Exception as error:
        print(f"[ERROR] camera_loop failed: {error}")
        state.add_event({"time": time.time(), "event": "camera_error", "message": str(error)})
    finally:
        if camera is not None:
            camera.release()


def get_features_from_frame(runner: ImageImpulseRunner, frame_bgr: Any) -> Tuple[Any, Any]:
    frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    if hasattr(runner, "get_features_from_image_auto_studio_settings"):
        return runner.get_features_from_image_auto_studio_settings(frame_rgb)
    return runner.get_features_from_image(frame_rgb)


def run_qwen_note(state: DemoState) -> None:
    with state.lock:
        anomaly_score = state.anomaly_score
        threshold = state.threshold
        inference_ms = state.inference_ms
        confirmed = state.confirmed
        model_mode = state.args.model_mode
        visual_cells = state.visual_cell_count
        hot_cells = state.hot_visual_cell_count

    prompt = f"""
A local Edge Impulse visual anomaly model running on an OnLogic FR101 detected a possible physical surface crack.

System context:
- model mode: {model_mode}
- confirmed anomaly: {confirmed}
- anomaly score: {anomaly_score}
- threshold: {threshold}
- inference time ms: {inference_ms}
- visual anomaly cells: {visual_cells}
- hot visual cells over threshold: {hot_cells}

Write a concise industrial operator note with:
1. likely meaning,
2. immediate check,
3. escalation recommendation,
4. evidence to log.

Keep it under 90 words.
""".strip()

    messages = [
        {"role": "system", "content": "You are an industrial maintenance assistant. The word crack means a physical crack in concrete, metal, plastic, or a machine component. Do not discuss cybersecurity, software cracking, hacking, or vulnerabilities. Keep the note practical and concise."},
        {"role": "user", "content": prompt},
    ]
    start = time.perf_counter()
    try:
        result = call_llama_chat(state.args.qwen_url, messages, state.args.qwen_max_tokens, 0.2, state.args.qwen_timeout)
        latency_ms = (time.perf_counter() - start) * 1000.0
        with state.lock:
            state.qwen_result = result
            state.qwen_latency_ms = latency_ms
        state.add_event({"time": time.time(), "event": "qwen_result", "latency_ms": round(latency_ms, 2), "result": result})
        print(f"[QWEN] {latency_ms:.2f} ms: {result}")
    except Exception as error:
        latency_ms = (time.perf_counter() - start) * 1000.0
        with state.lock:
            state.qwen_result = f"Qwen error: {error}"
            state.qwen_latency_ms = latency_ms
        state.add_event({"time": time.time(), "event": "qwen_error", "message": str(error)})


def run_vlm_analysis(state: DemoState) -> None:
    with state.lock:
        frame = None if state.latest_frame is None else state.latest_frame.copy()
        anomaly_score = state.anomaly_score
        threshold = state.threshold
    if frame is None:
        state.add_event({"time": time.time(), "event": "vlm_error", "message": "No frame available"})
        return
    image_b64 = encode_frame_to_base64_jpeg(frame)
    messages = [{"role": "user", "content": [{"type": "text", "text": f"Industrial inspection frame. Describe any visible physical cracks or surface damage. Edge anomaly score={anomaly_score}, threshold={threshold}. Do not overclaim."}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}]}]
    start = time.perf_counter()
    try:
        result = call_llama_chat(state.args.vlm_url, messages, state.args.vlm_max_tokens, 0.1, state.args.vlm_timeout)
        latency_ms = (time.perf_counter() - start) * 1000.0
        with state.lock:
            state.vlm_result = result
            state.vlm_latency_ms = latency_ms
        state.add_event({"time": time.time(), "event": "vlm_result", "latency_ms": round(latency_ms, 2), "result": result})
    except Exception as error:
        latency_ms = (time.perf_counter() - start) * 1000.0
        with state.lock:
            state.vlm_result = f"VLM error: {error}"
            state.vlm_latency_ms = latency_ms
        state.add_event({"time": time.time(), "event": "vlm_error", "message": str(error)})


def maybe_run_auto_llm(state: DemoState) -> None:
    if not state.args.auto_qwen_on_trigger:
        return
    with state.lock:
        now = time.time()
        if not state.confirmed or now - state.last_auto_llm_time < state.args.llm_cooldown_seconds:
            return
        state.last_auto_llm_time = now
    threading.Thread(target=run_qwen_note, args=(state,), daemon=True).start()


def model_loop(state: DemoState) -> None:
    args = state.args
    model_path = Path(args.model)
    if not model_path.exists():
        state.add_event({"time": time.time(), "event": "model_missing", "path": str(model_path)})
        with state.lock:
            state.model_state = "error"
            state.model_error = f"Model not found: {model_path}"
        return

    runner = ImageImpulseRunner(str(model_path))
    try:
        with state.lock:
            state.model_state = "initialising"
        state.add_event({"time": time.time(), "event": "model_initialising", "path": str(model_path), "mode": args.model_mode})
        print("[INIT] Starting Edge Impulse runner")
        model_info = runner.init(debug=args.debug)
        params = model_info.get("model_parameters", {})
        expected_features = int(params.get("input_features_count", 0))
        model_width = int(params.get("image_input_width", args.model_width_hint))
        model_height = int(params.get("image_input_height", args.model_height_hint))
        model_thresholds = params.get("thresholds", [])
        if args.use_model_threshold and model_thresholds:
            threshold = model_thresholds[0].get("min_anomaly_score")
            if isinstance(threshold, (int, float)):
                with state.lock:
                    state.threshold = float(threshold)
        with state.lock:
            state.model_state = "ready"
            state.model_width = model_width
            state.model_height = model_height
        state.add_event({"time": time.time(), "event": "model_ready", "mode": args.model_mode, "expected_features": expected_features, "model_width": model_width, "model_height": model_height})
        print("[INIT] Edge Impulse runner ready")
        state.output.off()

        frame_index = 0
        while not state.stop_requested:
            with state.lock:
                frame_bgr = None if state.latest_frame is None else state.latest_frame.copy()
                threshold_now = state.threshold
            if frame_bgr is None:
                time.sleep(0.1)
                continue

            start = time.perf_counter()
            features, _cropped = get_features_from_frame(runner, frame_bgr)
            if expected_features and len(features) != expected_features:
                raise RuntimeError(f"Feature length mismatch: got {len(features)}, expected {expected_features}")
            result = runner.classify(features)
            inference_ms = (time.perf_counter() - start) * 1000.0
            frame_index += 1

            if args.print_results_every and frame_index % args.print_results_every == 0:
                print("[RAW_RESULT]", json.dumps(result)[:4000])

            anomaly_score = extract_anomaly_score(result)
            above_threshold = anomaly_score is not None and anomaly_score >= threshold_now

            # Update history before drawing so whole-frame fallback knows confirmed state.
            with state.lock:
                state.history.append(above_threshold)
                state.confirmed = is_confirmed_anomaly(state.history, args.bad_frames)
                confirmed = state.confirmed

            cells = extract_visual_anomaly_cells(result)
            display_frame, hot_cell_count = draw_visual_anomaly_overlay(frame_bgr, result, threshold_now, model_width, model_height, confirmed)
            ok_jpeg, jpeg = cv2.imencode(".jpg", display_frame)

            with state.lock:
                state.anomaly_score = anomaly_score
                state.inference_ms = inference_ms
                state.inference_times.append(inference_ms)
                state.above_threshold = above_threshold
                state.visual_cell_count = len(cells)
                state.hot_visual_cell_count = hot_cell_count
                if ok_jpeg:
                    state.display_jpeg = jpeg.tobytes()
                now = time.time()
                can_trigger = now - state.last_trigger_time >= args.cooldown_seconds

            if confirmed and can_trigger:
                with state.lock:
                    state.last_trigger_time = time.time()
                    state.light_until = time.time() + args.light_seconds
                state.output.on()
                event = {"time": time.time(), "event": "confirmed_crack_or_anomaly", "score": anomaly_score, "threshold": threshold_now, "bad_frames_required": args.bad_frames, "inference_ms": round(inference_ms, 2), "model_mode": args.model_mode, "action": "digital_output_on", "gpio_chip": args.gpio_chip, "gpio_line": args.gpio_line, "light_seconds": args.light_seconds}
                state.add_event(event)
                print("[ACTION] " + json.dumps(event))
                maybe_run_auto_llm(state)

            with state.lock:
                light_should_turn_off = state.output.is_on() and time.time() >= state.light_until
            if light_should_turn_off:
                state.output.off()
                state.add_event({"time": time.time(), "event": "digital_output_off"})

            print(f"[FRAME] mode={args.model_mode} score={anomaly_score} threshold={threshold_now} cells={len(cells)} hot_cells={hot_cell_count} above={above_threshold} confirmed={confirmed} inference_ms={inference_ms:.2f}")
            time.sleep(max(0.0, args.loop_delay_seconds))
    except Exception as error:
        print(f"[ERROR] model_loop failed: {error}")
        with state.lock:
            state.model_state = "error"
            state.model_error = str(error)
        state.add_event({"time": time.time(), "event": "model_error", "message": str(error), "mode": args.model_mode})
    finally:
        try:
            state.output.off()
        except Exception:
            pass
        try:
            runner.stop()
        except Exception:
            pass


def create_app(state: DemoState) -> Flask:
    app = Flask(__name__)

    @app.route("/")
    def index():
        return render_template_string(HTML_PAGE)

    @app.route("/status")
    def status():
        return jsonify(state.snapshot())

    @app.route("/events")
    def events():
        with state.lock:
            return jsonify(state.events)

    @app.route("/set_threshold", methods=["POST"])
    def set_threshold():
        data = request.get_json(force=True)
        threshold = float(data.get("threshold", state.threshold))
        with state.lock:
            state.threshold = threshold
            state.history.clear()
        state.add_event({"time": time.time(), "event": "threshold_updated", "threshold": threshold})
        return jsonify({"threshold": threshold})

    @app.route("/light_on", methods=["POST"])
    def light_on():
        state.output.on()
        with state.lock:
            state.light_until = time.time() + state.args.light_seconds
        state.add_event({"time": time.time(), "event": "manual_light_on"})
        return jsonify({"output_on": True})

    @app.route("/light_off", methods=["POST"])
    def light_off():
        state.output.off()
        state.add_event({"time": time.time(), "event": "manual_light_off"})
        return jsonify({"output_on": False})

    @app.route("/run_qwen", methods=["POST"])
    def run_qwen_route():
        threading.Thread(target=run_qwen_note, args=(state,), daemon=True).start()
        return jsonify({"started": True})

    @app.route("/run_vlm", methods=["POST"])
    def run_vlm_route():
        threading.Thread(target=run_vlm_analysis, args=(state,), daemon=True).start()
        return jsonify({"started": True})

    @app.route("/video_feed")
    def video_feed():
        def generate():
            while not state.stop_requested:
                with state.lock:
                    jpeg = state.display_jpeg or state.latest_jpeg
                if jpeg is None:
                    time.sleep(0.1)
                    continue
                yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + jpeg + b"\r\n"
                time.sleep(0.05)
        return Response(generate(), mimetype="multipart/x-mixed-replace; boundary=frame")

    return app


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="FR101 Edge Impulse + local Qwen UI.")
    parser.add_argument("--model", required=True, help="Path to Edge Impulse .eim model.")
    parser.add_argument("--model-mode", default="CPU", help="Label shown in UI, for example CPU or QNN.")
    parser.add_argument("--camera-device", default="/dev/video2", help="Razer Kiyo camera device path.")
    parser.add_argument("--width", type=int, default=640, help="Camera width.")
    parser.add_argument("--height", type=int, default=480, help="Camera height.")
    parser.add_argument("--fps", type=int, default=15, help="Camera FPS.")
    parser.add_argument("--threshold", type=float, default=6.0, help="Anomaly threshold. Visual GMM projects often use scores around 6.0.")
    parser.add_argument("--use-model-threshold", action="store_true", help="Use min_anomaly_score from the .eim metadata when available.")
    parser.add_argument("--bad-frames", type=int, default=3, help="Consecutive frames required before action.")
    parser.add_argument("--cooldown-seconds", type=float, default=10.0, help="Minimum time between GPIO triggers.")
    parser.add_argument("--light-seconds", type=float, default=5.0, help="How long to keep output on.")
    parser.add_argument("--loop-delay-seconds", type=float, default=0.25, help="Delay between inference frames.")
    parser.add_argument("--perf-window", type=int, default=50, help="Number of inference timings for avg/min/max.")
    parser.add_argument("--model-width-hint", type=int, default=160, help="Used for overlay scaling before model metadata is available.")
    parser.add_argument("--model-height-hint", type=int, default=160, help="Used for overlay scaling before model metadata is available.")
    parser.add_argument("--gpio-chip", default="gpiochip5", help="GPIO chip exposed by Linux.")
    parser.add_argument("--gpio-line", type=int, default=0, help="GPIO line mapped to the FR101 DIO channel.")
    parser.add_argument("--active-low", action="store_true", help="Use active-low output logic.")
    parser.add_argument("--dry-run", action="store_true", help="Print output actions without touching GPIO.")
    parser.add_argument("--qwen-url", default="http://127.0.0.1:9876/v1/chat/completions", help="Qwen llama-server chat completions URL.")
    parser.add_argument("--vlm-url", default="http://127.0.0.1:9877/v1/chat/completions", help="Optional VLM llama-server chat completions URL.")
    parser.add_argument("--qwen-max-tokens", type=int, default=140, help="Max tokens for Qwen operator note.")
    parser.add_argument("--vlm-max-tokens", type=int, default=120, help="Max tokens for VLM result.")
    parser.add_argument("--qwen-timeout", type=int, default=120, help="Qwen request timeout seconds.")
    parser.add_argument("--vlm-timeout", type=int, default=300, help="VLM request timeout seconds.")
    parser.add_argument("--auto-qwen-on-trigger", action="store_true", help="Automatically run Qwen after confirmed anomaly.")
    parser.add_argument("--llm-cooldown-seconds", type=float, default=60.0, help="Minimum time between automatic Qwen runs.")
    parser.add_argument("--print-results-every", type=int, default=0, help="Print raw classification result every N frames for schema debugging.")
    parser.add_argument("--host", default="0.0.0.0", help="Web server host.")
    parser.add_argument("--port", type=int, default=8080, help="Web server port.")
    parser.add_argument("--debug", action="store_true", help="Enable Edge Impulse debug logs.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    state = DemoState(args)

    def handle_signal(_signum, _frame):
        state.stop_requested = True
        state.output.off()

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    threading.Thread(target=camera_loop, args=(state,), daemon=True).start()
    threading.Thread(target=model_loop, args=(state,), daemon=True).start()

    app = create_app(state)
    print(f"[WEB] Open http://<fr101-ip>:{args.port}")
    app.run(host=args.host, port=args.port, threaded=True)
    state.stop_requested = True
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
