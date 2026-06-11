from __future__ import annotations
import json
import logging
import os
import subprocess
from collections import deque
from dataclasses import asdict
from pathlib import Path
from typing import Dict

import cv2

from app.common.types import AlertEvent
from app.common.utils import ensure_dir

logger = logging.getLogger("evidence_writer")

# ── Codec ưu tiên ─────────────────────────────────────────────────
# Ưu tiên H264 (.mp4) cho browser playback.
# Fallback: mp4v nếu ffmpeg cũng không có.
_CODEC_CANDIDATES = [
    ("H264", ".mp4"),
    ("avc1", ".mp4"),
    ("mp4v", ".mp4"),
]


def _has_ffmpeg() -> bool:
    """Kiểm tra ffmpeg có sẵn trên hệ thống không."""
    try:
        r = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True, timeout=5,
        )
        return r.returncode == 0
    except Exception:
        return False


# Cache kết quả kiểm tra ffmpeg
_FFMPEG_AVAILABLE: bool | None = None


def _ffmpeg_available() -> bool:
    global _FFMPEG_AVAILABLE
    if _FFMPEG_AVAILABLE is None:
        _FFMPEG_AVAILABLE = _has_ffmpeg()
        if _FFMPEG_AVAILABLE:
            logger.info("ffmpeg detected — will use as H264 fallback")
    return _FFMPEG_AVAILABLE


def _write_clip_ffmpeg(clip_path: str, frames: list, fps: float) -> str | None:
    """Ghi frames thành H264 .mp4 bằng ffmpeg subprocess.
    Trả về path hoặc None nếu thất bại.
    """
    if not frames:
        return None

    h, w = frames[0].shape[:2]

    # Đảm kích thước chia hết cho 2 (yêu cầu của libx264)
    if w % 2 != 0:
        w -= 1
    if h % 2 != 0:
        h -= 1

    output_path = str(Path(clip_path).with_suffix(".mp4"))

    try:
        # Gom tất cả frame thành 1 bytes blob, tránh deadlock pipe
        raw_data = b""
        for frm in frames:
            if frm.shape[:2] != (h, w):
                frm = cv2.resize(frm, (w, h))
            raw_data += frm.tobytes()

        cmd = [
            "ffmpeg", "-y",
            "-f", "rawvideo",
            "-vcodec", "rawvideo",
            "-s", f"{w}x{h}",
            "-pix_fmt", "bgr24",
            "-r", str(fps),
            "-i", "-",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", "23",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            output_path,
        ]

        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # communicate() xử lý đồng thời stdin/stdout/stderr → không deadlock
        stdout, stderr = proc.communicate(input=raw_data, timeout=60)

        if proc.returncode != 0:
            err_msg = stderr.decode("utf-8", errors="replace")[-500:]
            logger.warning(f"ffmpeg failed (rc={proc.returncode}): {err_msg}")
            return None

        if not os.path.exists(output_path) or os.path.getsize(output_path) < 100:
            logger.warning(f"ffmpeg output empty: {output_path}")
            return None

        logger.info(f"ffmpeg H264 OK: {output_path} ({os.path.getsize(output_path)} bytes)")
        return output_path

    except subprocess.TimeoutExpired:
        logger.warning("ffmpeg timeout (60s)")
        return None
    except Exception as e:
        logger.warning(f"ffmpeg exception: {e}")
        return None


def _make_video_writer(path: str, fps: float, width: int, height: int):
    """Tạo cv2.VideoWriter với codec tốt nhất khả dụng.
    Trả về (writer, actual_path) hoặc (None, None) nếu tất cả thất bại.
    """
    for fourcc_name, ext in _CODEC_CANDIDATES:
        actual_path = str(Path(path).with_suffix(ext))
        fourcc = cv2.VideoWriter_fourcc(*fourcc_name)
        writer = cv2.VideoWriter(actual_path, fourcc, fps, (width, height))
        if writer.isOpened():
            logger.info(f"VideoWriter OK: codec={fourcc_name}, path={actual_path}")
            return writer, actual_path
        writer.release()
        logger.warning(f"VideoWriter FAILED: codec={fourcc_name}")

    logger.error("ALL OpenCV codecs failed")
    return None, None


