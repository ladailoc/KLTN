from __future__ import annotations
import time
from pathlib import Path
from typing import Dict, List
import json
import psutil
import cv2
from app.common.config import load_config
from app.common.logger import get_logger
from app.common.utils import ensure_dir, now_iso
from app.common.types import Detection, PoseResult
from app.edge.alert_manager import AlertManager
from app.edge.behavior_rules import BehaviorRules
from app.edge.edge_api_client import EdgeApiClient
from app.edge.evidence_writer import EvidenceWriter
from app.edge.overlay_renderer import OverlayRenderer
from app.edge.pose_estimator import PoseEstimator
from app.edge.video_source import VideoSource
from app.edge.yolo_detector import YoloDetector
from app.edge.upload_queue import UploadQueue

# ── Frame-based bbox/alert hold constants ─────────────────────────
BBOX_HOLD_FRAMES = 2              # Giữ bbox tối đa 2 frame sau khi mất detection
SMOKE_DEBOUNCE_FRAMES = 2         # Cần thấy smoking >= 2 frame liên tục mới hiện bbox

# Alert text hold — MỖI CLASS có TTL riêng (rất khác bbox)
ALERT_HOLD_FRAMES: dict = {
    "smoking": 45,                # ~2.2 giây @ 20 FPS
    "no_seatbelt": 60,            # ~3 giây @ 20 FPS (trạng thái liên tục, giữ lâu hơn)
    "using_phone": 45,            # ~2.2 giây @ 20 FPS
}
ALERT_HOLD_FRAMES_DEFAULT = 45    # fallback nếu event_type lạ

