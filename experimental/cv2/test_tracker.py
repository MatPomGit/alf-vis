from pathlib import Path

import numpy as np

from tracker import SortTracker, bbox_to_z, extract_appearance_embedding
from tracking_export import TrackingExporter


def test_bbox_state_and_export() -> None:
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

    last_person_bbox = collected[2][0][2]
    last_person_state = bbox_to_z(last_person_bbox)
    assert last_person_state[2] > 20.0
    assert last_person_state[3] > 20.0

    assert Path('/mnt/data/test_outputs/tracking_kalman_hungarian.csv').exists()


def test_appearance_embeddings_reduce_id_switches() -> None:
    tracker = SortTracker(
        max_distance=200.0,
        max_missing=1,
        min_iou=0.0,
        min_appearance_similarity=0.1,
        appearance_weight=0.7,
    )

    frame1 = np.zeros((80, 140, 3), dtype=np.uint8)
    frame2 = np.zeros((80, 140, 3), dtype=np.uint8)

    # BGR colors chosen to create very different HSV histograms.
    frame1[:, 10:40] = (0, 0, 255)
    frame1[:, 80:110] = (255, 0, 0)
    frame2[:, 45:75] = (255, 0, 0)
    frame2[:, 60:90] = (0, 0, 255)

    dets1 = [
        {'bbox': [10, 10, 40, 40], 'class_id': 0, 'class_name': 'person', 'confidence': 0.95, 'world_point': None},
        {'bbox': [80, 10, 110, 40], 'class_id': 0, 'class_name': 'person', 'confidence': 0.94, 'world_point': None},
    ]
    tracked1 = tracker.update(dets1, frame=frame1)
    ids_by_color = {}
    for tracked in tracked1:
        emb = extract_appearance_embedding(frame1, tracked.bbox)
        ids_by_color['red' if emb is not None and emb.argmax() == extract_appearance_embedding(frame1, dets1[0]['bbox']).argmax() else 'blue'] = tracked.track_id

    dets2 = [
        {'bbox': [45, 10, 75, 40], 'class_id': 0, 'class_name': 'person', 'confidence': 0.93, 'world_point': None},
        {'bbox': [60, 10, 90, 40], 'class_id': 0, 'class_name': 'person', 'confidence': 0.92, 'world_point': None},
    ]
    tracked2 = tracker.update(dets2, frame=frame2)

    red_emb = extract_appearance_embedding(frame2, dets2[1]['bbox'])
    blue_emb = extract_appearance_embedding(frame2, dets2[0]['bbox'])

    red_track = min(tracked2, key=lambda t: np.linalg.norm(extract_appearance_embedding(frame2, t.bbox) - red_emb))
    blue_track = min(tracked2, key=lambda t: np.linalg.norm(extract_appearance_embedding(frame2, t.bbox) - blue_emb))

    assert red_track.track_id != blue_track.track_id
    assert {red_track.track_id, blue_track.track_id} == {t.track_id for t in tracked1}


if __name__ == '__main__':
    test_bbox_state_and_export()
    test_appearance_embeddings_reduce_id_switches()
    print('Tracking tests passed. Full bbox state and appearance embeddings are working.')
