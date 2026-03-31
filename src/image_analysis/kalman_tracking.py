"""Kalman-based multi-object tracking utilities.

The module implements a lightweight tracker that associates detections between
frames using IoU and smooths bounding boxes with a constant-velocity Kalman
filter.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from image_analysis.detection import Detection


@dataclass(frozen=True)
class TrackedObject:
    """Tracked object state exposed by :class:`KalmanMultiObjectTracker`.

    Attributes:
        track_id: Stable numerical identifier of the trajectory.
        label: Object class label copied from the latest associated detection.
        confidence: Confidence score from the latest associated detection.
        bbox: Bounding box as ``(x1, y1, x2, y2)`` in pixel coordinates.
        age: Number of frames since track creation.
        hits: Number of successful measurement associations.
        missed_frames: Number of consecutive frames without measurement match.
    """

    track_id: int
    label: str
    confidence: float
    bbox: tuple[int, int, int, int]
    age: int
    hits: int
    missed_frames: int


class KalmanBBoxFilter:
    """Constant-velocity Kalman filter for 2D bounding boxes.

    State vector: ``[cx, cy, w, h, vx, vy, vw, vh]``.
    Measurement vector: ``[cx, cy, w, h]``.
    """

    def __init__(
        self,
        initial_bbox: tuple[int, int, int, int],
        process_noise: float,
        measurement_noise: float,
    ) -> None:
        z = _bbox_to_measurement(initial_bbox)

        self._x = np.array([z[0], z[1], z[2], z[3], 0.0, 0.0, 0.0, 0.0], dtype=float)

        self._p = np.eye(8, dtype=float)
        self._p[:4, :4] *= 40.0
        self._p[4:, 4:] *= 100.0

        self._f = np.eye(8, dtype=float)
        self._f[0, 4] = 1.0
        self._f[1, 5] = 1.0
        self._f[2, 6] = 1.0
        self._f[3, 7] = 1.0

        self._h = np.zeros((4, 8), dtype=float)
        self._h[0, 0] = 1.0
        self._h[1, 1] = 1.0
        self._h[2, 2] = 1.0
        self._h[3, 3] = 1.0

        pos_noise = max(1e-6, process_noise)
        vel_noise = max(1e-6, process_noise * 4.0)
        self._q = np.diag([
            pos_noise,
            pos_noise,
            pos_noise,
            pos_noise,
            vel_noise,
            vel_noise,
            vel_noise,
            vel_noise,
        ]).astype(float)

        meas_noise = max(1e-6, measurement_noise)
        self._r = np.eye(4, dtype=float) * meas_noise

    def predict(self) -> tuple[int, int, int, int]:
        """Run prediction step and return predicted bounding box."""
        self._x = self._f @ self._x
        self._x[2] = max(1.0, self._x[2])
        self._x[3] = max(1.0, self._x[3])
        self._p = self._f @ self._p @ self._f.T + self._q
        return _measurement_to_bbox(self._x[:4])

    def update(self, bbox: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
        """Run correction step with measured *bbox* and return filtered bbox."""
        z = _bbox_to_measurement(bbox)
        innovation = z - self._h @ self._x
        residual_cov = self._h @ self._p @ self._h.T + self._r
        gain = self._p @ self._h.T @ np.linalg.inv(residual_cov)

        self._x = self._x + gain @ innovation
        self._x[2] = max(1.0, self._x[2])
        self._x[3] = max(1.0, self._x[3])

        identity = np.eye(self._p.shape[0], dtype=float)
        self._p = (identity - gain @ self._h) @ self._p
        return _measurement_to_bbox(self._x[:4])


@dataclass
class _TrackState:
    track_id: int
    label: str
    confidence: float
    bbox: tuple[int, int, int, int]
    filter: KalmanBBoxFilter
    age: int = 1
    hits: int = 1
    missed_frames: int = 0


class KalmanMultiObjectTracker:
    """Track detections over time with Kalman smoothing and IoU association.

    Args:
        iou_threshold: Minimum IoU required to match detection to an existing
            track.
        max_missed_frames: Maximum number of consecutive unmatched frames before
            deleting a track.
        min_confirmed_hits: Minimum number of associations required for a track
            to be considered confirmed and returned.
        process_noise: Process covariance scalar for Kalman filter.
        measurement_noise: Measurement covariance scalar for Kalman filter.
    """

    def __init__(
        self,
        iou_threshold: float = 0.3,
        max_missed_frames: int = 5,
        min_confirmed_hits: int = 2,
        process_noise: float = 2.0,
        measurement_noise: float = 20.0,
    ) -> None:
        if not 0.0 <= iou_threshold <= 1.0:
            raise ValueError(f"iou_threshold must be in [0.0, 1.0], got {iou_threshold}")
        if max_missed_frames < 0:
            raise ValueError("max_missed_frames must be >= 0")
        if min_confirmed_hits < 1:
            raise ValueError("min_confirmed_hits must be >= 1")
        if process_noise <= 0.0:
            raise ValueError("process_noise must be > 0.0")
        if measurement_noise <= 0.0:
            raise ValueError("measurement_noise must be > 0.0")

        self._iou_threshold = iou_threshold
        self._max_missed_frames = max_missed_frames
        self._min_confirmed_hits = min_confirmed_hits
        self._process_noise = process_noise
        self._measurement_noise = measurement_noise

        self._tracks: list[_TrackState] = []
        self._next_track_id = 1

    def update(self, detections: list[Detection]) -> list[TrackedObject]:
        """Update tracker with detections from the current frame.

        Args:
            detections: Detections in ``(x1, y1, x2, y2)`` format.

        Returns:
            Confirmed tracks represented as :class:`TrackedObject`.
        """
        for track in self._tracks:
            track.bbox = track.filter.predict()
            track.age += 1
            track.missed_frames += 1

        matches, unmatched_track_indices, unmatched_detection_indices = self._associate(detections)

        for track_idx, det_idx in matches:
            det = detections[det_idx]
            track = self._tracks[track_idx]
            track.bbox = track.filter.update(det.bbox)
            track.label = det.label
            track.confidence = det.confidence
            track.hits += 1
            track.missed_frames = 0

        for det_idx in unmatched_detection_indices:
            det = detections[det_idx]
            kalman_filter = KalmanBBoxFilter(
                initial_bbox=det.bbox,
                process_noise=self._process_noise,
                measurement_noise=self._measurement_noise,
            )
            self._tracks.append(
                _TrackState(
                    track_id=self._next_track_id,
                    label=det.label,
                    confidence=det.confidence,
                    bbox=det.bbox,
                    filter=kalman_filter,
                )
            )
            self._next_track_id += 1

        self._tracks = [
            track for track in self._tracks if track.missed_frames <= self._max_missed_frames
        ]

        _ = unmatched_track_indices
        return [
            self._to_public(track)
            for track in self._tracks
            if track.hits >= self._min_confirmed_hits
        ]

    def _associate(
        self, detections: list[Detection]
    ) -> tuple[list[tuple[int, int]], set[int], set[int]]:
        track_indices = set(range(len(self._tracks)))
        detection_indices = set(range(len(detections)))

        if not self._tracks or not detections:
            return [], track_indices, detection_indices

        candidate_pairs: list[tuple[float, int, int]] = []
        for track_idx, track in enumerate(self._tracks):
            for det_idx, detection in enumerate(detections):
                if detection.label != track.label:
                    continue
                iou = _compute_iou(track.bbox, detection.bbox)
                if iou >= self._iou_threshold:
                    candidate_pairs.append((iou, track_idx, det_idx))

        candidate_pairs.sort(key=lambda item: item[0], reverse=True)

        matches: list[tuple[int, int]] = []
        for _, track_idx, det_idx in candidate_pairs:
            if track_idx not in track_indices or det_idx not in detection_indices:
                continue
            track_indices.remove(track_idx)
            detection_indices.remove(det_idx)
            matches.append((track_idx, det_idx))

        return matches, track_indices, detection_indices

    @staticmethod
    def _to_public(track: _TrackState) -> TrackedObject:
        return TrackedObject(
            track_id=track.track_id,
            label=track.label,
            confidence=track.confidence,
            bbox=track.bbox,
            age=track.age,
            hits=track.hits,
            missed_frames=track.missed_frames,
        )


def _bbox_to_measurement(bbox: tuple[int, int, int, int]) -> np.ndarray:
    x1, y1, x2, y2 = bbox
    width = max(1.0, float(x2 - x1))
    height = max(1.0, float(y2 - y1))
    cx = float(x1) + 0.5 * width
    cy = float(y1) + 0.5 * height
    return np.array([cx, cy, width, height], dtype=float)


def _measurement_to_bbox(measurement: np.ndarray) -> tuple[int, int, int, int]:
    cx, cy, width, height = [float(value) for value in measurement]
    width = max(1.0, width)
    height = max(1.0, height)
    x1 = round(cx - 0.5 * width)
    y1 = round(cy - 0.5 * height)
    x2 = round(cx + 0.5 * width)
    y2 = round(cy + 0.5 * height)
    if x2 <= x1:
        x2 = x1 + 1
    if y2 <= y1:
        y2 = y1 + 1
    return (x1, y1, x2, y2)


def _compute_iou(box_a: tuple[int, int, int, int], box_b: tuple[int, int, int, int]) -> float:
    ax1, ay1, ax2, ay2 = box_a
    bx1, by1, bx2, by2 = box_b

    inter_x1 = max(ax1, bx1)
    inter_y1 = max(ay1, by1)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)

    inter_width = max(0, inter_x2 - inter_x1)
    inter_height = max(0, inter_y2 - inter_y1)
    inter_area = float(inter_width * inter_height)

    area_a = float(max(0, ax2 - ax1) * max(0, ay2 - ay1))
    area_b = float(max(0, bx2 - bx1) * max(0, by2 - by1))
    union = area_a + area_b - inter_area
    if union <= 0.0:
        return 0.0
    return inter_area / union
