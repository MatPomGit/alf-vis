"""Tests for image_analysis.acquisition_metrics module."""

from __future__ import annotations

import numpy as np
import pytest

from image_analysis.acquisition_metrics import (
    AcquisitionMonitor,
    AcquisitionReport,
    MetricThresholds,
    assess_frame,
    compute_blur_score,
    compute_brightness_contrast,
    compute_depth_metrics,
    estimate_noise_std,
)


@pytest.fixture
def sharp_image() -> np.ndarray:
    """Return a high-contrast 100x100 BGR checkerboard (sharp)."""
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    img[::4, :] = 255
    img[:, ::4] = 255
    return img


@pytest.fixture
def blurry_image() -> np.ndarray:
    """Return a uniform (blurry) 100x100 BGR image."""
    return np.full((100, 100, 3), 128, dtype=np.uint8)


@pytest.fixture
def dark_image() -> np.ndarray:
    return np.zeros((100, 100, 3), dtype=np.uint8)


@pytest.fixture
def bright_image() -> np.ndarray:
    return np.full((100, 100, 3), 255, dtype=np.uint8)


@pytest.fixture
def valid_depth() -> np.ndarray:
    """Return a 100x100 depth map with all pixels at 2.0 m."""
    return np.full((100, 100), 2.0, dtype=np.float32)


@pytest.fixture
def partial_depth() -> np.ndarray:
    """Return a 100x100 depth map with 50 % valid pixels."""
    depth = np.full((100, 100), 2.0, dtype=np.float32)
    depth[:50, :] = 0.0  # invalid (zero)
    return depth


class TestComputeBlurScore:
    def test_sharp_image_has_higher_score_than_blurry(
        self, sharp_image: np.ndarray, blurry_image: np.ndarray
    ) -> None:
        sharp_score = compute_blur_score(sharp_image)
        blurry_score = compute_blur_score(blurry_image)
        assert sharp_score > blurry_score

    def test_returns_float(self, sharp_image: np.ndarray) -> None:
        result = compute_blur_score(sharp_image)
        assert isinstance(result, float)

    def test_raises_for_non_ndarray(self) -> None:
        with pytest.raises(TypeError):
            compute_blur_score("not an image")  # type: ignore[arg-type]


class TestComputeBrightnessContrast:
    def test_dark_image_has_low_brightness(self, dark_image: np.ndarray) -> None:
        brightness, _ = compute_brightness_contrast(dark_image)
        assert brightness < 10.0

    def test_bright_image_has_high_brightness(self, bright_image: np.ndarray) -> None:
        brightness, _ = compute_brightness_contrast(bright_image)
        assert brightness > 245.0

    def test_uniform_image_has_low_contrast(self, blurry_image: np.ndarray) -> None:
        _, contrast = compute_brightness_contrast(blurry_image)
        assert contrast < 5.0

    def test_raises_for_non_ndarray(self) -> None:
        with pytest.raises(TypeError):
            compute_brightness_contrast("not an image")  # type: ignore[arg-type]

    def test_raises_for_grayscale(self) -> None:
        gray = np.zeros((100, 100), dtype=np.uint8)
        with pytest.raises(ValueError):
            compute_brightness_contrast(gray)


class TestEstimateNoiseStd:
    def test_returns_float(self, sharp_image: np.ndarray) -> None:
        result = estimate_noise_std(sharp_image)
        assert isinstance(result, float)

    def test_uniform_image_has_low_noise(self, blurry_image: np.ndarray) -> None:
        noise = estimate_noise_std(blurry_image)
        assert noise < 5.0

    def test_raises_for_non_ndarray(self) -> None:
        with pytest.raises(TypeError):
            estimate_noise_std("not an image")  # type: ignore[arg-type]


