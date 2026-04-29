from __future__ import annotations
from typing import Tuple
import cv2

class VideoSource:
    def __init__(self, source: str | int):
        try:
            self.source = int(source)
        except (ValueError, TypeError):
            self.source = source
        self.cap = None

    def open(self) -> None:
        self.cap = cv2.VideoCapture(self.source)
        if not self.cap.isOpened():
            raise RuntimeError(f"Cannot open source: {self.source}")

    def read(self) -> Tuple[bool, any]:
        if self.cap is None:
            raise RuntimeError("Video source is not open")
        return self.cap.read()

    def get_fps(self) -> float:
        if self.cap is None:
            return 0.0
        fps = self.cap.get(cv2.CAP_PROP_FPS)
        return fps if fps and fps > 0 else 20.0

    def get_size(self) -> Tuple[int, int]:
        if self.cap is None:
            return (0, 0)
        width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        return width, height

    def release(self) -> None:
        if self.cap is not None:
            self.cap.release()