"""
Script vẽ Driver ROI và Chest ROI trên ảnh tĩnh.
Chạy: python -X utf8 scripts/capture_roi_on_image.py
"""
import sys
sys.path.insert(0, ".")

import cv2
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

source = "data/sample_images/test.png"
frame = cv2.imread(source)
if frame is None:
    print(f"Khong the doc anh: {source}")
    sys.exit(1)

resize_w = cfg["edge"].get("resize_width", 640)
h, w = frame.shape[:2]
if w > resize_w:
    scale = resize_w / w
    frame = cv2.resize(frame, (resize_w, int(h * scale)))

detections = detector.predict(frame, imgsz=resize_w)
pose = pose_est.predict(frame)

print(f"Pose landmarks: {len(pose.points)} - {list(pose.points.keys())}")

h, w = frame.shape[:2]
driver_roi = build_driver_roi(pose, w, h)
chest_roi = build_chest_roi(pose, w, h)

print(f"Driver ROI: {driver_roi}")
print(f"Chest ROI: {chest_roi}")

out = frame.copy()

# 1. Pose landmarks + connections
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

# 2. YOLO detections
for det in detections:
    x1, y1, x2, y2 = det.bbox
    cv2.rectangle(out, (x1, y1), (x2, y2), (0, 255, 0), 2)
    cv2.putText(out, f"{det.class_name} {det.confidence:.2f}",
                (x1, max(15, y1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

# 3. Driver ROI (blue dashed)
if driver_roi:
    rx1, ry1, rx2, ry2 = [int(v) for v in driver_roi]
    dash_len = 12
    for x in range(rx1, rx2, dash_len * 2):
        cv2.line(out, (x, ry1), (min(x + dash_len, rx2), ry1), (255, 50, 0), 3)
    for x in range(rx1, rx2, dash_len * 2):
        cv2.line(out, (x, ry2), (min(x + dash_len, rx2), ry2), (255, 50, 0), 3)
    for y in range(ry1, ry2, dash_len * 2):
        cv2.line(out, (rx1, y), (rx1, min(y + dash_len, ry2)), (255, 50, 0), 3)
    for y in range(ry1, ry2, dash_len * 2):
        cv2.line(out, (rx2, y), (rx2, min(y + dash_len, ry2)), (255, 50, 0), 3)
    (tw, th), _ = cv2.getTextSize("Driver ROI", cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)
    cv2.rectangle(out, (rx1, ry1 - th - 12), (rx1 + tw + 10, ry1 - 4), (255, 50, 0), -1)
    cv2.putText(out, "Driver ROI", (rx1 + 5, ry1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

# 4. Chest ROI (orange solid)
if chest_roi:
    cx1, cy1, cx2, cy2 = [int(v) for v in chest_roi]
    cv2.rectangle(out, (cx1, cy1), (cx2, cy2), (0, 100, 255), 3)
    (tw, th), _ = cv2.getTextSize("Chest ROI", cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)
    cv2.rectangle(out, (cx1, cy1 - th - 12), (cx1 + tw + 10, cy1 - 4), (0, 100, 255), -1)
    cv2.putText(out, "Chest ROI", (cx1 + 5, cy1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

output_path = "outputs/roi_on_image.jpg"
cv2.imwrite(output_path, out)
print(f"\nDa luu anh minh hoa tai: {output_path}")
print(f"Kich thuoc anh: {out.shape[1]}x{out.shape[0]}")

pose_est.close()
