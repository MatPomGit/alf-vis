"""Tests for image_analysis.plane_detection module."""

from __future__ import annotations

import numpy as np
import pytest

from image_analysis.plane_detection import (
    Plane3D,
    detect_multiple_planes,
    fit_plane_ransac,
)


@pytest.fixture
def flat_xy_points() -> np.ndarray:
    """Return 200 points on the Z=0 plane with a small amount of noise."""
    rng = np.random.default_rng(seed=0)
    xy = rng.uniform(-1.0, 1.0, (200, 2))
    z = rng.normal(0.0, 0.005, (200, 1))  # 5 mm noise
    return np.hstack([xy, z]).astype(np.float64)


@pytest.fixture
def two_plane_points() -> np.ndarray:
    """Return points from two planes: Z=0 and Z=1."""
    rng = np.random.default_rng(seed=1)
    xy0 = rng.uniform(-1.0, 1.0, (100, 2))
    z0 = rng.normal(0.0, 0.005, (100, 1))
    plane0 = np.hstack([xy0, z0])

    xy1 = rng.uniform(-1.0, 1.0, (100, 2))
    z1 = rng.normal(1.0, 0.005, (100, 1))
    plane1 = np.hstack([xy1, z1])

    return np.vstack([plane0, plane1]).astype(np.float64)


class TestPlane3D:
    def test_horizontal_plane(self) -> None:
        plane = Plane3D(
            normal=np.array([0.0, 0.0, 1.0], dtype=np.float64), d=0.0
        )
        assert plane.is_horizontal

    def test_vertical_plane(self) -> None:
        plane = Plane3D(
            normal=np.array([1.0, 0.0, 0.0], dtype=np.float64), d=0.0
        )
        assert plane.is_vertical

    def test_default_inlier_indices_is_empty(self) -> None:
        plane = Plane3D(normal=np.array([0.0, 0.0, 1.0]), d=0.0)
        assert len(plane.inlier_indices) == 0


class TestFitPlaneRansac:
    def test_detects_horizontal_plane(self, flat_xy_points: np.ndarray) -> None:
        plane = fit_plane_ransac(flat_xy_points, rng_seed=42)
        assert plane is not None
        # Normal should be roughly (0, 0, ±1).
        assert abs(plane.normal[2]) > 0.95

    def test_inlier_ratio_is_high(self, flat_xy_points: np.ndarray) -> None:
        plane = fit_plane_ransac(flat_xy_points, rng_seed=42)
        assert plane is not None
        assert plane.inlier_ratio > 0.8

    def test_returns_none_for_too_few_points(self) -> None:
        pts = np.array([[0, 0, 0], [1, 0, 0]], dtype=np.float64)
        result = fit_plane_ransac(pts)
        assert result is None

    def test_raises_for_non_ndarray(self) -> None:
        with pytest.raises(TypeError):
            fit_plane_ransac([[0, 0, 0], [1, 0, 0], [0, 1, 0]])  # type: ignore[arg-type]

    def test_raises_for_wrong_shape(self) -> None:
        pts = np.zeros((10, 2), dtype=np.float64)
        with pytest.raises(ValueError):
            fit_plane_ransac(pts)

    def test_centroid_has_shape_3(self, flat_xy_points: np.ndarray) -> None:
        plane = fit_plane_ransac(flat_xy_points, rng_seed=42)
        assert plane is not None
        assert plane.centroid.shape == (3,)


class TestDetectMultiplePlanes:
    def test_detects_two_planes(self, two_plane_points: np.ndarray) -> None:
        planes = detect_multiple_planes(
            two_plane_points, max_planes=2, num_iterations=500
        )
        assert len(planes) == 2

    def test_max_planes_respected(self, two_plane_points: np.ndarray) -> None:
        planes = detect_multiple_planes(two_plane_points, max_planes=1)
        assert len(planes) <= 1

    def test_raises_for_non_ndarray(self) -> None:
        with pytest.raises(TypeError):
            detect_multiple_planes([[0, 0, 0]])  # type: ignore[arg-type]

    def test_raises_for_wrong_shape(self) -> None:
        pts = np.zeros((10, 2), dtype=np.float64)
        with pytest.raises(ValueError):
            detect_multiple_planes(pts)

    def test_empty_for_insufficient_points(self) -> None:
        pts = np.array([[0, 0, 0], [1, 0, 0]], dtype=np.float64)
        planes = detect_multiple_planes(pts)
        assert planes == []
