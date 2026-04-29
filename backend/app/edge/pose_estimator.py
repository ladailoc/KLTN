from __future__ import annotations
from typing import Dict
import cv2
import mediapipe as mp
import numpy as np

from app.common.types import PoseResult


def brighten_for_pose(img_bgr, gamma: float = 1.18):
    if gamma is None or gamma <= 0 or abs(gamma - 1.0) < 1e-6:
        return img_bgr
    inv = 1.0 / gamma
    table = np.array([((i / 255.0) ** inv) * 255 for i in range(256)], dtype=np.uint8)
    return cv2.LUT(img_bgr, table)


class PoseEstimator:
    def __init__(
        self,
        min_detection_confidence: float = 0.45,
        min_tracking_confidence: float = 0.45,
        min_visibility: float = 0.35,
        model_complexity: int = 1,
        gamma: float = 1.18,
        use_brighten: bool = True,
    ):
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=model_complexity,
            enable_segmentation=False,
            smooth_landmarks=True,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )
        self.min_visibility = min_visibility
        self.gamma = gamma
        self.use_brighten = use_brighten

    def predict(self, frame) -> PoseResult:
        h, w = frame.shape[:2]

        work = frame
        if self.use_brighten:
            work = brighten_for_pose(work, self.gamma)

        rgb = cv2.cvtColor(work, cv2.COLOR_BGR2RGB)
        result = self.pose.process(rgb)

        if not result.pose_landmarks:
            return PoseResult(points={})

        lm = result.pose_landmarks.landmark
        idx = self.mp_pose.PoseLandmark

        mapping = {
            "nose": idx.NOSE,
            "left_ear": idx.LEFT_EAR,
            "right_ear": idx.RIGHT_EAR,
            "left_shoulder": idx.LEFT_SHOULDER,
            "right_shoulder": idx.RIGHT_SHOULDER,
            "left_elbow": idx.LEFT_ELBOW,
            "right_elbow": idx.RIGHT_ELBOW,
            "left_wrist": idx.LEFT_WRIST,
            "right_wrist": idx.RIGHT_WRIST,
            "left_hip": idx.LEFT_HIP,
            "right_hip": idx.RIGHT_HIP,
            "mouth_left": idx.MOUTH_LEFT,
            "mouth_right": idx.MOUTH_RIGHT,
        }

        points: Dict[str, tuple[int, int]] = {}
        for name, landmark_idx in mapping.items():
            landmark = lm[landmark_idx.value]
            if landmark.visibility >= self.min_visibility:
                x = int(landmark.x * w)
                y = int(landmark.y * h)
                points[name] = (x, y)

        return PoseResult(points=points)

    def close(self) -> None:
        self.pose.close()