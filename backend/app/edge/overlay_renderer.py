from __future__ import annotations
from typing import Dict, Tuple
import cv2

from app.common.types import AlertEvent, Detection, PoseResult

# ── Overlay style constants ──────────────────────────────────────────
BBOX_THICKNESS = 1
LABEL_FONT = cv2.FONT_HERSHEY_SIMPLEX
LABEL_FONT_SCALE = 0.5
LABEL_TEXT_THICKNESS = 1
LABEL_PADDING_X = 3
LABEL_PADDING_Y = 2

# Ngưỡng bbox nhỏ → chuyển sang label compact
SMALL_BBOX_WIDTH = 80
SMALL_BBOX_HEIGHT = 50

# Ngưỡng IoU để bỏ qua bbox trùng
IOU_DEDUP_THRESHOLD = 0.45

# Frame-based alert hold — per-class (phải khớp với pipeline)
ALERT_HOLD_FRAMES: dict = {
    "smoking": 45,
    "no_seatbelt": 60,
    "using_phone": 45,
}
ALERT_HOLD_FRAMES_DEFAULT = 45

# Màu sắc cho từng loại vi phạm (BGR)
ALERT_COLORS = {
    "using_phone": (0, 0, 255),      # đỏ
    "smoking": (0, 100, 255),         # cam
    "no_seatbelt": (0, 200, 255),     # vàng-cam
}

# Nhãn tiếng Việt (dùng cho bbox lớn)
ALERT_LABELS_VI = {
    "using_phone": "DUNG DIEN THOAI",
    "smoking": "HUT THUOC",
    "no_seatbelt": "KHONG THAT DAY AN TOAN",
}


def _iou(a: Tuple[int, int, int, int], b: Tuple[int, int, int, int]) -> float:
    """Tính IoU giữa 2 bbox (x1, y1, x2, y2)."""
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b

    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    inter = max(0, ix2 - ix1) * max(0, iy2 - iy1)

    area_a = max(0, ax2 - ax1) * max(0, ay2 - ay1)
    area_b = max(0, bx2 - bx1) * max(0, by2 - by1)
    union = area_a + area_b - inter

    return inter / union if union > 0 else 0.0


def _bbox_size(bbox: Tuple[int, int, int, int]) -> Tuple[int, int]:
    """Trả về (width, height) của bbox."""
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def _draw_bbox_label(frame, x1: int, y1: int, x2: int, y2: int,
                     label: str, color: tuple) -> None:
    """Vẻ bbox mỏng + label compact trên frame."""
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, BBOX_THICKNESS)

    (tw, th), baseline = cv2.getTextSize(label, LABEL_FONT, LABEL_FONT_SCALE, LABEL_TEXT_THICKNESS)

    # Background label
    bg_x1 = x1
    bg_y1 = y1 - th - LABEL_PADDING_Y * 2 - baseline
    bg_x2 = x1 + tw + LABEL_PADDING_X * 2
    bg_y2 = y1

    # Đảm bảo không ra ngoài frame
    h, w = frame.shape[:2]
    bg_y1 = max(0, bg_y1)
    bg_x2 = min(w, bg_x2)

    cv2.rectangle(frame, (bg_x1, bg_y1), (bg_x2, bg_y2), color, -1)

    # Text
    text_x = x1 + LABEL_PADDING_X
    text_y = bg_y2 - LABEL_PADDING_Y - baseline
    cv2.putText(frame, label, (text_x, text_y), LABEL_FONT,
                LABEL_FONT_SCALE, (255, 255, 255), LABEL_TEXT_THICKNESS)


