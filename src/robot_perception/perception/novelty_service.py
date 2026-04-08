from __future__ import annotations

from typing import List, Set, Tuple

from common.models import DetectedObject, TrackedObject


class NoveltyService:
    """Usługa wykrywania nowych obiektów względem już śledzonych."""

    def detect_new_objects(
        self,
        detections: List[DetectedObject],
        tracked_objects: List[TrackedObject],
        distance_threshold_px: float = 40.0,
    ) -> List[DetectedObject]:
        """Zwraca detekcje, które nie pasują do już śledzonych obiektów."""
        new_objects: List[DetectedObject] = []

        for det in detections:
            matched = False
            for tr in tracked_objects:
                if det.label != tr.label:
                    continue
                dx = det.centroid_xy[0] - tr.centroid_xy[0]
                dy = det.centroid_xy[1] - tr.centroid_xy[1]
                if (dx * dx + dy * dy) ** 0.5 < distance_threshold_px:
                    matched = True
                    break

            if not matched:
                det.is_new = True
                new_objects.append(det)

        return new_objects

    # TODO: dodać lepsze asocjowanie obiektów na podstawie IoU i embeddingów wizualnych.





""" from __future__ import annotations
from common.protocol import read_stdin_json, write_stdout_json, ok_response

def main() -> None:
    payload = read_stdin_json()
    tracked_objects = payload.get("tracked_objects", [])

    existing_labels = {obj["label"] for obj in tracked_objects if "label" in obj}
    candidate = {
        "label": "box",
        "bbox": [220, 180, 80, 60],
        "position": [220.0, 180.0],
        "velocity": [0.0, 0.0],
        "confidence": 0.94,
    }

    new_objects = []
    if candidate["label"] not in existing_labels:
        new_objects.append(candidate)

    write_stdout_json(ok_response(new_objects=new_objects))

if __name__ == "__main__":
    main() """

""" old version
import json
import sys
def main() -> None:
    payload = json.load(sys.stdin)
    tracked_objects = payload.get("tracked_objects", [])

    known_labels = {obj["label"] for obj in tracked_objects if "label" in obj}

    detected = []
    candidate = {
        "label": "box",
        "bbox": [220, 180, 80, 60],
        "position": [220.0, 180.0],
        "velocity": [0.0, 0.0],
        "confidence": 0.93
    }

    if candidate["label"] not in known_labels:
        detected.append(candidate)

    response = {
        "status": "ok",
        "new_objects": detected
    }
    print(json.dumps(response, ensure_ascii=False))
 """