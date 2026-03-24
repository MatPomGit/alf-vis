"""Tests for image_analysis.pose_estimation module."""

from __future__ import annotations

import numpy as np
import pytest

from image_analysis.calibration import CalibrationResult
from image_analysis.markers import MarkerDetection, MarkerType
from image_analysis.pose_estimation import (
    Pose3D,
    backproject_to_3d,
    draw_pose_axes,
    estimate_pose_from_depth,
    estimate_pose_from_marker,
    estimate_poses_from_markers,
)


@pytest.fixture
def calibration() -> CalibrationResult:
    """Return a synthetic camera calibration."""
    K = np.array(
        [[500.0, 0.0, 320.0], [0.0, 500.0, 240.0], [0.0, 0.0, 1.0]], dtype=np.float64
    )
    D = np.zeros((1, 5), dtype=np.float64)
    return CalibrationResult(
        camera_matrix=K, dist_coeffs=D, rms_error=0.2, image_size=(640, 480)
    )


@pytest.fixture
def square_marker() -> MarkerDetection:
    """Return a synthetic ArUco marker with square corners."""
    corners = np.array(
        [[150.0, 90.0], [190.0, 90.0], [190.0, 130.0], [150.0, 130.0]], dtype=np.float32
    )
    return MarkerDetection(
        marker_type=MarkerType.ARUCO, marker_id=0, corners=corners
    )


@pytest.fixture
def depth_map() -> np.ndarray:
    """Return a 480x640 depth map with constant depth of 1.5 m."""
    depth = np.full((480, 640), 1.5, dtype=np.float32)
    return depth


@pytest.fixture
def bgr_image() -> np.ndarray:
    rng = np.random.default_rng(seed=3)
    return rng.integers(0, 255, (480, 640, 3), dtype=np.uint8)


class TestPose3D:
    def test_rotation_matrix_is_3x3(self) -> None:
        rvec = np.zeros((3, 1), dtype=np.float64)
        tvec = np.array([[0.1], [0.2], [1.0]], dtype=np.float64)
        pose = Pose3D(rvec=rvec, tvec=tvec)
        assert pose.rotation_matrix.shape == (3, 3)

    def test_identity_rotation_gives_eye(self) -> None:
        rvec = np.zeros((3, 1), dtype=np.float64)
        tvec = np.zeros((3, 1), dtype=np.float64)
        pose = Pose3D(rvec=rvec, tvec=tvec)
        np.testing.assert_allclose(pose.rotation_matrix, np.eye(3), atol=1e-9)

    def test_position_m_returns_tuple_of_3(self) -> None:
        rvec = np.zeros((3, 1), dtype=np.float64)
        tvec = np.array([[1.0], [2.0], [3.0]], dtype=np.float64)
        pose = Pose3D(rvec=rvec, tvec=tvec)
        x, y, z = pose.position_m
        assert x == pytest.approx(1.0)
        assert y == pytest.approx(2.0)
        assert z == pytest.approx(3.0)

    def test_distance_m(self) -> None:
        rvec = np.zeros((3, 1), dtype=np.float64)
        tvec = np.array([[3.0], [4.0], [0.0]], dtype=np.float64)
        pose = Pose3D(rvec=rvec, tvec=tvec)
        assert pose.distance_m == pytest.approx(5.0)


class TestEstimatePoseFromMarker:
    def test_returns_pose3d_instance(
        self, square_marker: MarkerDetection, calibration: CalibrationResult
    ) -> None:
        pose = estimate_pose_from_marker(square_marker, calibration)
        assert isinstance(pose, Pose3D)

    def test_pose_has_valid_rotation_matrix(
        self, square_marker: MarkerDetection, calibration: CalibrationResult
    ) -> None:
        pose = estimate_pose_from_marker(square_marker, calibration)
        # Rotation matrix should be orthogonal.
        RtR = pose.rotation_matrix.T @ pose.rotation_matrix
        np.testing.assert_allclose(RtR, np.eye(3), atol=1e-5)


class TestEstimatePosesFromMarkers:
    def test_returns_list_of_pairs(
        self, square_marker: MarkerDetection, calibration: CalibrationResult
    ) -> None:
        results = estimate_poses_from_markers([square_marker], calibration)
        assert len(results) == 1
        marker, pose = results[0]
        assert marker is square_marker
        assert isinstance(pose, Pose3D)

    def test_empty_input_returns_empty(
        self, calibration: CalibrationResult
    ) -> None:
        assert estimate_poses_from_markers([], calibration) == []


class TestBackprojectTo3d:
    def test_centre_pixel_at_known_depth(
        self, calibration: CalibrationResult
    ) -> None:
        # Principal point at (320, 240); pixel (320, 240) → (0, 0, Z).
        x, y, z = backproject_to_3d(320, 240, 2.0, calibration)
        assert x == pytest.approx(0.0, abs=1e-6)
        assert y == pytest.approx(0.0, abs=1e-6)
        assert z == pytest.approx(2.0)

    def test_raises_for_non_positive_depth(
        self, calibration: CalibrationResult
    ) -> None:
        with pytest.raises(ValueError):
            backproject_to_3d(100, 100, 0.0, calibration)


class TestEstimatePoseFromDepth:
    def test_returns_pose3d(
        self, depth_map: np.ndarray, calibration: CalibrationResult
    ) -> None:
        pose = estimate_pose_from_depth((100, 100, 200, 200), depth_map, calibration)
        assert isinstance(pose, Pose3D)

    def test_depth_stored_in_tvec(
        self, depth_map: np.ndarray, calibration: CalibrationResult
    ) -> None:
        pose = estimate_pose_from_depth((300, 200, 400, 300), depth_map, calibration)
        # Z should be ~1.5 m (constant depth map).
        _, _, z = pose.position_m
        assert z == pytest.approx(1.5, rel=0.01)

    def test_raises_for_empty_depth_roi(
        self, calibration: CalibrationResult
    ) -> None:
        # All-zero depth map → no valid pixels.
        depth = np.zeros((480, 640), dtype=np.float32)
        with pytest.raises(ValueError, match="No valid depth"):
            estimate_pose_from_depth((0, 0, 100, 100), depth, calibration)


class TestDrawPoseAxes:
    def test_returns_copy(
        self,
        bgr_image: np.ndarray,
        square_marker: MarkerDetection,
        calibration: CalibrationResult,
    ) -> None:
        pose = estimate_pose_from_marker(square_marker, calibration)
        result = draw_pose_axes(bgr_image, pose, calibration)
        assert result is not bgr_image
        assert result.shape == bgr_image.shape

    def test_raises_for_non_ndarray(
        self, square_marker: MarkerDetection, calibration: CalibrationResult
    ) -> None:
        pose = estimate_pose_from_marker(square_marker, calibration)
        with pytest.raises(TypeError):
            draw_pose_axes("not an image", pose, calibration)  # type: ignore[arg-type]
