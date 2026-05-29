#!/usr/bin/env python3
import argparse
import time
import cv2


def open_camera(device: str, width: int, height: int, fps: int):
    cap = cv2.VideoCapture(device, cv2.CAP_V4L2)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open camera device: {device}")
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    cap.set(cv2.CAP_PROP_FPS, fps)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    print(f"Opened {device} requested={width}x{height}@{fps} actual={cap.get(cv2.CAP_PROP_FRAME_WIDTH)}x{cap.get(cv2.CAP_PROP_FRAME_HEIGHT)}@{cap.get(cv2.CAP_PROP_FPS)}")
    return cap


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--device", default="/dev/video2")
    parser.add_argument("--width", type=int, default=640)
    parser.add_argument("--height", type=int, default=480)
    parser.add_argument("--fps", type=int, default=15)
    parser.add_argument("--output", default="kiyo_test.jpg")
    args = parser.parse_args()
    cap = open_camera(args.device, args.width, args.height, args.fps)
    try:
        frame = None
        ok = False
        for _ in range(20):
            ok, frame = cap.read()
            if ok and frame is not None:
                break
            time.sleep(0.1)
        if not ok or frame is None:
            raise RuntimeError("Camera opened but did not return a valid frame")
        cv2.imwrite(args.output, frame)
        print(f"Saved {args.output}; shape={frame.shape}")
    finally:
        cap.release()

if __name__ == "__main__":
    main()
