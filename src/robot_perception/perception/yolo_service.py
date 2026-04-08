from __future__ import annotations

from typing import List

import numpy as np
from ultralytics import YOLO

from common.models import DetectedObject


class YoloService:
    """Usługa detekcji obiektów oparta o model YOLOv8s."""

    def __init__(self, model_path: str = "yolov8s.pt") -> None:
        self.model = YOLO(model_path)

    def detect(self, frame_bgr: np.ndarray) -> List[DetectedObject]:
        """Uruchamia inferencję YOLOv8s na podanej ramce obrazu."""
        results = self.model.predict(frame_bgr, verbose=False)
        detections: List[DetectedObject] = []

        if not results:
            return detections

        result = results[0]
        names = result.names
        boxes = result.boxes

        if boxes is None:
            return detections

        xyxy = boxes.xyxy.cpu().numpy()
        conf = boxes.conf.cpu().numpy()
        cls = boxes.cls.cpu().numpy()

        for i in range(len(xyxy)):
            x1, y1, x2, y2 = xyxy[i].tolist()
            class_id = int(cls[i])
            label = str(names[class_id]) if class_id in names else str(class_id)
            cx = (x1 + x2) / 2.0
            cy = (y1 + y2) / 2.0

            detections.append(
                DetectedObject(
                    label=label,
                    class_id=class_id,
                    confidence=float(conf[i]),
                    bbox_xyxy=(float(x1), float(y1), float(x2), float(y2)),
                    centroid_xy=(float(cx), float(cy)),
                )
            )

        return detections

    def detect_humans(self, frame_bgr: np.ndarray) -> List[DetectedObject]:
        """Wydziela z ogólnych detekcji tylko ludzi."""
        return [d for d in self.detect(frame_bgr) if d.label == "person"]

    def detect_obstacles(self, frame_bgr: np.ndarray) -> List[DetectedObject]:
        """Filtruje obiekty, które mogą być traktowane jako przeszkody."""
        obstacle_labels = {
            "chair", "bench", "potted plant", "tv", "couch", "table", "bottle",
            "cup", "backpack", "box"
        }
        return [d for d in self.detect(frame_bgr) if d.label in obstacle_labels or d.label == "person"]

    # TODO: dodać wersję detekcji na ROI oraz śledzenie z natywnym trackerem YOLO, jeśli będzie potrzebne.