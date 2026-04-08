from __future__ import annotations
from typing import List
from common.models import DetectedObject, TrackedObject
class NoveltyService:
    def detect_new_objects(self, detections: List[DetectedObject], tracked_objects: List[TrackedObject], distance_threshold_px: float=40.0) -> List[DetectedObject]:
        new_objects=[]
        for det in detections:
            matched=False
            for tr in tracked_objects:
                if det.label != tr.label: continue
                dx = det.centroid_xy[0]-tr.centroid_xy[0]; dy = det.centroid_xy[1]-tr.centroid_xy[1]
                if (dx*dx+dy*dy)**0.5 < distance_threshold_px: matched=True; break
            if not matched: det.is_new = True; new_objects.append(det)
        return new_objects
