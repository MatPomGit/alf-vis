from pathlib import Path

from tracker import SortTracker, bbox_to_z
from tracking_export import TrackingExporter


def main():
    tracker = SortTracker(max_distance=40.0, max_missing=2, min_iou=0.01)
    exporter = TrackingExporter('/mnt/data/test_outputs/tracking_kalman_hungarian.csv')

    frames = [
        [
            {'bbox': [10, 10, 30, 30], 'class_id': 0, 'class_name': 'person', 'confidence': 0.95, 'world_point': None},
            {'bbox': [100, 100, 120, 120], 'class_id': 2, 'class_name': 'car', 'confidence': 0.90, 'world_point': None},
        ],
        [
            {'bbox': [14, 10, 38, 34], 'class_id': 0, 'class_name': 'person', 'confidence': 0.96, 'world_point': None},
            {'bbox': [104, 100, 126, 124], 'class_id': 2, 'class_name': 'car', 'confidence': 0.91, 'world_point': None},
        ],
        [
            {'bbox': [18, 10, 46, 38], 'class_id': 0, 'class_name': 'person', 'confidence': 0.97, 'world_point': None},
            {'bbox': [108, 100, 132, 128], 'class_id': 2, 'class_name': 'car', 'confidence': 0.92, 'world_point': None},
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

    # Ensure the filter is tracking changing bbox size, not only centroid.
    last_person_bbox = collected[2][0][2]
    last_person_state = bbox_to_z(last_person_bbox)
    assert last_person_state[2] > 20.0
    assert last_person_state[3] > 20.0

    assert Path('/mnt/data/test_outputs/tracking_kalman_hungarian.csv').exists()
    print('Tracking test passed. Stable IDs and full bbox state:', collected)


if __name__ == '__main__':
    main()
