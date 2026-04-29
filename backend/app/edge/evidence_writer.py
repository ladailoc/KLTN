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

    def push_frame(self, frame) -> None:
        self.frame_buffer.append(frame.copy())

    def persist_alert(self, alert: AlertEvent, fps: float = 20.0) -> Dict[str, str]:
        day_dir = ensure_dir(self.base_dir / alert.timestamp[:10])
        stem = f"{alert.event_type}_{alert.frame_index}"

        frame_path = str(day_dir / f"{stem}.jpg")
        clip_path = str(day_dir / f"{stem}.mp4")
        event_json_path = str(day_dir / f"{stem}.json")

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

        payload = asdict(alert)
        payload.update(
            {
                "frame_path": frame_path,
                "clip_path": clip_path,
                "event_json_path": event_json_path,
            }
        )
        with open(event_json_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

        return {
            "frame_path": frame_path,
            "clip_path": clip_path,
            "event_json_path": event_json_path,
        }