"""Tests for image_analysis.calibration module."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from image_analysis.calibration import (
    CalibrationResult,
    calibrate_camera,
    compute_reprojection_error,
    find_chessboard_corners,
    load_calibration,
    save_calibration,
    undistort_image,
)


@pytest.fixture
def dummy_calibration() -> CalibrationResult:
    """Return a synthetic CalibrationResult for testing."""
    camera_matrix = np.array(
        [[500.0, 0.0, 320.0], [0.0, 500.0, 240.0], [0.0, 0.0, 1.0]], dtype=np.float64
    )
    dist_coeffs = np.zeros((1, 5), dtype=np.float64)
    return CalibrationResult(
        camera_matrix=camera_matrix,
        dist_coeffs=dist_coeffs,
        rms_error=0.3,
        image_size=(640, 480),
    )


@pytest.fixture
def bgr_image() -> np.ndarray:
    """Return a synthetic 200x200 BGR uint8 image."""
    rng = np.random.default_rng(seed=0)
    return rng.integers(0, 255, (200, 200, 3), dtype=np.uint8)


class TestFindChessboardCorners:
    def test_raises_for_non_ndarray(self) -> None:
        with pytest.raises(TypeError):
            find_chessboard_corners([[1, 2, 3]])  # type: ignore[arg-type]

    def test_raises_for_float_image(self) -> None:
        image = np.zeros((100, 100, 3), dtype=np.float32)
        with pytest.raises(ValueError, match="uint8"):
            find_chessboard_corners(image)

    def test_returns_false_for_blank_image(self, bgr_image: np.ndarray) -> None:
        found, corners = find_chessboard_corners(bgr_image)
        assert found is False
        assert corners is None


class TestCalibratCamera:
    def test_raises_for_empty_corners(self) -> None:
        with pytest.raises(ValueError, match="all_corners"):
            calibrate_camera([], image_size=(640, 480))


class TestSaveLoadCalibration:
    def test_round_trip(
        self, tmp_path: Path, dummy_calibration: CalibrationResult
    ) -> None:
        path = tmp_path / "cal.yaml"
        save_calibration(dummy_calibration, path)
        assert path.exists()
        loaded = load_calibration(path)
        np.testing.assert_allclose(
            loaded.camera_matrix, dummy_calibration.camera_matrix, atol=1e-6
        )
        assert loaded.rms_error == pytest.approx(dummy_calibration.rms_error)

    def test_creates_parent_directories(
        self, tmp_path: Path, dummy_calibration: CalibrationResult
    ) -> None:
        path = tmp_path / "a" / "b" / "cal.yaml"
        save_calibration(dummy_calibration, path)
        assert path.exists()


class TestLoadCalibration:
    def test_raises_file_not_found(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            load_calibration(tmp_path / "nonexistent.yaml")


class TestUndistortImage:
    def test_output_shape_matches_input(
        self, bgr_image: np.ndarray, dummy_calibration: CalibrationResult
    ) -> None:
        result = undistort_image(bgr_image, dummy_calibration)
        assert result.shape == bgr_image.shape

    def test_raises_for_non_ndarray(
        self, dummy_calibration: CalibrationResult
    ) -> None:
        with pytest.raises(TypeError):
            undistort_image("not an image", dummy_calibration)  # type: ignore[arg-type]


class TestComputeReprojectionError:
    def test_empty_result_returns_empty_list(
        self, dummy_calibration: CalibrationResult
    ) -> None:
        errors = compute_reprojection_error(dummy_calibration)
        assert errors == []

    def test_returns_list_for_nonempty_extrinsics(
        self, dummy_calibration: CalibrationResult
    ) -> None:
        rvec = np.zeros((3, 1), dtype=np.float64)
        tvec = np.zeros((3, 1), dtype=np.float64)
        cal = CalibrationResult(
            camera_matrix=dummy_calibration.camera_matrix,
            dist_coeffs=dummy_calibration.dist_coeffs,
            rms_error=0.3,
            image_size=(640, 480),
            rvecs=[rvec, rvec],
            tvecs=[tvec, tvec],
        )
        errors = compute_reprojection_error(cal)
        assert len(errors) == 2
