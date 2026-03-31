"""Tests for active vision area optimisation module."""

from __future__ import annotations

import numpy as np
import pytest

from image_analysis.active_vision import ActiveVisionOptimizer, RegionOfInterest
from image_analysis.detection import Detection


def test_returns_default_center_roi_when_no_detections() -> None:
    optimizer = ActiveVisionOptimizer()

    roi = optimizer.optimize_region((200, 300), detections=[])

    assert roi.width > 0
    assert roi.height > 0
    # Should be close to image centre.
    cx, cy = roi.center
    assert cx == pytest.approx(150, abs=20)
    assert cy == pytest.approx(100, abs=20)


def test_prefers_higher_confidence_detection() -> None:
    optimizer = ActiveVisionOptimizer()
    detections = [
        Detection(label="low", confidence=0.3, bbox=(10, 10, 60, 60)),
        Detection(label="high", confidence=0.9, bbox=(200, 120, 260, 180)),
    ]

    roi = optimizer.optimize_region((240, 320), detections=detections)

    cx, cy = roi.center
    assert cx > 180
    assert cy > 100


def test_stability_keeps_roi_close_to_previous() -> None:
    optimizer = ActiveVisionOptimizer()
    previous = RegionOfInterest(20, 20, 100, 100)
    detections = [
        Detection(label="a", confidence=0.8, bbox=(30, 30, 80, 80)),
        Detection(label="b", confidence=0.82, bbox=(220, 120, 290, 190)),
    ]

    roi = optimizer.optimize_region((240, 320), detections=detections, previous_roi=previous)

    cx, cy = roi.center
    assert cx < 150
    assert cy < 120


def test_uncertainty_map_can_shift_attention() -> None:
    optimizer = ActiveVisionOptimizer()
    detections = [
        Detection(label="a", confidence=0.75, bbox=(30, 30, 90, 90)),
        Detection(label="b", confidence=0.76, bbox=(220, 120, 290, 190)),
    ]
    uncertainty = np.zeros((240, 320), dtype=np.float32)
    uncertainty[120:200, 200:320] = 1.0

    roi = optimizer.optimize_region(
        (240, 320), detections=detections, uncertainty_map=uncertainty
    )

    cx, _ = roi.center
    assert cx > 180


def test_invalid_uncertainty_map_shape_raises() -> None:
    optimizer = ActiveVisionOptimizer()
    detections = [Detection(label="x", confidence=0.9, bbox=(10, 10, 30, 30))]

    with pytest.raises(ValueError):
        optimizer.optimize_region((100, 100), detections, uncertainty_map=np.zeros((10, 10, 3)))
