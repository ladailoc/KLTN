from __future__ import annotations
import time
from collections import deque
from pathlib import Path
import json
import psutil
import cv2
from app.common.config import load_config
from app.common.logger import get_logger
from app.common.utils import ensure_dir, now_iso
from app.common.types import PoseResult
from app.edge.alert_manager import AlertManager
from app.edge.behavior_rules import BehaviorRules
from app.edge.edge_api_client import EdgeApiClient
from app.edge.evidence_writer import EvidenceWriter
from app.edge.overlay_renderer import OverlayRenderer
from app.edge.pose_estimator import PoseEstimator
from app.edge.video_source import VideoSource
from app.edge.yolo_detector import YoloDetector

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
        recent_alerts = deque(maxlen=4)
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
                ok, frame = video.read()
                if not ok:
                    break

                frame_index += 1
                t0 = time.time()

                frame = self._resize_frame_if_needed(frame)
                self.evidence_writer.push_frame(frame)

                if frame_index % detect_every == 1 or not last_detections:
                    detections = self.detector.predict(frame, imgsz=self.cfg["edge"].get("resize_width", 640))
                    last_detections = detections
                else:
                    detections = last_detections

                pose = self._get_pose_for_frame(frame, frame_index, detections)

                candidates = self.rules.infer(detections, pose, frame.shape)

                alerts = self.alert_manager.update(
                    candidates=candidates,
                    frame_index=frame_index,
                    timestamp_iso=now_iso(),
                    current_time_sec=time.time(),
                    source_device=self.cfg["edge"]["source_device"],
                )

                for alert in alerts:
                    total_alert_count += 1
                    saved = self.evidence_writer.persist_alert(alert, fps=src_fps)
                    self.logger.info(
                        f"ALERT fired: {alert.event_type} | frame={alert.frame_index} | saved={saved}"
                    )
                    recent_alerts.appendleft(alert)

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

                fps_now = 1.0 / max(time.time() - t0, 1e-6)
                if fps_smooth is None:
                    fps_smooth = fps_now
                else:
                    fps_smooth = 0.9 * fps_smooth + 0.1 * fps_now

                fps_values.append(fps_now)

                if frame_index % 10 == 0:
                    cpu_values.append(psutil.cpu_percent(interval=None))
                    ram_values.append(process.memory_info().rss / (1024 * 1024))    

                rendered = self.renderer.draw(frame, detections, pose, recent_alerts, fps_smooth)

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