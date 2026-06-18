from __future__ import annotations
import json
import os
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional

import requests

from app.common.utils import ensure_dir, now_iso

logger = logging.getLogger("upload_queue")

# Retryable errors — network/timeout/server-side
_RETRYABLE = (
    requests.ConnectionError,
    requests.Timeout,
)

MAX_RETRIES = 5
RETRY_INTERVAL_SEC = 30      # tối thiểu 30s giữa các retry
MAX_AGE_SEC = 24 * 3600      # bỏ qua entry cũ hơn 24h


class UploadQueue:
    """Hàng đợi upload bền vững — lưu vào JSON, retry tự động khi có mạng."""

    def __init__(self, queue_path: str, api_client, edge_logger=None):
        self.queue_path = Path(queue_path)
        self.api_client = api_client
        self.log = edge_logger or logger
        self._entries: List[dict] = []
        self._last_flush_time: float = 0.0
        self._load()

    # ── Persistence ────────────────────────────────────────────────

    def _load(self) -> None:
        if not self.queue_path.exists():
            self._entries = []
            return
        try:
            with open(self.queue_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._entries = data.get("entries", [])
            self.log.info(f"[UPLOAD QUEUE] Loaded {len(self._entries)} pending item(s)")
        except Exception as e:
            self.log.warning(f"[UPLOAD QUEUE] Cannot load queue: {e}")
            self._entries = []

    def _save(self) -> None:
        ensure_dir(self.queue_path.parent)
        tmp = self.queue_path.with_suffix(".tmp")
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump({"entries": self._entries}, f, ensure_ascii=False, indent=2)
            tmp.replace(self.queue_path)
        except Exception as e:
            self.log.error(f"[UPLOAD QUEUE] Cannot save queue: {e}")

    # ── Enqueue ────────────────────────────────────────────────────

    def enqueue(self, alert_dict: dict, saved_paths: Dict[str, str], error: str = "") -> None:
        """Thêm 1 alert vào hàng đợi khi upload thất bại."""
        entry = {
            "alert": alert_dict,
            "saved_paths": saved_paths,
            "queued_at": now_iso(),
            "retry_count": 0,
            "last_error": str(error)[:500],
        }
        self._entries.append(entry)
        self._save()
        self.log.warning(
            f"[UPLOAD QUEUE] Enqueued: {alert_dict.get('event_type')} "
            f"frame={alert_dict.get('frame_index')} | total_pending={len(self._entries)}"
        )

    # ── Flush ──────────────────────────────────────────────────────

    def flush(self, verify: bool = True) -> None:
        """Thử upload tất cả entry đang chờ. Xóa nếu thành công."""
        if not self._entries:
            return

        # Rate limit: không flush quá nhanh
        now = time.time()
        if now - self._last_flush_time < RETRY_INTERVAL_SEC:
            return
        self._last_flush_time = now

        self.log.info(f"[UPLOAD QUEUE] Flushing {len(self._entries)} pending item(s)...")
        remaining: List[dict] = []
        success_count = 0
        skip_count = 0

        for entry in self._entries:
            alert_dict = entry["alert"]
            saved_paths = entry["saved_paths"]
            retry_count = entry.get("retry_count", 0)
            event_label = f"{alert_dict.get('event_type')}@frame{alert_dict.get('frame_index')}"

            # Skip: quá số lần retry
            if retry_count >= MAX_RETRIES:
                self.log.warning(f"[UPLOAD QUEUE] Drop (max retries): {event_label}")
                skip_count += 1
                continue

            # Skip: quá cũ
            queued_at = entry.get("queued_at", "")
            if queued_at:
                try:
                    from datetime import datetime
                    qt = datetime.fromisoformat(queued_at)
                    age = (datetime.now() - qt).total_seconds()
                    if age > MAX_AGE_SEC:
                        self.log.warning(f"[UPLOAD QUEUE] Drop (stale {age:.0f}s): {event_label}")
                        skip_count += 1
                        continue
                except Exception:
                    pass

            # Kiểm tra file còn tồn tại không
            missing_files = self._check_files(saved_paths)
            if missing_files:
                self.log.warning(
                    f"[UPLOAD QUEUE] Drop (missing files {missing_files}): {event_label}"
                )
                skip_count += 1
                continue

            # Thử upload
            try:
                from app.common.types import AlertEvent
                alert = AlertEvent(
                    event_type=alert_dict["event_type"],
                    confidence=alert_dict["confidence"],
                    frame_index=alert_dict["frame_index"],
                    timestamp=alert_dict["timestamp"],
                    source_device=alert_dict.get("source_device", "edge-01"),
                    note=alert_dict.get("note", ""),
                )
                self.api_client.send_alert_and_verify(
                    alert=alert,
                    saved_paths=saved_paths,
                    verify=verify,
                )
                success_count += 1
                self.log.info(f"[UPLOAD QUEUE] OK: {event_label}")

            except _RETRYABLE as e:
                # Mạng vẫn lỗi — giữ lại, tăng retry_count
                entry["retry_count"] = retry_count + 1
                entry["last_error"] = str(e)[:500]
                remaining.append(entry)
                self.log.info(
                    f"[UPLOAD QUEUE] Retry {retry_count + 1}/{MAX_RETRIES}: {event_label} | {e}"
                )

            except requests.HTTPError as e:
                status = e.response.status_code if e.response is not None else 0
                if status == 408 or status >= 500:
                    # Server lỗi — giữ lại retry
                    entry["retry_count"] = retry_count + 1
                    entry["last_error"] = f"HTTP {status}: {str(e)[:200]}"
                    remaining.append(entry)
                    self.log.info(f"[UPLOAD QUEUE] Retry (HTTP {status}): {event_label}")
                else:
                    # 4xx client error — không retry, drop
                    self.log.warning(f"[UPLOAD QUEUE] Drop (HTTP {status}): {event_label}")
                    skip_count += 1

            except Exception as e:
                # Lỗi không xác định — giữ lại
                entry["retry_count"] = retry_count + 1
                entry["last_error"] = str(e)[:500]
                remaining.append(entry)
                self.log.warning(f"[UPLOAD QUEUE] Retry (unknown): {event_label} | {e}")

        self._entries = remaining
        self._save()

        total = success_count + skip_count + len(remaining)
        if total > 0:
            self.log.info(
                f"[UPLOAD QUEUE] Flush done: {success_count} ok, "
                f"{skip_count} dropped, {len(remaining)} still pending"
            )

    # ── Helpers ────────────────────────────────────────────────────

    @staticmethod
    def _check_files(saved_paths: Dict[str, str]) -> List[str]:
        """Kiểm tra các file evidence còn tồn tại không."""
        missing = []
        for key, path in saved_paths.items():
            if path and not os.path.exists(path):
                missing.append(key)
        return missing

    @property
    def pending_count(self) -> int:
        return len(self._entries)
