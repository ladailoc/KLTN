from __future__ import annotations
import json
from collections import deque
from dataclasses import asdict
from pathlib import Path
from typing import Dict

import cv2

from app.common.types import AlertEvent
from app.common.utils import ensure_dir

class EvidenceWriter:
    def __init__(self, alerts_dir: str, buffer_size: int = 150):
        self.base_dir = ensure_dir(alerts_dir)
        self.frame_buffer = deque(maxlen=buffer_size)
        self.original_frame_buffer = deque(maxlen=buffer_size)

    def push_frame(self, frame) -> None:
        self.frame_buffer.append(frame.copy())

    def push_original_frame(self, frame) -> None:
        """Lưu frame gốc (chưa render overlay) để dùng cho SlowFast verification."""
        self.original_frame_buffer.append(frame.copy())

    def _crop_roi_frames(self, bbox, pad_ratio: float = 0.35):
        """Crop vùng ROI từ original frames dựa trên bounding box."""
        if not self.original_frame_buffer or bbox is None:
            return []

        x1, y1, x2, y2 = bbox
        bw, bh = x2 - x1, y2 - y1
        pad_x = int(bw * pad_ratio)
        pad_y = int(bh * pad_ratio)

        cropped = []
        for frm in self.original_frame_buffer:
            h, w = frm.shape[:2]
            cx1 = max(0, x1 - pad_x)
            cy1 = max(0, y1 - pad_y)
            cx2 = min(w, x2 + pad_x)
            cy2 = min(h, y2 + pad_y)

            if cx2 <= cx1 or cy2 <= cy1:
                continue

            crop = frm[cy1:cy2, cx1:cx2]
            if crop.size > 0:
                cropped.append(crop)

        return cropped

    def persist_roi_clip(self, alert: AlertEvent, day_dir: Path, stem: str, fps: float = 20.0) -> str | None:
        """Tạo clip crop ROI từ original frames (không có overlay) cho SlowFast."""
        cropped = self._crop_roi_frames(alert.bbox)
        if not cropped:
            return None

        roi_clip_path = str(day_dir / f"{stem}_roi.mp4")
        h, w = cropped[0].shape[:2]
        writer = cv2.VideoWriter(
            roi_clip_path,
            cv2.VideoWriter_fourcc(*"mp4v"),
            fps if fps > 0 else 20.0,
            (w, h),
        )
        for frm in cropped:
            writer.write(frm)
        writer.release()

        return roi_clip_path

    def persist_alert(self, alert: AlertEvent, fps: float = 20.0) -> Dict[str, str]:
        day_dir = ensure_dir(self.base_dir / alert.timestamp[:10])
        stem = f"{alert.event_type}_{alert.frame_index}"

        frame_path = str(day_dir / f"{stem}.jpg")
        clip_path = str(day_dir / f"{stem}.mp4")
        event_json_path = str(day_dir / f"{stem}.json")
        roi_clip_path = None

        if self.frame_buffer:
            cv2.imwrite(frame_path, self.frame_buffer[-1])

            h, w = self.frame_buffer[-1].shape[:2]
            writer = cv2.VideoWriter(
                clip_path,
                cv2.VideoWriter_fourcc(*"mp4v"),
                fps if fps > 0 else 20.0,
                (w, h),
            )
            for frm in self.frame_buffer:
                writer.write(frm)
            writer.release()

        # Tạo ROI clip từ original frames (không overlay) cho SlowFast
        roi_clip_path = self.persist_roi_clip(alert, day_dir, stem, fps)

        payload = asdict(alert)
        payload.update(
            {
                "frame_path": frame_path,
                "clip_path": clip_path,
                "roi_clip_path": roi_clip_path,
                "event_json_path": event_json_path,
            }
        )
        with open(event_json_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

        return {
            "frame_path": frame_path,
            "clip_path": clip_path,
            "roi_clip_path": roi_clip_path or "",
            "event_json_path": event_json_path,
        }