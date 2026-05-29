#!/usr/bin/env python3
import argparse
import cv2
import json
from edge_impulse_linux.image import ImageImpulseRunner


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model", default="models/fomo_ad_qnn.eim")
    p.add_argument("--image", default="qnn_test_frame.jpg")
    args = p.parse_args()

    frame_bgr = cv2.imread(args.image)
    if frame_bgr is None:
        raise RuntimeError(f"Could not read {args.image}")
    print("Input frame shape:", frame_bgr.shape)

    runner = ImageImpulseRunner(args.model)
    try:
        info = runner.init(debug=True)
        print(json.dumps(info, indent=2))
        params = info["model_parameters"]
        expected = params["input_features_count"]
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        features, _cropped = runner.get_features_from_image_auto_studio_settings(frame_rgb)
        print("Expected features:", expected)
        print("Actual features:", len(features))
        result = runner.classify(features)
        print(json.dumps(result, indent=2))
    finally:
        runner.stop()

if __name__ == "__main__":
    main()