class EdgePipeline:
    def __init__(self, config_path: str = "config.yaml"):
        self.cfg = load_config(config_path)
        self.logger = get_logger("edge_pipeline", self.cfg["storage"]["logs_dir"])

        self.detector = YoloDetector(
            model_path=self.cfg["models"]["yolo_path"],
            conf=self.cfg["edge"]["conf_threshold"],
            iou=self.cfg["edge"]["iou_threshold"],
        )

        self.pose_estimator = None
        if self.cfg["pose"]["enabled"]:
            self.pose_estimator = PoseEstimator(
                min_detection_confidence=self.cfg["pose"]["min_detection_confidence"],
                min_tracking_confidence=self.cfg["pose"]["min_tracking_confidence"],
                min_visibility=self.cfg["pose"].get("min_visibility", 0.35),
                model_complexity=self.cfg["pose"].get("model_complexity", 1),
                gamma=self.cfg["pose"].get("gamma", 1.18),
                use_brighten=self.cfg["pose"].get("use_brighten", True),
            )

        self.rules = BehaviorRules(self.cfg)
        self.alert_manager = AlertManager(self.cfg)
        self.evidence_writer = EvidenceWriter(
            alerts_dir=self.cfg["storage"]["alerts_dir"],
            buffer_size=self.cfg["edge"]["buffer_size"],
        )
        self.renderer = OverlayRenderer()
        self.api_client = EdgeApiClient(
            server_url=self.cfg["edge"]["server_url"],
            timeout_sec=self.cfg["cloud"]["upload_timeout_sec"],
            verify_timeout_sec=self.cfg["edge"].get("verify_timeout_sec", 120),
        )

        queue_path = str(Path(self.cfg["storage"]["alerts_dir"]) / "upload_queue.json")
        self.upload_queue = UploadQueue(
            queue_path=queue_path,
            api_client=self.api_client,
            edge_logger=self.logger,
        )

        self.last_pose = PoseResult(points={})

    def _resize_frame_if_needed(self, frame):
        resize_width = self.cfg["edge"].get("resize_width", None)
        if resize_width is None or resize_width <= 0:
            return frame

        h, w = frame.shape[:2]
        if w <= resize_width:
            return frame

        scale = resize_width / float(w)
        new_h = int(h * scale)
        return cv2.resize(frame, (resize_width, new_h))

    def _has_relevant_detection(self, detections) -> bool:
        relevant_names = {
            "phone",
            "smoking",
            "seatbelt",
            "no-seatbelt",
            "no_seatbelt",
            "no seatbelt",
        }
        return any(str(d.class_name).lower().strip() in relevant_names for d in detections)

    def _get_pose_for_frame(self, frame, frame_index: int, detections):
        if not self.pose_estimator:
            return PoseResult(points={})

        # Chỉ chạy pose khi có detection liên quan
        if not self._has_relevant_detection(detections):
            return self.last_pose

        pose_every = max(1, int(self.cfg["edge"].get("pose_every_n_frames", 3)))

        # Chỉ chạy pose mỗi N frame
        if frame_index % pose_every == 0 or not self.last_pose.points:
            self.last_pose = self.pose_estimator.predict(frame)

        return self.last_pose

    # ── Frame-based bbox cache ────────────────────────────────────────

    def _update_bbox_cache(self, detections: List[Detection], frame_index: int) -> None:
        """Cập nhật bbox_cache từ detections hiện tại.
        Match theo class_name + IoU để cập nhật entry cũ, thêm entry mới nếu không match.
        """
        matched_indices: set = set()

        # Cập nhật entry có sẵn trong cache
        for cache_key, entry in self.bbox_cache.items():
            best_match = None
            best_iou = 0.0
            best_idx = -1

            for i, det in enumerate(detections):
                if i in matched_indices:
                    continue
                if det.class_name != entry["class_name"]:
                    continue
                iou_val = self._iou(entry["bbox"], det.bbox)
                if iou_val > best_iou:
                    best_iou = iou_val
                    best_match = det
                    best_idx = i

            if best_match is not None and best_iou > 0.3:
                self.bbox_cache[cache_key] = {
                    "class_name": best_match.class_name,
                    "bbox": best_match.bbox,
                    "confidence": best_match.confidence,
                    "last_seen_frame": frame_index,
                }
                matched_indices.add(best_idx)

        # Xóa entry cũ (quá hạn BBOX_HOLD_FRAMES)
        expired_keys = [
            k for k, v in self.bbox_cache.items()
            if frame_index - v["last_seen_frame"] > BBOX_HOLD_FRAMES
        ]
        for k in expired_keys:
            del self.bbox_cache[k]

        # Thêm detection mới (chưa match) vào cache
        for i, det in enumerate(detections):
            if i not in matched_indices:
                new_key = f"{det.class_name}_{frame_index}_{i}"
                self.bbox_cache[new_key] = {
                    "class_name": det.class_name,
                    "bbox": det.bbox,
                    "confidence": det.confidence,
                    "last_seen_frame": frame_index,
                }

    def _update_active_alerts(self, alerts, frame_index: int) -> None:
        """Cập nhật active_alerts: giữ 1 alert per event_type.
        Mỗi class có TTL riêng (ALERT_HOLD_FRAMES dict).
        """
        for alert in alerts:
            self.active_alerts[alert.event_type] = {
                "alert": alert,
                "last_seen_frame": frame_index,
            }

        # Xóa alert cũ — TTL per class
        expired_types = [
            etype for etype, entry in self.active_alerts.items()
            if frame_index - entry["last_seen_frame"] > ALERT_HOLD_FRAMES.get(etype, ALERT_HOLD_FRAMES_DEFAULT)
        ]
        for etype in expired_types:
            del self.active_alerts[etype]

    def _get_detections_for_render(self, frame_index: int) -> List[Detection]:
        """Lấy danh sách detection để render từ bbox_cache.
        Chỉ trả về entry còn hạn (trong BBOX_HOLD_FRAMES).
        Áp dụng debounce cho smoking: cần >= SMOKE_DEBOUNCE_FRAMES frame liên tục.
        """
        result: List[Detection] = []
        smoking_in_frame = False

        for entry in self.bbox_cache.values():
            if frame_index - entry["last_seen_frame"] > BBOX_HOLD_FRAMES:
                continue

            # Smoking debounce: đếm số frame liên tục có smoking
            if entry["class_name"] == "smoking":
                smoking_in_frame = True

            result.append(Detection(
                class_id=0,
                class_name=entry["class_name"],
                confidence=entry["confidence"],
                bbox=entry["bbox"],
            ))

        # Cập nhật smoking debounce counter
        if smoking_in_frame:
            self.smoking_frame_count += 1
        else:
            self.smoking_frame_count = 0

        # Lọc smoking: chỉ hiện bbox nếu đủ frame liên tục
        if self.smoking_frame_count < SMOKE_DEBOUNCE_FRAMES:
            result = [d for d in result if d.class_name != "smoking"]

        return result

    @staticmethod
    def _iou(a, b) -> float:
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

    def run(self, source_override: str | None = None, send_to_cloud_override: bool | None = None) -> None:
        source = source_override or self.cfg["edge"]["source"]
        send_to_cloud = (
            self.cfg["edge"]["send_to_cloud"]
            if send_to_cloud_override is None
            else send_to_cloud_override
        )
        show_window = self.cfg["edge"]["show_window"]

        video = VideoSource(source)
        video.open()
        src_fps = video.get_fps()
        width, height = video.get_size()

        resize_width = self.cfg["edge"].get("resize_width", None)
        if resize_width is not None and resize_width > 0 and width > resize_width:
            scale = resize_width / float(width)
            width = resize_width
            height = int(height * scale)

        writer = None
        if self.cfg["edge"]["save_video"]:
            output_path = Path(self.cfg["edge"]["output_video_path"])
            ensure_dir(output_path.parent)
            writer = cv2.VideoWriter(
                str(output_path),
                cv2.VideoWriter_fourcc(*"mp4v"),
                src_fps if src_fps > 0 else 20.0,
                (width, height),
            )

        frame_index = 0
        self.bbox_cache: Dict[str, dict] = {}      # frame-based bbox cache
        self.active_alerts: Dict[str, dict] = {}    # frame-based alert cache
        self.smoking_frame_count = 0                 # smoking debounce counter
        fps_smooth = None

        fps_values = []
        cpu_values = []
        ram_values = []
        total_alert_count = 0
        start_run_time = time.time()
        process = psutil.Process()

        detect_every = max(1, int(self.cfg["edge"].get("detect_every_n_frames", 2)))
        last_detections = []

        self.logger.info("Starting edge pipeline...")

        try:
            while True:
                try:
                    ok, frame = video.read()
                except SystemError:
                    # OpenCV đôi khi throw SystemError ở frame cuối khi hết bộ nhớ
                    self.logger.warning("Video read SystemError — assuming end of stream")
                    break
                if not ok:
                    break

                frame_index += 1
                t0 = time.time()

                frame = self._resize_frame_if_needed(frame)

                if detect_every <= 1 or frame_index % detect_every == 1 or not last_detections:
                    detections = self.detector.predict(frame, imgsz=self.cfg["edge"].get("resize_width", 640))
                    last_detections = detections
                else:
                    detections = last_detections

                # Cập nhật bbox_cache theo frame (không dùng time.time())
                self._update_bbox_cache(detections, frame_index)

                pose = self._get_pose_for_frame(frame, frame_index, detections)

                candidates = self.rules.infer(detections, pose, frame.shape)

                alerts = self.alert_manager.update(
                    candidates=candidates,
                    frame_index=frame_index,
                    timestamp_iso=now_iso(),
                    current_time_sec=time.time(),
                    source_device=self.cfg["edge"]["source_device"],
                )

                # Cập nhật active_alerts theo frame
                self._update_active_alerts(alerts, frame_index)
                for alert in alerts:
                    total_alert_count += 1

                # Flush upload queue — retry các alert chưa upload được trước đó
                if send_to_cloud:
                    verify_on_cloud = self.cfg["edge"].get("verify_on_cloud", False)
                    self.upload_queue.flush(verify=verify_on_cloud)

                # Lưu frame GỐC (không overlay) cho SlowFast verification
                self.evidence_writer.push_original_frame(frame)

                # Lấy detections từ cache (đã lọc theo frame + smoking debounce)
                render_detections = self._get_detections_for_render(frame_index)

                # Render frame với overlay (bbox khoanh vùng vi phạm)
                rendered = self.renderer.draw(
                    frame, render_detections, pose,
                    self.active_alerts, fps_smooth, frame_index,
                )

                # Đẩy frame ĐÃ RENDER vào evidence buffer (có khoanh vùng)
                self.evidence_writer.push_frame(rendered)

                # Lưu bằng chứng & upload lên cloud
                for alert in alerts:
                    saved = self.evidence_writer.persist_alert(alert, fps=src_fps)
                    self.logger.info(
                        f"ALERT fired: {alert.event_type} | frame={alert.frame_index} | saved={saved}"
                    )

                    # ── Diagnostic log: xác nhận frame separation ──
                    self.logger.info(
                        f"[FRAME FLOW] "
                        f"raw_buffer={len(self.evidence_writer.original_frame_buffer)} | "
                        f"render_buffer={len(self.evidence_writer.frame_buffer)} | "
                        f"slowfast_input={saved.get('raw_clip_path', 'N/A')} | "
                        f"roi_clip={saved.get('roi_clip_path', 'N/A')} | "
                        f"evidence_clip={saved.get('clip_path', 'N/A')}"
                    )

                    if send_to_cloud:
                        try:
                            verify_on_cloud = self.cfg["edge"].get("verify_on_cloud", False)

                            cloud_result = self.api_client.send_alert_and_verify(
                                alert=alert,
                                saved_paths=saved,
                                verify=verify_on_cloud,
                            )

                            create_result = cloud_result.get("create_result")
                            verify_result = cloud_result.get("verify_result")

                            self.logger.info(f"Cloud upload success: {create_result}")

                            if verify_result is not None:
                                self.logger.info(f"SlowFast verify result: {verify_result}")

                        except Exception as e:
                            self.logger.error(f"Cloud upload/verify failed: {e}")
                            # Thêm vào hàng đợi để retry khi có mạng
                            self.upload_queue.enqueue(
                                alert_dict={
                                    "event_type": alert.event_type,
                                    "confidence": alert.confidence,
                                    "frame_index": alert.frame_index,
                                    "timestamp": alert.timestamp,
                                    "source_device": alert.source_device,
                                    "note": alert.note,
                                },
                                saved_paths=saved,
                                error=str(e),
                            )

                # Giải phóng buffer sau khi đã persist & upload xong — tránh OOM
                if alerts:
                    self.evidence_writer.clear_buffers()

                fps_now = 1.0 / max(time.time() - t0, 1e-6)
                if fps_smooth is None:
                    fps_smooth = fps_now
                else:
                    fps_smooth = 0.9 * fps_smooth + 0.1 * fps_now

                fps_values.append(fps_now)

                if frame_index % 10 == 0:
                    cpu_values.append(psutil.cpu_percent(interval=None))
                    ram_values.append(process.memory_info().rss / (1024 * 1024))

                if writer is not None:
                    writer.write(rendered)

                if show_window:
                    cv2.imshow("Driver Behavior Hybrid - Edge", rendered)
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord("q"):
                        break

        finally:
            if writer is not None:
                writer.release()

            video.release()

            if self.pose_estimator:
                self.pose_estimator.close()

            cv2.destroyAllWindows()

            total_time = time.time() - start_run_time

            benchmark_result = {
                "source": str(source),
                "total_frames": frame_index,
                "total_time_sec": round(total_time, 3),
                "avg_fps": round(sum(fps_values) / len(fps_values), 3) if fps_values else 0,
                "min_fps": round(min(fps_values), 3) if fps_values else 0,
                "max_fps": round(max(fps_values), 3) if fps_values else 0,
                "avg_cpu_percent": round(sum(cpu_values) / len(cpu_values), 3) if cpu_values else 0,
                "avg_ram_mb": round(sum(ram_values) / len(ram_values), 3) if ram_values else 0,
                "total_alerts": total_alert_count,
                "save_video": self.cfg["edge"].get("save_video"),
                "send_to_cloud": send_to_cloud,
                "verify_on_cloud": self.cfg["edge"].get("verify_on_cloud", False),
                "resize_width": self.cfg["edge"].get("resize_width"),
                "pose_every_n_frames": self.cfg["edge"].get("pose_every_n_frames"),
            }

            benchmark_dir = ensure_dir("outputs/benchmarks")
            benchmark_path = benchmark_dir / f"edge_runtime_benchmark_{int(time.time())}.json"

            with open(benchmark_path, "w", encoding="utf-8") as f:
                json.dump(benchmark_result, f, ensure_ascii=False, indent=2)

            self.logger.info(f"Edge benchmark result: {benchmark_result}")
            self.logger.info(f"Benchmark saved to: {benchmark_path}")
            self.logger.info("Edge pipeline stopped.")