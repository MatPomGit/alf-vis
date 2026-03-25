from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np


BBox = Sequence[float]


def bbox_to_z(bbox: BBox) -> np.ndarray:
    x1, y1, x2, y2 = bbox
    w = max(0.0, float(x2) - float(x1))
    h = max(0.0, float(y2) - float(y1))
    cx = float(x1) + 0.5 * w
    cy = float(y1) + 0.5 * h
    return np.array([cx, cy, w, h], dtype=float)


def z_to_bbox(state: Sequence[float]) -> np.ndarray:
    cx, cy, w, h = [float(v) for v in state[:4]]
    w = max(0.0, w)
    h = max(0.0, h)
    half_w = 0.5 * w
    half_h = 0.5 * h
    return np.array([cx - half_w, cy - half_h, cx + half_w, cy + half_h], dtype=float)


def bbox_area(bbox: BBox) -> float:
    x1, y1, x2, y2 = bbox
    return max(0.0, float(x2) - float(x1)) * max(0.0, float(y2) - float(y1))


def bbox_iou(a: BBox, b: BBox) -> float:
    ax1, ay1, ax2, ay2 = [float(v) for v in a]
    bx1, by1, bx2, by2 = [float(v) for v in b]

    ix1 = max(ax1, bx1)
    iy1 = max(ay1, by1)
    ix2 = min(ax2, bx2)
    iy2 = min(ay2, by2)

    inter_w = max(0.0, ix2 - ix1)
    inter_h = max(0.0, iy2 - iy1)
    inter = inter_w * inter_h
    if inter <= 0.0:
        return 0.0

    union = bbox_area(a) + bbox_area(b) - inter
    if union <= 0.0:
        return 0.0
    return inter / union


class KalmanFilterBBoxCV:
    """Constant-velocity Kalman filter with full bbox state.

    State: [cx, cy, w, h, vx, vy, vw, vh]
    Measurement: [cx, cy, w, h]
    """

    def __init__(self, initial_bbox: BBox):
        z = bbox_to_z(initial_bbox)
        self.x = np.array([z[0], z[1], z[2], z[3], 0.0, 0.0, 0.0, 0.0], dtype=float)

        self.P = np.eye(8, dtype=float)
        self.P[:4, :4] *= 50.0
        self.P[4:, 4:] *= 200.0

        self.F = np.eye(8, dtype=float)
        self.F[0, 4] = 1.0
        self.F[1, 5] = 1.0
        self.F[2, 6] = 1.0
        self.F[3, 7] = 1.0

        self.H = np.zeros((4, 8), dtype=float)
        self.H[0, 0] = 1.0
        self.H[1, 1] = 1.0
        self.H[2, 2] = 1.0
        self.H[3, 3] = 1.0

        q_pos = 1.0
        q_size = 2.0
        q_vel = 5.0
        self.Q = np.diag([q_pos, q_pos, q_size, q_size, q_vel, q_vel, q_vel, q_vel]).astype(float)

        r_pos = 10.0
        r_size = 25.0
        self.R = np.diag([r_pos, r_pos, r_size, r_size]).astype(float)

    def predict(self) -> np.ndarray:
        self.x = self.F @ self.x
        self.x[2] = max(1.0, self.x[2])
        self.x[3] = max(1.0, self.x[3])
        self.P = self.F @ self.P @ self.F.T + self.Q
        return self.bbox.copy()

    def update(self, measurement_bbox: BBox) -> np.ndarray:
        z = bbox_to_z(measurement_bbox)
        y = z - self.H @ self.x
        S = self.H @ self.P @ self.H.T + self.R
        K = self.P @ self.H.T @ np.linalg.inv(S)
        self.x = self.x + K @ y
        self.x[2] = max(1.0, self.x[2])
        self.x[3] = max(1.0, self.x[3])
        identity = np.eye(self.P.shape[0], dtype=float)
        self.P = (identity - K @ self.H) @ self.P
        return self.bbox.copy()

    @property
    def bbox(self) -> np.ndarray:
        return z_to_bbox(self.x[:4])

    @property
    def centroid(self) -> np.ndarray:
        return self.x[:2].copy()


