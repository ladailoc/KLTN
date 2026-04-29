from __future__ import annotations
import argparse
import cv2

from app.common.config import load_config, reset_config_cache
from app.edge.behavior_rules import BehaviorRules
from app.edge.overlay_renderer import OverlayRenderer
from app.edge.pose_estimator import PoseEstimator
from app.edge.yolo_detector import YoloDetector
from app.common.types import PoseResult


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--image", required=True, help="Path tới ảnh test")
    parser.add_argument("--save", default="outputs/test_image_result.jpg")
    args = parser.parse_args()

    reset_config_cache()
    cfg = load_config(args.config)

    img = cv2.imread(args.image)
    if img is None:
        raise FileNotFoundError(f"Không đọc được ảnh: {args.image}")

    detector = YoloDetector(
        model_path=cfg["models"]["yolo_path"],
        conf=cfg["edge"]["conf_threshold"],
        iou=cfg["edge"]["iou_threshold"],
    )

    pose_estimator = None
    if cfg["pose"]["enabled"]:
        pose_estimator = PoseEstimator(
            min_detection_confidence=cfg["pose"]["min_detection_confidence"],
            min_tracking_confidence=cfg["pose"]["min_tracking_confidence"],
            min_visibility=cfg["pose"].get("min_visibility", 0.35),
            model_complexity=cfg["pose"].get("model_complexity", 1),
            gamma=cfg["pose"].get("gamma", 1.18),
            use_brighten=cfg["pose"].get("use_brighten", True),
        )

    rules = BehaviorRules(cfg)
    renderer = OverlayRenderer()

    detections = detector.predict(img)
    pose = pose_estimator.predict(img) if pose_estimator else PoseResult(points={})
    candidates = rules.infer(detections, pose, img.shape)

    print("===== DETECTIONS =====")
    for d in detections:
        print(d)

    print("\n===== CANDIDATES =====")
    for c in candidates:
        print(c)

    rendered = renderer.draw(img, detections, pose, [], fps=0.0)
    cv2.imwrite(args.save, rendered)
    print(f"\nĐã lưu ảnh kết quả tại: {args.save}")

    if pose_estimator:
        pose_estimator.close()


if __name__ == "__main__":
    main()

# python -m scripts.test_image --image data/sample_images/test.png