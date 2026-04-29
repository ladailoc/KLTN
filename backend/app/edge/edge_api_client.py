from __future__ import annotations
from typing import Dict, Optional
import requests

from app.common.types import AlertEvent


class EdgeApiClient:
    def __init__(self, server_url: str, timeout_sec: int = 10, verify_timeout_sec: int = 120):
        self.base_url = server_url.rstrip("/")
        self.timeout_sec = timeout_sec
        self.verify_timeout_sec = verify_timeout_sec

    def send_alert(self, alert: AlertEvent, saved_paths: Dict[str, str]) -> dict:
        url = f"{self.base_url}/alerts"

        data = {
            "event_type": alert.event_type,
            "timestamp": alert.timestamp,
            "confidence": str(alert.confidence),
            "frame_index": str(alert.frame_index),
            "source_device": alert.source_device,
            "notes": alert.note,
        }

        files = {}
        try:
            if saved_paths.get("frame_path"):
                files["frame_file"] = open(saved_paths["frame_path"], "rb")
            if saved_paths.get("clip_path"):
                files["clip_file"] = open(saved_paths["clip_path"], "rb")
            if saved_paths.get("event_json_path"):
                files["event_file"] = open(saved_paths["event_json_path"], "rb")

            response = requests.post(url, data=data, files=files, timeout=self.timeout_sec)
            response.raise_for_status()
            return response.json()
        finally:
            for f in files.values():
                f.close()

    def verify_alert(self, alert_id: int) -> dict:
        url = f"{self.base_url}/alerts/{alert_id}/verify"
        response = requests.post(url, timeout=self.verify_timeout_sec)
        response.raise_for_status()
        return response.json()

    def send_alert_and_verify(
        self,
        alert: AlertEvent,
        saved_paths: Dict[str, str],
        verify: bool = True,
    ) -> Dict[str, Optional[dict]]:
        create_result = self.send_alert(alert, saved_paths)

        verify_result = None
        if verify:
            alert_id = create_result.get("id")
            if alert_id is not None:
                verify_result = self.verify_alert(int(alert_id))

        return {
            "create_result": create_result,
            "verify_result": verify_result,
        }