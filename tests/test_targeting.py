"""Tests for image_analysis.targeting module."""

from __future__ import annotations

import numpy as np
import pytest

from image_analysis.detection import Detection
from image_analysis.targeting import (
    compute_center_offset,
    compute_offsets,
    draw_crosshair,
    draw_target_line,
    get_most_centered,
)


@pytest.fixture
def bgr_image() -> np.ndarray:
    """Return a synthetic 200x300 BGR uint8 image."""
    rng = np.random.default_rng(seed=1)
    return rng.integers(0, 255, (200, 300, 3), dtype=np.uint8)


@pytest.fixture
def centered_detection() -> Detection:
    """Detection whose bounding box is centred on a 300x200 image."""
    # Image centre: (150, 100).  BBox centre: (150, 100).
    return Detection(label="person", confidence=0.9, bbox=(100, 50, 200, 150))


@pytest.fixture
def offset_detection() -> Detection:
    """Detection to the right and below centre."""
    # BBox centre: (250, 150).  Image centre (300x200): (150, 100).
    # Expected dx=+100, dy=+50.
    return Detection(label="chair", confidence=0.7, bbox=(200, 100, 300, 200))


class TestComputeCenterOffset:
    def test_centered_detection_has_zero_offset(
        self, centered_detection: Detection
    ) -> None:
        offset = compute_center_offset(centered_detection, 300, 200)
        assert offset.dx_px == pytest.approx(0.0)
        assert offset.dy_px == pytest.approx(0.0)
        assert offset.distance_px == pytest.approx(0.0)

    def test_normalised_offsets_are_in_range(
        self, offset_detection: Detection
    ) -> None:
        offset = compute_center_offset(offset_detection, 300, 200)
        assert -1.0 <= offset.dx_norm <= 1.0
        assert -1.0 <= offset.dy_norm <= 1.0

    def test_dx_positive_for_right_offset(
        self, offset_detection: Detection
    ) -> None:
        offset = compute_center_offset(offset_detection, 300, 200)
        assert offset.dx_px > 0

    def test_dy_positive_for_below_offset(
        self, offset_detection: Detection
    ) -> None:
        offset = compute_center_offset(offset_detection, 300, 200)
        assert offset.dy_px > 0

    @pytest.mark.parametrize("w,h", [(0, 100), (100, 0), (-1, 100)])
    def test_raises_for_non_positive_dimensions(
        self, centered_detection: Detection, w: int, h: int
    ) -> None:
        with pytest.raises(ValueError):
            compute_center_offset(centered_detection, w, h)

    def test_detection_stored_in_result(
        self, centered_detection: Detection
    ) -> None:
        offset = compute_center_offset(centered_detection, 300, 200)
        assert offset.detection is centered_detection


class TestComputeOffsets:
    def test_returns_same_length_as_input(self) -> None:
        dets = [
            Detection(label="a", confidence=0.9, bbox=(0, 0, 10, 10)),
            Detection(label="b", confidence=0.8, bbox=(20, 20, 30, 30)),
        ]
        offsets = compute_offsets(dets, 100, 100)
        assert len(offsets) == 2

    def test_empty_input_returns_empty(self) -> None:
        assert compute_offsets([], 100, 100) == []


class TestGetMostCentered:
    def test_returns_none_for_empty_list(self) -> None:
        assert get_most_centered([]) is None

    def test_returns_closest_to_centre(
        self,
        centered_detection: Detection,
        offset_detection: Detection,
    ) -> None:
        offsets = compute_offsets([centered_detection, offset_detection], 300, 200)
        best = get_most_centered(offsets)
        assert best is not None
        assert best.detection is centered_detection


class TestDrawCrosshair:
    def test_returns_copy_not_inplace(self, bgr_image: np.ndarray) -> None:
        original = bgr_image.copy()
        result = draw_crosshair(bgr_image)
        np.testing.assert_array_equal(bgr_image, original)
        assert result is not bgr_image

    def test_output_shape_matches_input(self, bgr_image: np.ndarray) -> None:
        result = draw_crosshair(bgr_image)
        assert result.shape == bgr_image.shape

    def test_raises_for_non_ndarray(self) -> None:
        with pytest.raises(TypeError):
            draw_crosshair("not an image")  # type: ignore[arg-type]

    def test_raises_for_grayscale_image(self) -> None:
        gray = np.zeros((100, 100), dtype=np.uint8)
        with pytest.raises(ValueError):
            draw_crosshair(gray)


class TestDrawTargetLine:
    def test_returns_copy(
        self, bgr_image: np.ndarray, centered_detection: Detection
    ) -> None:
        offset = compute_center_offset(centered_detection, 300, 200)
        result = draw_target_line(bgr_image, offset)
        assert result is not bgr_image

    def test_output_shape_matches_input(
        self, bgr_image: np.ndarray, offset_detection: Detection
    ) -> None:
        offset = compute_center_offset(offset_detection, 300, 200)
        result = draw_target_line(bgr_image, offset)
        assert result.shape == bgr_image.shape
