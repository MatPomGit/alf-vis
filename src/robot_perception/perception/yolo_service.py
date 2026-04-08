from __future__ import annotations
from typing import List
import numpy as np
from ultralytics import YOLO
from common.models import DetectedObject
class YoloService:
    def __init__(self, model_path: str='yolov8s.pt') -> None:
        self.model = YOLO(model_path)
    def detect(self, frame_bgr: np.ndarray) -> List[DetectedObject]:
        results = self.model.predict(frame_bgr, verbose=False); detections=[]
        if not results: return detections
        result = results[0]; boxes = result.boxes; names = result.names
        if boxes is None: return detections
        xyxy = boxes.xyxy.cpu().numpy(); conf = boxes.conf.cpu().numpy(); cls = boxes.cls.cpu().numpy()
        for i in range(len(xyxy)):
            x1,y1,x2,y2 = xyxy[i].tolist(); class_id = int(cls[i]); label = str(names[class_id]) if class_id in names else str(class_id); cx=(x1+x2)/2.0; cy=(y1+y2)/2.0
            detections.append(DetectedObject(label=label, class_id=class_id, confidence=float(conf[i]), bbox_xyxy=(float(x1),float(y1),float(x2),float(y2)), centroid_xy=(float(cx),float(cy))))
        return detections
    def detect_humans(self, frame_bgr: np.ndarray) -> List[DetectedObject]:
        return [d for d in self.detect(frame_bgr) if d.label == 'person']
    def detect_obstacles(self, frame_bgr: np.ndarray) -> List[DetectedObject]:
        obstacle_labels = {'chair','bench','potted plant','tv','couch','table','bottle','cup','backpack','box','person'}
        return [d for d in self.detect(frame_bgr) if d.label in obstacle_labels]