class OverlayRenderer:
    def draw(self, frame, detections: list[Detection], pose: PoseResult,
             active_alerts: Dict[str, dict], fps: float, frame_index: int = 0):
        out = frame.copy()

        # Lọc alert còn hạn theo frame — TTL per class
        valid_alerts: list[AlertEvent] = []
        for etype, entry in active_alerts.items():
            hold = ALERT_HOLD_FRAMES.get(etype, ALERT_HOLD_FRAMES_DEFAULT)
            if frame_index - entry["last_seen_frame"] <= hold:
                valid_alerts.append(entry["alert"])

        # Thu thập bbox từ alerts
        alert_bboxes: list[tuple[int, int, int, int]] = []
        for alert in valid_alerts:
            if alert.bbox and len(alert.bbox) == 4:
                alert_bboxes.append(tuple(int(v) for v in alert.bbox))

        # ── 1. Vẽ detection bbox (xanh lá) — bỏ qua nếu trùng alert ──
        for det in detections:
            dx1, dy1, dx2, dy2 = det.bbox
            det_box = (dx1, dy1, dx2, dy2)

            if any(_iou(det_box, ab) > 0.3 for ab in alert_bboxes):
                continue

            bw, bh = _bbox_size(det_box)
            cv2.rectangle(out, (dx1, dy1), (dx2, dy2), (0, 255, 0), BBOX_THICKNESS)

            # Label compact cho detection
            if bw < SMALL_BBOX_WIDTH or bh < SMALL_BBOX_HEIGHT:
                label = f"{det.class_name} {det.confidence:.2f}"
            else:
                label = f"{det.class_name} {det.confidence:.0%}"

            (tw, th), baseline = cv2.getTextSize(label, LABEL_FONT, LABEL_FONT_SCALE, LABEL_TEXT_THICKNESS)
            bg_y1 = max(0, dy1 - th - LABEL_PADDING_Y * 2 - baseline)
            cv2.rectangle(out, (dx1, bg_y1),
                          (dx1 + tw + LABEL_PADDING_X * 2, dy1), (0, 255, 0), -1)
            cv2.putText(out, label,
                        (dx1 + LABEL_PADDING_X, dy1 - LABEL_PADDING_Y - baseline),
                        LABEL_FONT, LABEL_FONT_SCALE, (255, 255, 255), LABEL_TEXT_THICKNESS)

        # ── 2. Vẽ pose keypoints ──
        for name, (x, y) in pose.points.items():
            cv2.circle(out, (x, y), 2, (255, 0, 0), -1)
            cv2.putText(out, name, (x + 3, y - 3), LABEL_FONT, 0.25, (255, 0, 0), 1)

        # ── 3. Vẽ alert bbox (vi phạm) — chỉ từ valid_alerts ──
        drawn_alert_types: set[str] = set()
        drawn_alert_bboxes: list[tuple[int, int, int, int]] = []

        for alert in valid_alerts:
            if not alert.bbox or len(alert.bbox) != 4:
                continue

            x1, y1, x2, y2 = [int(v) for v in alert.bbox]
            alert_box = (x1, y1, x2, y2)

            # Bỏ qua nếu bbox trùng với alert đã vẽ
            if any(_iou(alert_box, db) > IOU_DEDUP_THRESHOLD for db in drawn_alert_bboxes):
                continue

            color = ALERT_COLORS.get(alert.event_type, (0, 0, 255))
            bw, bh = _bbox_size(alert_box)

            # Chọn label dựa trên kích thước bbox
            if bw < SMALL_BBOX_WIDTH or bh < SMALL_BBOX_HEIGHT:
                label = f"{alert.event_type} {alert.confidence:.2f}"
            else:
                vi_text = ALERT_LABELS_VI.get(alert.event_type, alert.event_type.upper())
                label = f"{vi_text} {alert.confidence:.0%}"

            _draw_bbox_label(out, x1, y1, x2, y2, label, color)

            drawn_alert_types.add(alert.event_type)
            drawn_alert_bboxes.append(alert_box)

        # ── 4. HUD: FPS ──
        y0 = 18
        fps_text = f"FPS: {fps:.1f}" if fps is not None else "FPS: --"
        cv2.putText(out, fps_text, (6, y0), LABEL_FONT, 0.4, (0, 255, 255), 1)

        # ── 5. HUD: Alert list — tối đa 1 dòng mỗi loại ──
        y = y0 + 14
        seen_types: set[str] = set()
        for alert in valid_alerts:
            if alert.event_type in seen_types:
                continue
            seen_types.add(alert.event_type)
            color = ALERT_COLORS.get(alert.event_type, (0, 0, 255))
            text = f"ALERT: {alert.event_type} ({alert.confidence:.2f})"
            cv2.putText(out, text, (6, y), LABEL_FONT, 0.35, color, 1)
            y += 14

        return out