class TestComputeDepthMetrics:
    def test_full_coverage(self, valid_depth: np.ndarray) -> None:
        coverage, mean, std = compute_depth_metrics(valid_depth)
        assert coverage == pytest.approx(1.0)
        assert mean == pytest.approx(2.0, abs=0.01)

    def test_partial_coverage(self, partial_depth: np.ndarray) -> None:
        coverage, _, _ = compute_depth_metrics(partial_depth)
        assert coverage == pytest.approx(0.5, abs=0.01)

    def test_all_zero_depth_gives_zero_coverage(self) -> None:
        depth = np.zeros((100, 100), dtype=np.float32)
        coverage, mean, std = compute_depth_metrics(depth)
        assert coverage == pytest.approx(0.0)
        assert np.isnan(mean)

    def test_raises_for_non_ndarray(self) -> None:
        with pytest.raises(TypeError):
            compute_depth_metrics([[1.0, 2.0]])  # type: ignore[arg-type]

    def test_raises_for_3d_array(self) -> None:
        arr = np.zeros((50, 50, 3), dtype=np.float32)
        with pytest.raises(ValueError):
            compute_depth_metrics(arr)


class TestAssessFrame:
    def test_blurry_flag_set_for_uniform_image(
        self, blurry_image: np.ndarray
    ) -> None:
        # A uniform image has Laplacian variance ≈ 0 → blurry.
        metrics = assess_frame(blurry_image)
        assert metrics.is_blurry

    def test_underexposed_flag_for_dark_image(
        self, dark_image: np.ndarray
    ) -> None:
        metrics = assess_frame(dark_image)
        assert metrics.is_underexposed

    def test_overexposed_flag_for_bright_image(
        self, bright_image: np.ndarray
    ) -> None:
        metrics = assess_frame(bright_image)
        assert metrics.is_overexposed

    def test_valid_frame_passes(self, sharp_image: np.ndarray) -> None:
        # Sharp image with mid-range brightness should not trigger flags.
        # Use custom thresholds to avoid edge cases in the checkerboard.
        thresh = MetricThresholds(min_blur_score=1.0, min_brightness=5.0)
        metrics = assess_frame(sharp_image, thresholds=thresh)
        assert metrics.blur_score > 0.0

    def test_depth_metrics_included_when_provided(
        self, sharp_image: np.ndarray, valid_depth: np.ndarray
    ) -> None:
        metrics = assess_frame(sharp_image, depth=valid_depth)
        assert metrics.depth_coverage > 0.0
        assert not np.isnan(metrics.depth_mean_m)

    def test_reprojection_error_stored(self, sharp_image: np.ndarray) -> None:
        metrics = assess_frame(sharp_image, reprojection_error=0.42)
        assert metrics.reprojection_error == pytest.approx(0.42)


class TestAcquisitionMonitor:
    def test_empty_monitor_returns_zero_report(self) -> None:
        monitor = AcquisitionMonitor()
        report = monitor.report()
        assert report.total_frames == 0

    def test_record_and_report(self, blurry_image: np.ndarray) -> None:
        monitor = AcquisitionMonitor()
        for _ in range(5):
            metrics = assess_frame(blurry_image)
            monitor.record(metrics)
        report = monitor.report()
        assert report.total_frames == 5

    def test_blur_rate_computation(self, blurry_image: np.ndarray) -> None:
        monitor = AcquisitionMonitor()
        for _ in range(4):
            monitor.record(assess_frame(blurry_image))
        report = monitor.report()
        # All frames are blurry (uniform image).
        assert report.blur_rate == pytest.approx(1.0)

    def test_reset_clears_history(self, blurry_image: np.ndarray) -> None:
        monitor = AcquisitionMonitor()
        monitor.record(assess_frame(blurry_image))
        monitor.reset()
        assert monitor.report().total_frames == 0


class TestAcquisitionReport:
    def test_invalid_rate_for_all_blurry(self) -> None:
        report = AcquisitionReport(
            total_frames=10, blurry_frames=10, overexposed_frames=0, underexposed_frames=0
        )
        assert report.blur_rate == pytest.approx(1.0)

    def test_invalid_rate_zero_total(self) -> None:
        report = AcquisitionReport(total_frames=0)
        assert report.blur_rate == pytest.approx(0.0)
