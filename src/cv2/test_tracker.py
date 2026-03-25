from pathlib import Path

from tracker import SortTracker
from tracking_export import TrackingExporter


def main():
    tracker = SortTracker(max_distance=30.0, max_missing=2)
    exporter = TrackingExporter("/mnt/data/test_outputs/tracking_kalman_hungarian.csv")

    frames = [
        [
            {"bbox": [10, 10, 30, 30], "class_id": 0, "class_name": "person", "confidence": 0.95, "world_point": None},
            {"bbox": [100, 100, 120, 120], "class_id": 2, "class_name": "car", "confidence": 0.90, "world_point": None},
        ],
        [
            {"bbox": [14, 10, 34, 30], "class_id": 0, "class_name": "person", "confidence": 0.96, "world_point": None},
            {"bbox": [104, 100, 124, 120], "class_id": 2, "class_name": "car", "confidence": 0.91, "world_point": None},
        ],
        [
            {"bbox": [18, 10, 38, 30], "class_id": 0, "class_name": "person", "confidence": 0.97, "world_point": None},
            {"bbox": [108, 100, 128, 120], "class_id": 2, "class_name": "car", "confidence": 0.92, "world_point": None},
        ],
    ]

    collected = []
    for frame_idx, detections in enumerate(frames):
        tracked = tracker.update(detections)
        collected.append([(t.track_id, t.class_name, t.bbox.tolist()) for t in tracked])
        for t in tracked:
            exporter.write(frame_idx, t.track_id, t.class_id, t.class_name, t.confidence, t.bbox, t.world_point)

    exporter.close()

    assert collected[0][0][0] == collected[1][0][0] == collected[2][0][0]
    assert collected[0][1][0] == collected[1][1][0] == collected[2][1][0]
    assert Path("/mnt/data/test_outputs/tracking_kalman_hungarian.csv").exists()
    print("Tracking test passed. Stable IDs:", collected)


if __name__ == "__main__":
    main()
