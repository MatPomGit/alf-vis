from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np


BBox = Sequence[float]


def bbox_to_centroid(bbox: BBox) -> np.ndarray:
    x1, y1, x2, y2 = bbox
    return np.array([(x1 + x2) * 0.5, (y1 + y2) * 0.5], dtype=float)


def bbox_area(bbox: BBox) -> float:
    x1, y1, x2, y2 = bbox
    return max(0.0, x2 - x1) * max(0.0, y2 - y1)


class KalmanFilterCV:
    """Simple constant-velocity Kalman filter over bbox centroid."""

    def __init__(self, initial_centroid: np.ndarray):
        self.x = np.array([
            initial_centroid[0],
            initial_centroid[1],
            0.0,
            0.0,
        ], dtype=float)
        self.P = np.eye(4, dtype=float) * 500.0
        self.F = np.array(
            [
                [1.0, 0.0, 1.0, 0.0],
                [0.0, 1.0, 0.0, 1.0],
                [0.0, 0.0, 1.0, 0.0],
                [0.0, 0.0, 0.0, 1.0],
            ],
            dtype=float,
        )
        self.H = np.array(
            [
                [1.0, 0.0, 0.0, 0.0],
                [0.0, 1.0, 0.0, 0.0],
            ],
            dtype=float,
        )
        self.Q = np.array(
            [
                [1.0, 0.0, 0.5, 0.0],
                [0.0, 1.0, 0.0, 0.5],
                [0.5, 0.0, 2.0, 0.0],
                [0.0, 0.5, 0.0, 2.0],
            ],
            dtype=float,
        )
        self.R = np.eye(2, dtype=float) * 10.0

    def predict(self) -> np.ndarray:
        self.x = self.F @ self.x
        self.P = self.F @ self.P @ self.F.T + self.Q
        return self.x[:2].copy()

    def update(self, measurement: np.ndarray) -> np.ndarray:
        z = np.asarray(measurement, dtype=float)
        y = z - self.H @ self.x
        S = self.H @ self.P @ self.H.T + self.R
        K = self.P @ self.H.T @ np.linalg.inv(S)
        self.x = self.x + K @ y
        identity = np.eye(self.P.shape[0], dtype=float)
        self.P = (identity - K @ self.H) @ self.P
        return self.x[:2].copy()

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
    kalman: KalmanFilterCV
    world_point: Optional[np.ndarray] = None
    age: int = 1
    hits: int = 1
    missing: int = 0
    predicted_centroid: np.ndarray = field(default_factory=lambda: np.zeros(2, dtype=float))

    def predict(self) -> np.ndarray:
        self.predicted_centroid = self.kalman.predict()
        self.age += 1
        self.missing += 1
        return self.predicted_centroid

    def update(
        self,
        bbox: BBox,
        class_id: int,
        class_name: str,
        confidence: float,
        world_point: Optional[np.ndarray],
    ) -> None:
        self.bbox = np.asarray(bbox, dtype=float)
        self.class_id = int(class_id)
        self.class_name = str(class_name)
        self.confidence = float(confidence)
        self.world_point = None if world_point is None else np.asarray(world_point, dtype=float)
        self.kalman.update(bbox_to_centroid(self.bbox))
        self.predicted_centroid = self.kalman.centroid
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
    def __init__(self, max_distance: float = 60.0, max_missing: int = 10):
        self.max_distance = float(max_distance)
        self.max_missing = int(max_missing)
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
        centroid = bbox_to_centroid(bbox)
        track = Track(
            track_id=self.next_track_id,
            bbox=np.asarray(bbox, dtype=float),
            class_id=int(class_id),
            class_name=str(class_name),
            confidence=float(confidence),
            kalman=KalmanFilterCV(centroid),
            world_point=None if world_point is None else np.asarray(world_point, dtype=float),
            predicted_centroid=centroid.copy(),
        )
        self.tracks[track.track_id] = track
        self.next_track_id += 1
        return track

    def update(self, detections: Sequence[dict]) -> List[TrackedDetection]:
        if not self.tracks and not detections:
            return []

        track_ids = list(self.tracks.keys())
        predicted_centroids = []
        for track_id in track_ids:
            predicted_centroids.append(self.tracks[track_id].predict())
        predicted_centroids = np.asarray(predicted_centroids, dtype=float) if predicted_centroids else np.empty((0, 2))

        det_centroids = np.asarray(
            [bbox_to_centroid(det["bbox"]) for det in detections],
            dtype=float,
        ) if detections else np.empty((0, 2))

        matches: List[Tuple[int, int]] = []
        unmatched_tracks = set(range(len(track_ids)))
        unmatched_detections = set(range(len(detections)))

        if len(track_ids) > 0 and len(detections) > 0:
            diff = predicted_centroids[:, None, :] - det_centroids[None, :, :]
            cost_matrix = np.linalg.norm(diff, axis=2)
            for track_idx, det_idx in HungarianAssigner.solve(cost_matrix):
                if cost_matrix[track_idx, det_idx] <= self.max_distance:
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
