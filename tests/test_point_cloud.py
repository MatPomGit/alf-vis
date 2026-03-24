"""Tests for image_analysis.point_cloud module."""

from __future__ import annotations

import numpy as np
import pytest

from image_analysis.calibration import CalibrationResult
from image_analysis.point_cloud import (
    PointCloud,
    RgbdFusionConfig,
    create_point_cloud,
)


@pytest.fixture
def calibration() -> CalibrationResult:
    K = np.array(
        [[500.0, 0.0, 320.0], [0.0, 500.0, 240.0], [0.0, 0.0, 1.0]], dtype=np.float64
    )
    D = np.zeros((1, 5), dtype=np.float64)
    return CalibrationResult(
        camera_matrix=K, dist_coeffs=D, rms_error=0.2, image_size=(640, 480)
    )


@pytest.fixture
def small_rgb() -> np.ndarray:
    rng = np.random.default_rng(seed=10)
    return rng.integers(0, 255, (60, 80, 3), dtype=np.uint8)


@pytest.fixture
def small_depth() -> np.ndarray:
    """Depth map with constant 1.0 m depth."""
    return np.full((60, 80), 1.0, dtype=np.float32)


class TestPointCloud:
    def test_len_returns_number_of_points(self) -> None:
        pts = np.zeros((42, 3), dtype=np.float64)
        col = np.zeros((42, 3), dtype=np.float32)
        cloud = PointCloud(points=pts, colors=col)
        assert len(cloud) == 42

    def test_is_empty_when_no_points(self) -> None:
        cloud = PointCloud(
            points=np.empty((0, 3), dtype=np.float64),
            colors=np.empty((0, 3), dtype=np.float32),
        )
        assert cloud.is_empty()

    def test_is_not_empty_with_points(self) -> None:
        pts = np.ones((5, 3), dtype=np.float64)
        col = np.ones((5, 3), dtype=np.float32)
        assert not PointCloud(points=pts, colors=col).is_empty()


class TestCreatePointCloud:
    def test_returns_point_cloud_instance(
        self,
        small_rgb: np.ndarray,
        small_depth: np.ndarray,
        calibration: CalibrationResult,
    ) -> None:
        cloud = create_point_cloud(small_rgb, small_depth, calibration)
        assert isinstance(cloud, PointCloud)

    def test_points_have_shape_n3(
        self,
        small_rgb: np.ndarray,
        small_depth: np.ndarray,
        calibration: CalibrationResult,
    ) -> None:
        cloud = create_point_cloud(small_rgb, small_depth, calibration)
        assert cloud.points.ndim == 2
        assert cloud.points.shape[1] == 3

    def test_colors_have_shape_n3(
        self,
        small_rgb: np.ndarray,
        small_depth: np.ndarray,
        calibration: CalibrationResult,
    ) -> None:
        cloud = create_point_cloud(small_rgb, small_depth, calibration)
        assert cloud.colors.shape[1] == 3

    def test_colors_are_normalised(
        self,
        small_rgb: np.ndarray,
        small_depth: np.ndarray,
        calibration: CalibrationResult,
    ) -> None:
        cloud = create_point_cloud(small_rgb, small_depth, calibration)
        if not cloud.is_empty():
            assert cloud.colors.min() >= 0.0
            assert cloud.colors.max() <= 1.0

    def test_z_values_equal_depth(
        self,
        small_rgb: np.ndarray,
        small_depth: np.ndarray,
        calibration: CalibrationResult,
    ) -> None:
        # All depth values are 1.0 m → all Z coordinates should be 1.0 m.
        cloud = create_point_cloud(small_rgb, small_depth, calibration)
        np.testing.assert_allclose(cloud.points[:, 2], 1.0, atol=1e-6)

    def test_stride_reduces_point_count(
        self,
        small_rgb: np.ndarray,
        small_depth: np.ndarray,
        calibration: CalibrationResult,
    ) -> None:
        cloud_full = create_point_cloud(
            small_rgb, small_depth, calibration, RgbdFusionConfig(stride=1)
        )
        cloud_half = create_point_cloud(
            small_rgb, small_depth, calibration, RgbdFusionConfig(stride=2)
        )
        assert len(cloud_half) < len(cloud_full)

    def test_raises_for_non_ndarray_rgb(
        self, small_depth: np.ndarray, calibration: CalibrationResult
    ) -> None:
        with pytest.raises(TypeError):
            create_point_cloud("not an image", small_depth, calibration)  # type: ignore[arg-type]

    def test_raises_for_mismatched_spatial_dimensions(
        self, small_rgb: np.ndarray, calibration: CalibrationResult
    ) -> None:
        wrong_depth = np.full((30, 40), 1.0, dtype=np.float32)
        with pytest.raises(ValueError, match="same spatial dimensions"):
            create_point_cloud(small_rgb, wrong_depth, calibration)

    def test_depth_range_filter(
        self, small_rgb: np.ndarray, calibration: CalibrationResult
    ) -> None:
        # Depth values of 0.05 m are below the default 0.1 m threshold.
        near_depth = np.full((60, 80), 0.05, dtype=np.float32)
        cfg = RgbdFusionConfig(depth_min_m=0.1)
        cloud = create_point_cloud(small_rgb, near_depth, calibration, cfg)
        assert cloud.is_empty()