class EvidenceWriter:
    def __init__(self, alerts_dir: str, buffer_size: int = 64):
        self.base_dir = ensure_dir(alerts_dir)
        self.frame_buffer = deque(maxlen=buffer_size)
        self.original_frame_buffer = deque(maxlen=buffer_size)

    def push_frame(self, frame) -> None:
        self.frame_buffer.append(frame.copy())

    def push_original_frame(self, frame) -> None:
        """Lưu frame gốc (chưa render overlay) để dùng cho SlowFast verification."""
        self.original_frame_buffer.append(frame.copy())

    def clear_buffers(self) -> None:
        """Giải phóng bộ nhớ sau khi đã persist xong alert.
        Gọi sau persist_alert() để tránh OOM khi chạy video dài.
        """
        self.frame_buffer.clear()
        self.original_frame_buffer.clear()

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

    def _write_clip(self, clip_path: str, frames: list, fps: float) -> str | None:
        """Ghi list frame thành video clip.
        Ưu tiên: ffmpeg H264 → OpenCV VideoWriter.
        ffmpeg luôn tạo H264 .mp4 chuẩn browser.
        """
        if not frames:
            return None

        h, w = frames[0].shape[:2]

        # Lọc frame cùng kích thước
        valid_frames = [f for f in frames if f.shape[:2] == (h, w)]
        if not valid_frames:
            logger.warning("No valid frames with consistent dimensions")
            return None

        # Ưu tiên 1: ffmpeg H264 (tạo .mp4 chuẩn, browser play được)
        if _ffmpeg_available():
            result = _write_clip_ffmpeg(clip_path, valid_frames, fps)
            if result:
                return result
            logger.warning("ffmpeg failed, falling back to OpenCV")

        # Fallback: OpenCV VideoWriter (mp4v — có thể không play được trên browser)
        writer, actual_path = _make_video_writer(clip_path, fps, w, h)
        if writer is not None:
            for frm in valid_frames:
                writer.write(frm)
            writer.release()

            if os.path.exists(actual_path) and os.path.getsize(actual_path) >= 100:
                logger.warning(f"Using OpenCV mp4v (may not play in browser): {actual_path}")
                return actual_path

        logger.error(f"Cannot write video clip: {clip_path}")
        return None

    def persist_raw_clip(self, day_dir: Path, stem: str, fps: float = 20.0) -> str | None:
        """Tạo clip RAW từ original frames (không overlay, không crop) cho SlowFast.
        Đây là input chính cho SlowFast — full frame, không có bbox/label/FPS/keypoints.
        """
        if not self.original_frame_buffer:
            logger.warning("original_frame_buffer is empty — cannot save raw clip")
            return None
        raw_clip_path = str(day_dir / f"{stem}_raw.mp4")
        result = self._write_clip(raw_clip_path, list(self.original_frame_buffer), fps)
        if result:
            logger.info(
                f"Raw clip saved: {result} | "
                f"frames={len(self.original_frame_buffer)} | "
                f"size={os.path.getsize(result)} bytes"
            )
        return result

    def persist_roi_clip(self, alert: AlertEvent, day_dir: Path, stem: str, fps: float = 20.0) -> str | None:
        """Tạo clip crop ROI từ original frames (không có overlay) cho SlowFast.
        Đây là option nâng cao — crop vùng vi phạm từ raw frames.
        """
        cropped = self._crop_roi_frames(alert.bbox)
        if not cropped:
            logger.info("ROI crop returned empty (no bbox or no original frames) — skipping ROI clip")
            return None
        roi_clip_path = str(day_dir / f"{stem}_roi.mp4")
        result = self._write_clip(roi_clip_path, cropped, fps)
        if result:
            logger.info(
                f"ROI clip saved: {result} | "
                f"frames={len(cropped)} | "
                f"size={os.path.getsize(result)} bytes"
            )
        return result

    def persist_alert(self, alert: AlertEvent, fps: float = 20.0) -> Dict[str, str]:
        day_dir = ensure_dir(self.base_dir / alert.timestamp[:10])
        stem = f"{alert.event_type}_{alert.frame_index}"

        frame_path = str(day_dir / f"{stem}.jpg")
        clip_path = str(day_dir / f"{stem}_rendered.mp4")
        raw_clip_path = str(day_dir / f"{stem}_raw.mp4")
        event_json_path = str(day_dir / f"{stem}.json")
        roi_clip_path = None

        # ── 1. Lưu rendered clip (có bbox/label/FPS) cho dashboard/evidence ──
        if self.frame_buffer:
            cv2.imwrite(frame_path, self.frame_buffer[-1])
            actual_clip = self._write_clip(clip_path, list(self.frame_buffer), fps)
            if actual_clip:
                clip_path = actual_clip
                logger.info(
                    f"Rendered evidence clip: {clip_path} | "
                    f"frames={len(self.frame_buffer)}"
                )

        # ── 2. Lưu raw clip (KHÔNG overlay) — input chính cho SlowFast ──
        actual_raw = self.persist_raw_clip(day_dir, stem, fps)
        if actual_raw:
            raw_clip_path = actual_raw

        # ── 3. Lưu ROI clip (raw crop) — option nâng cao cho SlowFast ──
        roi_clip_path = self.persist_roi_clip(alert, day_dir, stem, fps)

        # ── Log kiểm tra naming convention ──
        logger.info(f"[CLIP PATHS] event={alert.event_type} frame={alert.frame_index}")
        logger.info(f"  rendered (dashboard): {clip_path}")
        logger.info(f"  raw (SlowFast primary): {raw_clip_path}")
        logger.info(f"  roi (SlowFast enhanced): {roi_clip_path or 'N/A'}")
        logger.info(f"  raw_buffer_size={len(self.original_frame_buffer)}")
        logger.info(f"  render_buffer_size={len(self.frame_buffer)}")

        payload = asdict(alert)
        payload.update(
            {
                "frame_path": frame_path,
                "clip_path": clip_path,
                "raw_clip_path": raw_clip_path,
                "roi_clip_path": roi_clip_path,
                "event_json_path": event_json_path,
            }
        )
        with open(event_json_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

        return {
            "frame_path": frame_path,
            "clip_path": clip_path,
            "raw_clip_path": raw_clip_path or "",
            "roi_clip_path": roi_clip_path or "",
            "event_json_path": event_json_path,
        }