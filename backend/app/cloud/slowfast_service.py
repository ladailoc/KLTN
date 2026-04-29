from __future__ import annotations

import json
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

import cv2
import numpy as np
import torch

from app.common.config import load_config
from app.common.logger import get_logger
from app.common.utils import ensure_dir


KINETICS_LABELS_URL = "https://dl.fbaipublicfiles.com/pyslowfast/dataset/class_names/kinetics_classnames.json"


class SlowFastService:
    """
    Cloud verification service dùng SlowFast pretrained.

    Lưu ý:
    - Không dùng pytorchvideo.transforms để tránh lỗi tương thích torchvision.
    - Video được đọc bằng OpenCV.
    - Transform được tự xử lý bằng numpy + torch.
    """

    def __init__(self):
        self.cfg = load_config()
        self.log = get_logger("slowfast_service", self.cfg["storage"]["logs_dir"])
        self.sf_cfg = self.cfg["slowfast"]

        self.device = self._resolve_device(self.sf_cfg.get("device", "auto"))
        self.model = None
        self.id_to_label: Dict[int, str] = {}

    def _resolve_device(self, device_cfg: str) -> str:
        if device_cfg == "auto":
            return "cuda" if torch.cuda.is_available() else "cpu"
        return device_cfg

    def _ensure_loaded(self) -> None:
        if self.model is not None and self.id_to_label:
            return

        model_name = self.sf_cfg.get("model_name", "slowfast_r50")
        pretrained = bool(self.sf_cfg.get("pretrained", True))

        self.log.info(
            f"Loading SlowFast model={model_name}, pretrained={pretrained}, device={self.device}"
        )

        self.model = torch.hub.load(
            "facebookresearch/pytorchvideo:main",
            model=model_name,
            pretrained=pretrained,
        )

        self.model = self.model.eval().to(self.device)
        self.id_to_label = self._load_kinetics_labels()

    def _load_kinetics_labels(self) -> Dict[int, str]:
        cache_path = Path(
            self.sf_cfg.get("labels_cache_path", "models/kinetics_classnames.json")
        )
        ensure_dir(cache_path.parent)

        if not cache_path.exists():
            try:
                self.log.info(f"Downloading Kinetics labels to {cache_path}")
                urllib.request.urlretrieve(KINETICS_LABELS_URL, str(cache_path))
            except Exception as e:
                self.log.error(f"Could not download Kinetics labels: {e}")
                return {i: f"class_{i}" for i in range(400)}

        with open(cache_path, "r", encoding="utf-8") as f:
            raw = json.load(f)

        id_to_label: Dict[int, str] = {}
        for class_name, class_id in raw.items():
            id_to_label[int(class_id)] = str(class_name).replace('"', "")

        return id_to_label

    def _read_video_frames(
        self,
        video_path: str,
        start_sec: float,
        end_sec: float,
        num_frames: int,
    ) -> List[np.ndarray]:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS)
        if not fps or fps <= 0:
            fps = float(self.sf_cfg.get("frames_per_second", 30))

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames <= 0:
            cap.release()
            raise ValueError(f"Video has no frames: {video_path}")

        start_frame = max(0, int(start_sec * fps))
        end_frame = min(total_frames - 1, int(end_sec * fps))

        if end_frame <= start_frame:
            end_frame = min(total_frames - 1, start_frame + num_frames)

        indices = np.linspace(start_frame, end_frame, num=num_frames).astype(int)

        frames: List[np.ndarray] = []
        last_good_frame = None

        for idx in indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(idx))
            ok, frame_bgr = cap.read()

            if not ok or frame_bgr is None:
                if last_good_frame is not None:
                    frames.append(last_good_frame.copy())
                continue

            frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            last_good_frame = frame_rgb
            frames.append(frame_rgb)

        cap.release()

        if not frames:
            raise ValueError(f"Could not decode frames from video: {video_path}")

        while len(frames) < num_frames:
            frames.append(frames[-1].copy())

        return frames[:num_frames]

    def _resize_short_side(self, frame: np.ndarray, size: int) -> np.ndarray:
        h, w = frame.shape[:2]

        if h < w:
            new_h = size
            new_w = int(w * size / h)
        else:
            new_w = size
            new_h = int(h * size / w)

        return cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)

    def _center_crop(self, frame: np.ndarray, crop_size: int) -> np.ndarray:
        h, w = frame.shape[:2]

        if h < crop_size or w < crop_size:
            pad_h = max(0, crop_size - h)
            pad_w = max(0, crop_size - w)
            frame = cv2.copyMakeBorder(
                frame,
                pad_h // 2,
                pad_h - pad_h // 2,
                pad_w // 2,
                pad_w - pad_w // 2,
                cv2.BORDER_CONSTANT,
                value=(0, 0, 0),
            )
            h, w = frame.shape[:2]

        y1 = max(0, (h - crop_size) // 2)
        x1 = max(0, (w - crop_size) // 2)

        return frame[y1 : y1 + crop_size, x1 : x1 + crop_size]

    def _preprocess_frames(self, frames: List[np.ndarray]) -> List[torch.Tensor]:
        side_size = int(self.sf_cfg.get("side_size", 256))
        crop_size = int(self.sf_cfg.get("crop_size", 256))
        alpha = int(self.sf_cfg.get("alpha", 4))

        processed = []

        for frame in frames:
            frame = self._resize_short_side(frame, side_size)
            frame = self._center_crop(frame, crop_size)
            processed.append(frame)

        # Shape: T, H, W, C
        arr = np.stack(processed).astype(np.float32) / 255.0

        # Shape: C, T, H, W
        tensor = torch.from_numpy(arr).permute(3, 0, 1, 2)

        mean = torch.tensor([0.45, 0.45, 0.45]).view(3, 1, 1, 1)
        std = torch.tensor([0.225, 0.225, 0.225]).view(3, 1, 1, 1)

        tensor = (tensor - mean) / std

        fast_pathway = tensor
        t = tensor.shape[1]

        slow_count = max(1, t // alpha)
        slow_indices = torch.linspace(0, t - 1, slow_count).long()
        slow_pathway = torch.index_select(tensor, dim=1, index=slow_indices)

        # SlowFast expects:
        # [
        #   slow pathway: B, C, T_slow, H, W
        #   fast pathway: B, C, T_fast, H, W
        # ]
        inputs = [
            slow_pathway.unsqueeze(0).to(self.device),
            fast_pathway.unsqueeze(0).to(self.device),
        ]

        return inputs

    def _project_mapping_score(
        self,
        labels: List[str],
        scores: List[float],
        event_type_hint: Optional[str],
    ) -> Dict[str, Any]:
        project_scores = {
            "using_phone": 0.0,
            "smoking": 0.0,
            "no_seatbelt": 0.0,
        }

        phone_keywords = [
            "phone",
            "cell phone",
            "telephone",
            "texting",
            "talking",
            "calling",
        ]

        smoking_keywords = [
            "smoking",
            "cigarette",
            "vaping",
            "vape",
            "hookah",
        ]

        # Kinetics pretrained không chuyên cho seatbelt,
        # nên no_seatbelt chỉ là weak signal.
        no_seatbelt_keywords = [
            "driving",
            "sitting",
            "riding",
        ]

        for label, score in zip(labels, scores):
            lab = label.lower()

            if any(k in lab for k in phone_keywords):
                project_scores["using_phone"] = max(
                    project_scores["using_phone"], float(score)
                )

            if any(k in lab for k in smoking_keywords):
                project_scores["smoking"] = max(
                    project_scores["smoking"], float(score)
                )

            if any(k in lab for k in no_seatbelt_keywords):
                project_scores["no_seatbelt"] = max(
                    project_scores["no_seatbelt"], float(score) * 0.25
                )

        if event_type_hint in project_scores:
            chosen_event = event_type_hint
            chosen_score = project_scores[event_type_hint]
        else:
            chosen_event, chosen_score = max(project_scores.items(), key=lambda x: x[1])

        min_score = float(self.sf_cfg.get("min_project_score", 0.20))

        verified = chosen_score >= min_score

        verification_status = "verified" if verified else "unconfirmed"

        return {
            "project_scores": {k: round(v, 4) for k, v in project_scores.items()},
            "predicted_project_event": chosen_event,
            "predicted_project_score": round(chosen_score, 4),
            "verified": bool(verified),
            "note": (
                "Heuristic mapping from Kinetics labels to project events. "
                "This is baseline Cloud verification, not fine-tuned driver behavior recognition."
            ),
            "verification_status": verification_status,
        }

    def verify_clip(
        self,
        video_path: str,
        start_sec: float = 0.0,
        end_sec: Optional[float] = None,
        event_type_hint: Optional[str] = None,
    ) -> Dict[str, Any]:
        self._ensure_loaded()

        num_frames = int(self.sf_cfg.get("num_frames", 32))
        sampling_rate = int(self.sf_cfg.get("sampling_rate", 2))
        frames_per_second = int(self.sf_cfg.get("frames_per_second", 30))
        top_k = int(self.sf_cfg.get("top_k", 5))

        if end_sec is None:
            clip_duration = (num_frames * sampling_rate) / frames_per_second
            end_sec = start_sec + clip_duration

        frames = self._read_video_frames(
            video_path=video_path,
            start_sec=start_sec,
            end_sec=end_sec,
            num_frames=num_frames,
        )

        inputs = self._preprocess_frames(frames)

        with torch.no_grad():
            preds = self.model(inputs)
            probs = torch.nn.functional.softmax(preds, dim=1)
            top = probs.topk(k=top_k)

        top_indices = top.indices[0].detach().cpu().tolist()
        top_scores = top.values[0].detach().cpu().tolist()
        top_labels = [
            self.id_to_label.get(int(i), f"class_{i}") for i in top_indices
        ]

        mapped = self._project_mapping_score(
            labels=top_labels,
            scores=top_scores,
            event_type_hint=event_type_hint,
        )

        return {
            "video_path": video_path,
            "start_sec": start_sec,
            "end_sec": end_sec,
            "device": self.device,
            "model_name": self.sf_cfg.get("model_name", "slowfast_r50"),
            "top_k": [
                {
                    "label": label,
                    "score": round(float(score), 4),
                }
                for label, score in zip(top_labels, top_scores)
            ],
            **mapped,
        }


_slowfast_service_singleton: Optional[SlowFastService] = None


def get_slowfast_service() -> SlowFastService:
    global _slowfast_service_singleton

    if _slowfast_service_singleton is None:
        _slowfast_service_singleton = SlowFastService()

    return _slowfast_service_singleton