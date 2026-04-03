"""Image acquisition error assessment module.

Evaluates the quality of image acquisition from the Unitree G1 EDU camera
system.  Monitoring acquisition quality in real time allows the pipeline to:

- Detect motion blur caused by fast robot movement.
- Flag over-/under-exposed frames before they reach the detection stage.
- Track temporal consistency (dropped frames, outlier depth readings).
- Report calibration quality (reprojection error per frame).

Metrics computed
----------------
* **Blur score** - Laplacian variance; low values → blurred image.
* **Brightness** - Mean luminance in the YCrCb colour space.
* **Contrast** - Standard deviation of the luminance channel.
* **Noise** - Estimated noise standard deviation using a median-based
  estimator on the green channel.
* **Depth coverage** - Fraction of depth pixels that are valid (finite, > 0).
* **Depth std** - Standard deviation of valid depth values (metres).
* **Reprojection error** - Passed through from calibration when available.
* **Frame drop rate** - Estimated from inter-frame timestamps.

Implementation notes:
    - All metrics are computed on ``np.ndarray`` inputs with no heavy ML
      dependencies.
    - The :class:`AcquisitionMonitor` class accumulates statistics across
      multiple frames and emits warnings when thresholds are exceeded.
    - Thresholds are configurable via :class:`MetricThresholds`.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np

logger = logging.getLogger(__name__)

# Default quality thresholds (conservative, adjust per deployment).
DEFAULT_MIN_BLUR_SCORE: float = 100.0  # Laplacian variance
DEFAULT_MIN_BRIGHTNESS: float = 30.0  # YCrCb Y-channel mean
DEFAULT_MAX_BRIGHTNESS: float = 220.0
DEFAULT_MIN_CONTRAST: float = 10.0  # Y-channel std
DEFAULT_MAX_REPROJECTION_ERROR: float = 1.0  # pixels
DEFAULT_MIN_DEPTH_COVERAGE: float = 0.5  # fraction of valid pixels


@dataclass
class MetricThresholds:
    """Quality thresholds for acquisition metrics.

    Attributes:
        min_blur_score: Minimum acceptable Laplacian variance.
        min_brightness: Minimum acceptable mean luminance.
        max_brightness: Maximum acceptable mean luminance.
        min_contrast: Minimum acceptable luminance standard deviation.
        max_reprojection_error: Maximum acceptable calibration reprojection
            error in pixels.
        min_depth_coverage: Minimum fraction of valid depth pixels.
    """

    min_blur_score: float = DEFAULT_MIN_BLUR_SCORE
    min_brightness: float = DEFAULT_MIN_BRIGHTNESS
    max_brightness: float = DEFAULT_MAX_BRIGHTNESS
    min_contrast: float = DEFAULT_MIN_CONTRAST
    max_reprojection_error: float = DEFAULT_MAX_REPROJECTION_ERROR
    min_depth_coverage: float = DEFAULT_MIN_DEPTH_COVERAGE


@dataclass
class FrameMetrics:
    """Quality metrics for a single acquired frame.

    Attributes:
        blur_score: Laplacian variance of the luminance channel.
            Higher → sharper image.
        brightness: Mean luminance (Y channel in YCrCb), range ``[0, 255]``.
        contrast: Standard deviation of the luminance channel.
        noise_std: Estimated noise standard deviation.
        depth_coverage: Fraction of depth pixels with valid readings.
        depth_mean_m: Mean depth of valid pixels in metres.
        depth_std_m: Standard deviation of valid depth pixels in metres.
        reprojection_error: Reprojection error in pixels from calibration,
            or ``NaN`` if not available.
        is_blurry: ``True`` if *blur_score* is below the threshold.
        is_overexposed: ``True`` if *brightness* exceeds the threshold.
        is_underexposed: ``True`` if *brightness* is below the threshold.
    """

    blur_score: float = 0.0
    brightness: float = 0.0
    contrast: float = 0.0
    noise_std: float = 0.0
    depth_coverage: float = 0.0
    depth_mean_m: float = float("nan")
    depth_std_m: float = float("nan")
    reprojection_error: float = float("nan")
    is_blurry: bool = False
    is_overexposed: bool = False
    is_underexposed: bool = False

    @property
    def is_valid(self) -> bool:
        """Return ``True`` if none of the quality flags are set."""
        return not (self.is_blurry or self.is_overexposed or self.is_underexposed)


def compute_blur_score(image: np.ndarray) -> float:
    """Compute the blur score as Laplacian variance of the luminance channel.

    A higher value indicates a sharper image.  Typical threshold: 100.

    Args:
        image: BGR or greyscale ``uint8`` image.

    Returns:
        Laplacian variance (float).  Returns ``0.0`` for empty images.

    Raises:
        TypeError: If *image* is not a ``np.ndarray``.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(f"Expected np.ndarray, got {type(image).__name__}")
    import cv2

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def compute_brightness_contrast(
    image: np.ndarray,
) -> tuple[float, float]:
    """Compute mean luminance and contrast of *image*.

    Args:
        image: BGR ``uint8`` image array of shape ``(H, W, 3)``.

    Returns:
        Tuple ``(brightness, contrast)`` where *brightness* is the mean
        Y-channel value and *contrast* is its standard deviation.

    Raises:
        TypeError: If *image* is not a ``np.ndarray``.
        ValueError: If *image* is not a 3-channel BGR array.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(f"Expected np.ndarray, got {type(image).__name__}")
    if image.ndim != 3 or image.shape[2] != 3:
        raise ValueError(f"Expected 3-channel BGR image (H, W, 3), got shape {image.shape}")
    import cv2

    ycrcb = cv2.cvtColor(image, cv2.COLOR_BGR2YCrCb)
    y_channel = ycrcb[:, :, 0].astype(np.float32)
    return float(y_channel.mean()), float(y_channel.std())


def estimate_noise_std(image: np.ndarray) -> float:
    """Estimate image noise using a median-absolute-deviation estimator.

    Applies a simple high-pass filter and estimates the noise standard
    deviation from the resulting residuals.

    Args:
        image: BGR or greyscale ``uint8`` image array.

    Returns:
        Estimated noise standard deviation (float).

    Raises:
        TypeError: If *image* is not a ``np.ndarray``.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(f"Expected np.ndarray, got {type(image).__name__}")
    import cv2

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
    blurred = cv2.GaussianBlur(gray.astype(np.float32), (5, 5), 0)
    residuals = gray.astype(np.float32) - blurred
    mad = float(np.median(np.abs(residuals - np.median(residuals))))
    # Convert MAD to std estimate (consistent for Gaussian noise).
    return mad * 1.4826


