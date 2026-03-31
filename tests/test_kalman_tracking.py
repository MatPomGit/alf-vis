"""Tests for image_analysis.kalman_tracking module."""

from __future__ import annotations

import pytest

from image_analysis.detection import Detection
from image_analysis.kalman_tracking import KalmanMultiObjectTracker


def _center_x(bbox: tuple[int, int, int, int]) -> float:
    return (bbox[0] + bbox[2]) / 2.0


def test_tracker_assigns_stable_id_for_same_object() -> None:
    tracker = KalmanMultiObjectTracker(iou_threshold=0.2, min_confirmed_hits=1)

    first = tracker.update([Detection(label="person", confidence=0.9, bbox=(10, 10, 50, 80))])
    second = tracker.update([Detection(label="person", confidence=0.9, bbox=(14, 11, 54, 81))])

    assert len(first) == 1
    assert len(second) == 1
    assert first[0].track_id == second[0].track_id


def test_tracker_handles_short_occlusion_and_recovers_same_id() -> None:
    tracker = KalmanMultiObjectTracker(
        iou_threshold=0.2,
        max_missed_frames=2,
        min_confirmed_hits=1,
    )

    first = tracker.update([Detection(label="car", confidence=0.95, bbox=(100, 50, 180, 120))])
    tracker.update([])
    recovered = tracker.update([Detection(label="car", confidence=0.91, bbox=(104, 52, 184, 122))])

    assert len(first) == 1
    assert len(recovered) == 1
    assert recovered[0].track_id == first[0].track_id


def test_kalman_filter_smooths_single_frame_outlier() -> None:
    tracker = KalmanMultiObjectTracker(
        iou_threshold=0.2,
        min_confirmed_hits=1,
        process_noise=1.0,
        measurement_noise=50.0,
    )

    raw_x_centers = [30.0, 35.0, 90.0, 45.0]
    raw_bboxes = [
        (10, 10, 50, 80),
        (15, 10, 55, 80),
        (70, 10, 110, 80),
        (25, 10, 65, 80),
    ]

    tracked_x_centers: list[float] = []
    for bbox in raw_bboxes:
        tracked = tracker.update([Detection(label="box", confidence=0.9, bbox=bbox)])
        tracked_x_centers.append(_center_x(tracked[0].bbox))

    outlier_raw_jump = raw_x_centers[2] - raw_x_centers[1]
    outlier_filtered_jump = tracked_x_centers[2] - tracked_x_centers[1]

    assert outlier_filtered_jump < outlier_raw_jump


def test_invalid_tracker_parameters_raise_value_error() -> None:
    with pytest.raises(ValueError):
        KalmanMultiObjectTracker(iou_threshold=1.5)

    with pytest.raises(ValueError):
        KalmanMultiObjectTracker(max_missed_frames=-1)
