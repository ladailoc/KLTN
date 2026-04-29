from __future__ import annotations
from typing import Iterable
import cv2

from app.common.types import AlertEvent, Detection, PoseResult

class OverlayRenderer:
    def draw(self, frame, detections: list[Detection], pose: PoseResult, alerts: Iterable[AlertEvent], fps: float):
        out = frame.copy()

        for det in detections:
            x1, y1, x2, y2 = det.bbox
            cv2.rectangle(out, (x1, y1), (x2, y2), (0, 255, 0), 2)
            label = f"{det.class_name} {det.confidence:.2f}"
            cv2.putText(out, label, (x1, max(20, y1 - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        for name, (x, y) in pose.points.items():
            cv2.circle(out, (x, y), 4, (255, 0, 0), -1)
            cv2.putText(out, name, (x + 5, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 0), 1)

        y0 = 30
        cv2.putText(out, f"FPS: {fps:.2f}", (10, y0), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

        y = y0 + 30
        for alert in alerts:
            text = f"ALERT: {alert.event_type} ({alert.confidence:.2f})"
            cv2.putText(out, text, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            y += 28

        return out