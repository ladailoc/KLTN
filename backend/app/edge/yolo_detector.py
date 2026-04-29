from __future__ import annotations
from typing import List
from ultralytics import YOLO

from app.common.types import Detection

class YoloDetector:
    def __init__(self, model_path: str, conf: float = 0.35, iou: float = 0.45):
        self.model = YOLO(model_path)
        self.conf = conf
        self.iou = iou

    def predict(self, frame, imgsz: int = 640) -> List[Detection]:
        # Using imgsz to avoid resizing internally if frame is big;
        # half=True requires GPU typically, skipped for universal compatibility
        results = self.model(frame, conf=self.conf, iou=self.iou, imgsz=imgsz, verbose=False)[0]
        names = results.names
        detections: List[Detection] = []

        if results.boxes is None or len(results.boxes) == 0:
            return detections

        xyxy = results.boxes.xyxy.cpu().numpy()
        confs = results.boxes.conf.cpu().numpy()
        clss = results.boxes.cls.cpu().numpy()

        for box, conf, cls_id in zip(xyxy, confs, clss):
            x1, y1, x2, y2 = [int(v) for v in box.tolist()]
            class_id = int(cls_id)
            class_name = names[class_id]
            detections.append(
                Detection(
                    class_id=class_id,
                    class_name=str(class_name).strip().lower(),
                    confidence=float(conf),
                    bbox=(x1, y1, x2, y2),
                )
            )
        return detections