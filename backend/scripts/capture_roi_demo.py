"""
Script chụp minh họa Driver ROI và Chest ROI trên ảnh cabin.
Chạy: python -X utf8 scripts/capture_roi_demo.py
"""
import sys
sys.path.insert(0, ".")

import cv2
import numpy as np
from app.edge.yolo_detector import YoloDetector
from app.edge.pose_estimator import PoseEstimator
from app.edge.behavior_rules import build_driver_roi, build_chest_roi
from app.common.config import load_config

cfg = load_config()

detector = YoloDetector(
    model_path=cfg["models"]["yolo_path"],
    conf=cfg["edge"]["conf_threshold"],
    iou=cfg["edge"]["iou_threshold"],
)

pose_est = PoseEstimator(
    min_detection_confidence=cfg["pose"]["min_detection_confidence"],
    min_tracking_confidence=cfg["pose"]["min_tracking_confidence"],
    min_visibility=cfg["pose"].get("min_visibility", 0.35),
    model_complexity=cfg["pose"].get("model_complexity", 0),
    gamma=cfg["pose"].get("gamma", 1.18),
    use_brighten=cfg["pose"].get("use_brighten", True),
)

source = "data/sample_videos/test.mp4"
cap = cv2.VideoCapture(source)

resize_w = cfg["edge"].get("resize_width", 640)

# Duyệt video, tìm frame có pose landmarks
found = False
for i in range(500):
    ok, frame = cap.read()
    if not ok:
        break
    h, w = frame.shape[:2]
    if w > resize_w:
        scale = resize_w / w
        frame = cv2.resize(frame, (resize_w, int(h * scale)))

    detections = detector.predict(frame, imgsz=resize_w)
    pose = pose_est.predict(frame)

    if pose.points and len(pose.points) >= 6:
        print(f"Frame {i}: Found {len(pose.points)} pose landmarks: {list(pose.points.keys())}")

        h, w = frame.shape[:2]
        driver_roi = build_driver_roi(pose, w, h)
        chest_roi = build_chest_roi(pose, w, h)

        print(f"  Driver ROI: {driver_roi}")
        print(f"  Chest ROI: {chest_roi}")

        # Bắt đầu vẽ
        out = frame.copy()

        # 1. Vẽ pose landmarks + connections
        # connections pairs cho 13 landmarks
        connections = [
            ("nose", "left_ear"), ("nose", "right_ear"),
            ("nose", "left_shoulder"), ("nose", "right_shoulder"),
            ("left_shoulder", "left_elbow"), ("right_shoulder", "right_elbow"),
            ("left_elbow", "left_wrist"), ("right_elbow", "right_wrist"),
            ("left_shoulder", "right_shoulder"),
            ("left_shoulder", "left_hip"), ("right_shoulder", "right_hip"),
            ("left_hip", "right_hip"),
        ]
        for a, b in connections:
            pa = pose.points.get(a)
            pb = pose.points.get(b)
            if pa and pb:
                cv2.line(out, pa, pb, (0, 255, 255), 2, cv2.LINE_AA)

        for name, (x, y) in pose.points.items():
            cv2.circle(out, (x, y), 5, (0, 255, 255), -1, cv2.LINE_AA)

        # 2. Vẽ bounding boxes từ YOLO
        for det in detections:
            x1, y1, x2, y2 = det.bbox
            cv2.rectangle(out, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(out, f"{det.class_name} {det.confidence:.2f}",
                        (x1, max(15, y1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        # 3. Vẽ Driver ROI (xanh dương, nét đứt)
        if driver_roi:
            rx1, ry1, rx2, ry2 = [int(v) for v in driver_roi]
            dash_len = 12
            # Top edge
            for x in range(rx1, rx2, dash_len * 2):
                cv2.line(out, (x, ry1), (min(x + dash_len, rx2), ry1), (255, 50, 0), 3)
            # Bottom edge
            for x in range(rx1, rx2, dash_len * 2):
                cv2.line(out, (x, ry2), (min(x + dash_len, rx2), ry2), (255, 50, 0), 3)
            # Left edge
            for y in range(ry1, ry2, dash_len * 2):
                cv2.line(out, (rx1, y), (rx1, min(y + dash_len, ry2)), (255, 50, 0), 3)
            # Right edge
            for y in range(ry1, ry2, dash_len * 2):
                cv2.line(out, (rx2, y), (rx2, min(y + dash_len, ry2)), (255, 50, 0), 3)
            # Label background
            (tw, th), _ = cv2.getTextSize("Driver ROI", cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)
            cv2.rectangle(out, (rx1, ry1 - th - 12), (rx1 + tw + 10, ry1 - 4), (255, 50, 0), -1)
            cv2.putText(out, "Driver ROI", (rx1 + 5, ry1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

        # 4. Vẽ Chest ROI (cam đỏ, nét liền)
        if chest_roi:
            cx1, cy1, cx2, cy2 = [int(v) for v in chest_roi]
            cv2.rectangle(out, (cx1, cy1), (cx2, cy2), (0, 100, 255), 3)
            (tw, th), _ = cv2.getTextSize("Chest ROI", cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)
            cv2.rectangle(out, (cx1, cy1 - th - 12), (cx1 + tw + 10, cy1 - 4), (0, 100, 255), -1)
            cv2.putText(out, "Chest ROI", (cx1 + 5, cy1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

        # Lưu ảnh
        output_path = "outputs/roi_demo.jpg"
        cv2.imwrite(output_path, out)
        print(f"\nDa luu anh minh hoa tai: {output_path}")
        print(f"Kich thuoc anh: {out.shape[1]}x{out.shape[0]}")
        found = True
        break

cap.release()
pose_est.close()

if not found:
    print("Khong tim thay frame co du pose landmarks.")