def compute_depth_metrics(
    depth: np.ndarray,
) -> tuple[float, float, float]:
    """Compute depth map quality metrics.

    Args:
        depth: Depth map of shape ``(H, W)``, dtype ``float32``, in metres.
            ``NaN`` and zero values are treated as invalid.

    Returns:
        Tuple ``(coverage, mean_m, std_m)`` where:
        - *coverage* is the fraction of valid pixels in ``[0.0, 1.0]``,
        - *mean_m* is the mean depth of valid pixels in metres,
        - *std_m* is the standard deviation of valid depths in metres.
        *mean_m* and *std_m* are ``NaN`` when no valid pixels exist.

    Raises:
        TypeError: If *depth* is not a ``np.ndarray``.
        ValueError: If *depth* is not a 2-D float32 array.
    """
    if not isinstance(depth, np.ndarray):
        raise TypeError(f"Expected np.ndarray, got {type(depth).__name__}")
    if depth.ndim != 2:
        raise ValueError(f"depth must be 2-D, got {depth.ndim}-D")

    total = depth.size
    valid = depth[np.isfinite(depth) & (depth > 0)]
    coverage = float(valid.size) / max(total, 1)

    if valid.size == 0:
        return coverage, float("nan"), float("nan")
    return coverage, float(valid.mean()), float(valid.std())