@dataclass
class Track:
    track_id: int
    bbox: np.ndarray
    class_id: int
    class_name: str
    confidence: float
    kalman: KalmanFilterBBoxCV
    world_point: Optional[np.ndarray] = None
    age: int = 1
    hits: int = 1
    missing: int = 0
    predicted_bbox: np.ndarray = field(default_factory=lambda: np.zeros(4, dtype=float))

    def predict(self) -> np.ndarray:
        self.predicted_bbox = self.kalman.predict()
        self.bbox = self.predicted_bbox.copy()
        self.age += 1
        self.missing += 1
        return self.predicted_bbox

    def update(
        self,
        bbox: BBox,
        class_id: int,
        class_name: str,
        confidence: float,
        world_point: Optional[np.ndarray],
    ) -> None:
        self.bbox = np.asarray(self.kalman.update(bbox), dtype=float)
        self.class_id = int(class_id)
        self.class_name = str(class_name)
        self.confidence = float(confidence)
        self.world_point = None if world_point is None else np.asarray(world_point, dtype=float)
        self.predicted_bbox = self.bbox.copy()
        self.hits += 1
        self.missing = 0


@dataclass
class TrackedDetection:
    track_id: int
    bbox: np.ndarray
    class_id: int
    class_name: str
    confidence: float
    world_point: Optional[np.ndarray]


class HungarianAssigner:
    @staticmethod
    def solve(cost_matrix: np.ndarray) -> List[Tuple[int, int]]:
        cost_matrix = np.asarray(cost_matrix, dtype=float)
        if cost_matrix.size == 0:
            return []

        n_rows, n_cols = cost_matrix.shape
        transposed = False
        if n_rows > n_cols:
            cost_matrix = cost_matrix.T
            n_rows, n_cols = cost_matrix.shape
            transposed = True

        u = np.zeros(n_rows + 1, dtype=float)
        v = np.zeros(n_cols + 1, dtype=float)
        p = np.zeros(n_cols + 1, dtype=int)
        way = np.zeros(n_cols + 1, dtype=int)

        for i in range(1, n_rows + 1):
            p[0] = i
            minv = np.full(n_cols + 1, np.inf, dtype=float)
            used = np.zeros(n_cols + 1, dtype=bool)
            j0 = 0
            while True:
                used[j0] = True
                i0 = p[j0]
                delta = np.inf
                j1 = 0
                for j in range(1, n_cols + 1):
                    if used[j]:
                        continue
                    cur = cost_matrix[i0 - 1, j - 1] - u[i0] - v[j]
                    if cur < minv[j]:
                        minv[j] = cur
                        way[j] = j0
                    if minv[j] < delta:
                        delta = minv[j]
                        j1 = j
                for j in range(n_cols + 1):
                    if used[j]:
                        u[p[j]] += delta
                        v[j] -= delta
                    else:
                        minv[j] -= delta
                j0 = j1
                if p[j0] == 0:
                    break
            while True:
                j1 = way[j0]
                p[j0] = p[j1]
                j0 = j1
                if j0 == 0:
                    break

        assignment: List[Tuple[int, int]] = []
        for j in range(1, n_cols + 1):
            if p[j] != 0:
                row = p[j] - 1
                col = j - 1
                assignment.append((row, col))

        if transposed:
            assignment = [(col, row) for row, col in assignment]
        return assignment


