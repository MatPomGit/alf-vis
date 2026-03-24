"""Tests for image_analysis.viewer module."""

from __future__ import annotations

import numpy as np
import pytest

from image_analysis.viewer import (
    encode_jpeg,
    render_depth,
    render_rgb,
    render_rgbd_side_by_side,
)


@pytest.fixture
def bgr_image() -> np.ndarray:
    """Return a synthetic 100x200 BGR uint8 image."""
    rng = np.random.default_rng(seed=7)
    return rng.integers(50, 200, (100, 200, 3), dtype=np.uint8)


@pytest.fixture
def depth_map() -> np.ndarray:
    """Return a synthetic 100x200 depth map (float32, metres)."""
    rng = np.random.default_rng(seed=8)
    depth = rng.uniform(0.5, 5.0, (100, 200)).astype(np.float32)
    return depth


class TestRenderRgb:
    def test_output_is_copy(self, bgr_image: np.ndarray) -> None:
        result = render_rgb(bgr_image)
        assert result is not bgr_image
        original = bgr_image.copy()
        np.testing.assert_array_equal(bgr_image, original)

    def test_shape_preserved(self, bgr_image: np.ndarray) -> None:
        result = render_rgb(bgr_image)
        assert result.shape == bgr_image.shape

    def test_label_does_not_change_shape(self, bgr_image: np.ndarray) -> None:
        result = render_rgb(bgr_image, label="Test")
        assert result.shape == bgr_image.shape

    def test_raises_for_non_ndarray(self) -> None:
        with pytest.raises(TypeError):
            render_rgb("not an image")  # type: ignore[arg-type]

    def test_raises_for_grayscale(self) -> None:
        gray = np.zeros((100, 100), dtype=np.uint8)
        with pytest.raises(ValueError):
            render_rgb(gray)


class TestRenderDepth:
    def test_output_is_bgr_uint8(self, depth_map: np.ndarray) -> None:
        result = render_depth(depth_map)
        assert result.dtype == np.uint8
        assert result.ndim == 3
        assert result.shape[2] == 3

    def test_output_shape_matches_input(self, depth_map: np.ndarray) -> None:
        result = render_depth(depth_map)
        assert result.shape[:2] == depth_map.shape

    def test_zero_depth_pixels_are_black(self) -> None:
        depth = np.zeros((50, 50), dtype=np.float32)
        result = render_depth(depth)
        # All pixels should be black (no valid depth).
        assert np.all(result == 0)

    def test_raises_for_non_ndarray(self) -> None:
        with pytest.raises(TypeError):
            render_depth([[1.0, 2.0]])  # type: ignore[arg-type]

    def test_raises_for_3d_array(self) -> None:
        arr = np.zeros((50, 50, 3), dtype=np.float32)
        with pytest.raises(ValueError):
            render_depth(arr)

    def test_raises_for_wrong_dtype(self) -> None:
        arr = np.zeros((50, 50), dtype=np.uint8)
        with pytest.raises(ValueError):
            render_depth(arr)


class TestRenderRgbdSideBySide:
    def test_output_width_is_sum(
        self, bgr_image: np.ndarray, depth_map: np.ndarray
    ) -> None:
        result = render_rgbd_side_by_side(bgr_image, depth_map)
        # Width should be larger than either input alone.
        assert result.shape[1] > bgr_image.shape[1]

    def test_output_height_matches_rgb(
        self, bgr_image: np.ndarray, depth_map: np.ndarray
    ) -> None:
        result = render_rgbd_side_by_side(bgr_image, depth_map)
        assert result.shape[0] == bgr_image.shape[0]

    def test_output_is_bgr_uint8(
        self, bgr_image: np.ndarray, depth_map: np.ndarray
    ) -> None:
        result = render_rgbd_side_by_side(bgr_image, depth_map)
        assert result.dtype == np.uint8
        assert result.shape[2] == 3


class TestEncodeJpeg:
    def test_returns_bytes(self, bgr_image: np.ndarray) -> None:
        result = encode_jpeg(bgr_image)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_valid_jpeg_header(self, bgr_image: np.ndarray) -> None:
        result = encode_jpeg(bgr_image)
        # JPEG files start with the magic bytes 0xFF 0xD8.
        assert result[:2] == b"\xff\xd8"

    def test_raises_for_non_ndarray(self) -> None:
        with pytest.raises(TypeError):
            encode_jpeg("not an image")  # type: ignore[arg-type]