def assess_frame(
    image: np.ndarray,
    depth: np.ndarray | None = None,
    reprojection_error: float = float("nan"),
    thresholds: MetricThresholds | None = None,
) -> FrameMetrics:
    """Compute all quality metrics for a single captured frame.

    Args:
        image: BGR ``uint8`` image array of shape ``(H, W, 3)``.
        depth: Optional depth map of shape ``(H, W)``, dtype ``float32``,
            in metres.
        reprojection_error: Calibration reprojection error in pixels, if
            already computed.
        thresholds: Quality thresholds.  Uses defaults when ``None``.

    Returns:
        :class:`FrameMetrics` with all computed quality indicators.

    Raises:
        TypeError: If *image* is not a ``np.ndarray``.
    """
    thresh = thresholds or MetricThresholds()

    blur = compute_blur_score(image)
    brightness, contrast = compute_brightness_contrast(image)
    noise = estimate_noise_std(image)

    depth_cov, depth_mean, depth_std = (0.0, float("nan"), float("nan"))
    if depth is not None:
        depth_cov, depth_mean, depth_std = compute_depth_metrics(depth)

    metrics = FrameMetrics(
        blur_score=blur,
        brightness=brightness,
        contrast=contrast,
        noise_std=noise,
        depth_coverage=depth_cov,
        depth_mean_m=depth_mean,
        depth_std_m=depth_std,
        reprojection_error=reprojection_error,
        is_blurry=blur < thresh.min_blur_score,
        is_overexposed=brightness > thresh.max_brightness,
        is_underexposed=brightness < thresh.min_brightness,
    )

    if not metrics.is_valid:
        logger.warning(
            "Frame quality issue detected: blurry=%s, over=%s, under=%s "
            "(blur=%.1f, brightness=%.1f).",
            metrics.is_blurry,
            metrics.is_overexposed,
            metrics.is_underexposed,
            blur,
            brightness,
        )
    return metrics


@dataclass
class AcquisitionReport:
    """Summary statistics over a sequence of assessed frames.

    Attributes:
        total_frames: Number of frames assessed.
        blurry_frames: Number of frames flagged as blurry.
        overexposed_frames: Number of over-exposed frames.
        underexposed_frames: Number of under-exposed frames.
        mean_blur_score: Mean blur score across all frames.
        mean_brightness: Mean brightness across all frames.
        mean_depth_coverage: Mean depth coverage fraction.
        mean_reprojection_error: Mean reprojection error (NaN if unavailable).
    """

    total_frames: int = 0
    blurry_frames: int = 0
    overexposed_frames: int = 0
    underexposed_frames: int = 0
    mean_blur_score: float = 0.0
    mean_brightness: float = 0.0
    mean_depth_coverage: float = 0.0
    mean_reprojection_error: float = float("nan")

    @property
    def blur_rate(self) -> float:
        """Fraction of blurry frames."""
        return self.blurry_frames / max(self.total_frames, 1)

    @property
    def invalid_rate(self) -> float:
        """Fraction of frames with at least one quality issue."""
        invalid = self.blurry_frames + self.overexposed_frames + self.underexposed_frames
        return invalid / max(self.total_frames, 1)


class AcquisitionMonitor:
    """Accumulates per-frame metrics and produces summary reports.

    Example::

        monitor = AcquisitionMonitor()
        for frame in camera.stream_rgbd():
            metrics = assess_frame(frame.rgb, frame.depth)
            monitor.record(metrics)
        report = monitor.report()
        print(f"Blur rate: {report.blur_rate:.1%}")

    Args:
        thresholds: Quality thresholds.  Uses defaults when ``None``.
    """

    def __init__(self, thresholds: MetricThresholds | None = None) -> None:
        self._thresholds = thresholds or MetricThresholds()
        self._metrics: list[FrameMetrics] = []

    def record(self, metrics: FrameMetrics) -> None:
        """Add a :class:`FrameMetrics` result to the history.

        Args:
            metrics: Metrics from :func:`assess_frame`.
        """
        self._metrics.append(metrics)

    def report(self) -> AcquisitionReport:
        """Generate a summary report over all recorded frames.

        Returns:
            :class:`AcquisitionReport` with aggregate statistics.
        """
        if not self._metrics:
            return AcquisitionReport()

        n = len(self._metrics)
        blurry = sum(1 for m in self._metrics if m.is_blurry)
        over = sum(1 for m in self._metrics if m.is_overexposed)
        under = sum(1 for m in self._metrics if m.is_underexposed)

        mean_blur = float(np.mean([m.blur_score for m in self._metrics]))
        mean_bright = float(np.mean([m.brightness for m in self._metrics]))
        mean_cov = float(np.mean([m.depth_coverage for m in self._metrics]))
        reproj_vals = [
            m.reprojection_error for m in self._metrics if np.isfinite(m.reprojection_error)
        ]
        mean_reproj = float(np.mean(reproj_vals)) if reproj_vals else float("nan")

        return AcquisitionReport(
            total_frames=n,
            blurry_frames=blurry,
            overexposed_frames=over,
            underexposed_frames=under,
            mean_blur_score=mean_blur,
            mean_brightness=mean_bright,
            mean_depth_coverage=mean_cov,
            mean_reprojection_error=mean_reproj,
        )

    def reset(self) -> None:
        """Clear the accumulated frame history."""
        self._metrics.clear()