class SortTracker:
    def __init__(self, max_distance: float = 60.0, max_missing: int = 10, min_iou: float = 0.01):
        self.max_distance = float(max_distance)
        self.max_missing = int(max_missing)
        self.min_iou = float(min_iou)
        self.tracks: Dict[int, Track] = {}
        self.next_track_id = 1

    def _create_track(
        self,
        bbox: BBox,
        class_id: int,
        class_name: str,
        confidence: float,
        world_point: Optional[np.ndarray],
    ) -> Track:
        track = Track(
            track_id=self.next_track_id,
            bbox=np.asarray(bbox, dtype=float),
            class_id=int(class_id),
            class_name=str(class_name),
            confidence=float(confidence),
            kalman=KalmanFilterBBoxCV(bbox),
            world_point=None if world_point is None else np.asarray(world_point, dtype=float),
            predicted_bbox=np.asarray(bbox, dtype=float),
        )
        self.tracks[track.track_id] = track
        self.next_track_id += 1
        return track

    def update(self, detections: Sequence[dict]) -> List[TrackedDetection]:
        if not self.tracks and not detections:
            return []

        track_ids = list(self.tracks.keys())
        predicted_bboxes = []
        for track_id in track_ids:
            predicted_bboxes.append(self.tracks[track_id].predict())
        predicted_bboxes = np.asarray(predicted_bboxes, dtype=float) if predicted_bboxes else np.empty((0, 4))

        det_bboxes = np.asarray([det["bbox"] for det in detections], dtype=float) if detections else np.empty((0, 4))
        det_z = np.asarray([bbox_to_z(det["bbox"]) for det in detections], dtype=float) if detections else np.empty((0, 4))

        matches: List[Tuple[int, int]] = []
        unmatched_tracks = set(range(len(track_ids)))
        unmatched_detections = set(range(len(detections)))

        if len(track_ids) > 0 and len(detections) > 0:
            cost_matrix = np.full((len(track_ids), len(detections)), 1e6, dtype=float)
            for track_idx, track_id in enumerate(track_ids):
                track = self.tracks[track_id]
                pred_z = bbox_to_z(track.predicted_bbox)
                for det_idx, det_bbox in enumerate(det_bboxes):
                    det_measure = det_z[det_idx]
                    center_distance = np.linalg.norm(pred_z[:2] - det_measure[:2])
                    iou = bbox_iou(track.predicted_bbox, det_bbox)
                    if center_distance <= self.max_distance and iou >= self.min_iou:
                        size_delta = np.linalg.norm(pred_z[2:] - det_measure[2:])
                        cost_matrix[track_idx, det_idx] = (1.0 - iou) + 0.01 * center_distance + 0.005 * size_delta

            for track_idx, det_idx in HungarianAssigner.solve(cost_matrix):
                if cost_matrix[track_idx, det_idx] < 1e5:
                    matches.append((track_idx, det_idx))
                    unmatched_tracks.discard(track_idx)
                    unmatched_detections.discard(det_idx)

        for track_idx, det_idx in matches:
            track = self.tracks[track_ids[track_idx]]
            det = detections[det_idx]
            track.update(
                det["bbox"],
                det["class_id"],
                det["class_name"],
                det["confidence"],
                det.get("world_point"),
            )

        stale_ids = []
        for track_idx in unmatched_tracks:
            track = self.tracks[track_ids[track_idx]]
            if track.missing > self.max_missing:
                stale_ids.append(track.track_id)
        for track_id in stale_ids:
            self.tracks.pop(track_id, None)

        for det_idx in unmatched_detections:
            det = detections[det_idx]
            self._create_track(
                det["bbox"],
                det["class_id"],
                det["class_name"],
                det["confidence"],
                det.get("world_point"),
            )

        outputs: List[TrackedDetection] = []
        for track_id in sorted(self.tracks.keys()):
            track = self.tracks[track_id]
            if track.missing == 0:
                outputs.append(
                    TrackedDetection(
                        track_id=track.track_id,
                        bbox=track.bbox.copy(),
                        class_id=track.class_id,
                        class_name=track.class_name,
                        confidence=track.confidence,
                        world_point=None if track.world_point is None else track.world_point.copy(),
                    )
                )
        return outputs
