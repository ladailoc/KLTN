from __future__ import annotations
from typing import Dict, List
from app.common.constants import EVENT_NO_SEATBELT, EVENT_SMOKING, EVENT_USING_PHONE
from app.common.types import AlertEvent, CandidateEvent

# Cooldown giữa 2 lần alert cùng loại (quy đổi giây → frame, giả sử ~20 FPS)
ALERT_COOLDOWN_FRAMES = 80   # ~4 giây × 20 FPS


class AlertManager:
    def __init__(self, config: Dict):
        self.cfg = config
        self.counts = {
            EVENT_USING_PHONE: 0,
            EVENT_SMOKING: 0,
            EVENT_NO_SEATBELT: 0,
        }
        # Frame-based cooldown (thay cho time-based last_fired_sec)
        self.last_fired_frame = {
            EVENT_USING_PHONE: -9999,
            EVENT_SMOKING: -9999,
            EVENT_NO_SEATBELT: -9999,
        }

    def _need_frames(self, event_type: str) -> int:
        mapping = {
            EVENT_USING_PHONE: self.cfg["rules"]["phone_confirm_frames"],
            EVENT_SMOKING: self.cfg["rules"]["smoking_confirm_frames"],
            EVENT_NO_SEATBELT: self.cfg["rules"]["no_seatbelt_confirm_frames"],
        }
        return mapping[event_type]

    def update(
        self,
        candidates: List[CandidateEvent],
        frame_index: int,
        timestamp_iso: str,
        current_time_sec: float,
        source_device: str,
    ) -> List[AlertEvent]:
        candidate_map: Dict[str, CandidateEvent] = {}
        for c in candidates:
            if c.event_type not in candidate_map or c.score > candidate_map[c.event_type].score:
                candidate_map[c.event_type] = c

        alerts: List[AlertEvent] = []

        for event_type in self.counts.keys():
            cand = candidate_map.get(event_type)
            if cand:
                self.counts[event_type] += 1
            else:
                self.counts[event_type] = max(0, self.counts[event_type] - 1)

            if cand and self.counts[event_type] >= self._need_frames(event_type):
                # Cooldown theo frame (không dùng time.time())
                if frame_index - self.last_fired_frame[event_type] >= ALERT_COOLDOWN_FRAMES:
                    alerts.append(
                        AlertEvent(
                            event_type=event_type,
                            confidence=cand.score,
                            frame_index=frame_index,
                            timestamp=timestamp_iso,
                            bbox=cand.bbox,
                            note=cand.note,
                            source_device=source_device,
                        )
                    )
                    self.last_fired_frame[event_type] = frame_index
                    self.counts[event_type] = 0
        return alerts