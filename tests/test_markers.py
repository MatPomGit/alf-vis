"""Tests for image_analysis.markers module."""

from __future__ import annotations

import numpy as np
import pytest

from image_analysis.markers import (
    MarkerDetection,
    MarkerType,
    _validate_bgr,
    detect_aruco_markers,
    detect_qr_codes,
)


@pytest.fixture
def bgr_image() -> np.ndarray:
    """Return a synthetic 200x200 BGR uint8 image."""
    rng = np.random.default_rng(seed=5)
    return rng.integers(0, 255, (200, 200, 3), dtype=np.uint8)


class TestMarkerDetection:
    def test_can_be_created(self) -> None:
        corners = np.array([[0, 0], [10, 0], [10, 10], [0, 10]], dtype=np.float32)
        det = MarkerDetection(
            marker_type=MarkerType.ARUCO, marker_id=3, corners=corners
        )
        assert det.marker_id == 3
        assert det.payload == ""

    def test_qr_marker_has_payload(self) -> None:
        corners = np.array([[0, 0], [10, 0], [10, 10], [0, 10]], dtype=np.float32)
        det = MarkerDetection(
            marker_type=MarkerType.QR_CODE,
            marker_id=-1,
            corners=corners,
            payload="hello",
        )
        assert det.payload == "hello"


class TestValidateBgr:
    def test_raises_for_non_ndarray(self) -> None:
        with pytest.raises(TypeError):
            _validate_bgr("not an image")  # type: ignore[arg-type]

    def test_raises_for_grayscale(self) -> None:
        with pytest.raises(ValueError):
            _validate_bgr(np.zeros((100, 100), dtype=np.uint8))

    def test_passes_for_valid_bgr(self, bgr_image: np.ndarray) -> None:
        _validate_bgr(bgr_image)  # should not raise


class TestDetectArucoMarkers:
    def test_returns_empty_for_blank_image(self, bgr_image: np.ndarray) -> None:
        result = detect_aruco_markers(bgr_image)
        assert isinstance(result, list)
        # A random image typically contains no ArUco markers.

    def test_raises_for_non_ndarray(self) -> None:
        with pytest.raises(TypeError):
            detect_aruco_markers("not an image")  # type: ignore[arg-type]

    def test_raises_for_grayscale_image(self) -> None:
        gray = np.zeros((100, 100), dtype=np.uint8)
        with pytest.raises(ValueError):
            detect_aruco_markers(gray)


class TestDetectQrCodes:
    def test_returns_empty_for_blank_image(self, bgr_image: np.ndarray) -> None:
        result = detect_qr_codes(bgr_image)
        assert isinstance(result, list)

    def test_raises_for_non_ndarray(self) -> None:
        with pytest.raises(TypeError):
            detect_qr_codes("not an image")  # type: ignore[arg-type]
