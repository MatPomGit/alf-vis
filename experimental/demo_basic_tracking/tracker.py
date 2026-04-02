
import numpy as np

def iou(bbox1, bbox2):
    x1 = max(bbox1[0], bbox2[0])
    y1 = max(bbox1[1], bbox2[1])
    x2 = min(bbox1[2], bbox2[2])
    y2 = min(bbox1[3], bbox2[3])

    inter = max(0, x2 - x1) * max(0, y2 - y1)
    area1 = (bbox1[2] - bbox1[0]) * (bbox1[3] - bbox1[1])
    area2 = (bbox2[2] - bbox2[0]) * (bbox2[3] - bbox2[1])

    union = area1 + area2 - inter
    return inter / union if union > 0 else 0


def linear_assignment(tracks, detections, iou_threshold):
    matches = []
    unmatched_tracks = list(range(len(tracks)))
    unmatched_dets = list(range(len(detections)))

    for t_idx, t in enumerate(tracks):
        best_iou = 0
        best_d = -1
        for d_idx, d in enumerate(detections):
            score = iou(t.bbox, d["bbox"])
            if score > best_iou:
                best_iou = score
                best_d = d_idx

        if best_iou >= iou_threshold:
            matches.append((t_idx, best_d))
            if t_idx in unmatched_tracks:
                unmatched_tracks.remove(t_idx)
            if best_d in unmatched_dets:
                unmatched_dets.remove(best_d)

    return matches, unmatched_tracks, unmatched_dets


class Track:
    def __init__(self, bbox, track_id):
        self.bbox = bbox
        self.id = track_id
        self.lost = 0

    def update(self, det):
        self.bbox = det["bbox"]
        self.lost = 0

    def mark_lost(self):
        self.lost += 1


class ByteTracker:
    def __init__(self):
        self.tracks = []
        self.next_id = 0

        self.high_thresh = 0.5
        self.low_thresh = 0.1

    def update(self, detections):
        high_dets = [d for d in detections if d["score"] >= self.high_thresh]
        low_dets = [d for d in detections if self.low_thresh <= d["score"] < self.high_thresh]

        # First association
        matches, unmatched_tracks, unmatched_dets = linear_assignment(
            self.tracks, high_dets, iou_threshold=0.3
        )

        for t_idx, d_idx in matches:
            self.tracks[t_idx].update(high_dets[d_idx])

        # Second association
        if len(unmatched_tracks) > 0 and len(low_dets) > 0:
            sub_tracks = [self.tracks[i] for i in unmatched_tracks]

            second_matches, still_unmatched, _ = linear_assignment(
                sub_tracks, low_dets, iou_threshold=0.5
            )

            for t_idx, d_idx in second_matches:
                real_t = unmatched_tracks[t_idx]
                self.tracks[real_t].update(low_dets[d_idx])

            unmatched_tracks = [unmatched_tracks[i] for i in still_unmatched]

        # Mark lost
        for i in unmatched_tracks:
            self.tracks[i].mark_lost()

        # Create new tracks ONLY from high confidence detections
        for d_idx in unmatched_dets:
            det = high_dets[d_idx]
            self.tracks.append(Track(det["bbox"], self.next_id))
            self.next_id += 1

        # Remove long-lost tracks
        self.tracks = [t for t in self.tracks if t.lost < 30]

        return self.tracks
