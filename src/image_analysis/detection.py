"""Object detection utilities.

Provides basic object-detection helpers that wrap common OpenCV and
third-party model interfaces.  Replace the stub implementations with
your actual model integration.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import cv2
import numpy as np

logger = logging.getLogger(__name__)

# Minimum confidence score for a detection to be kept.
DETECTION_CONFIDENCE_THRESHOLD: float = 0.5

# IoU threshold used by Non-Maximum Suppression.
NMS_IOU_THRESHOLD: float = 0.45


@dataclass(frozen=True)
class Detection:
    """A single object detection result.

    Attributes:
        label: Predicted class name.
        confidence: Prediction confidence in ``[0.0, 1.0]``.
        bbox: Bounding box as ``(x1, y1, x2, y2)`` in pixel coordinates.
    """

    label: str
    confidence: float
    bbox: tuple[int, int, int, int]


def detect_objects(
    image: np.ndarray,
    confidence_threshold: float = DETECTION_CONFIDENCE_THRESHOLD,
) -> list[Detection]:
    """Detect objects in *image* and return filtered detections.

    This is a **stub** implementation that returns an empty list.
    Replace the body with your model's inference call.

    Args:
        image: BGR image array with shape ``(H, W, 3)``, dtype ``uint8``.
        confidence_threshold: Minimum confidence score. Detections below
            this value are discarded.

    Returns:
        List of :class:`Detection` objects sorted by descending confidence.

    Raises:
        TypeError: If *image* is not a ``np.ndarray``.
        ValueError: If *image* is not a 3-channel BGR array.
        ValueError: If *confidence_threshold* is outside ``[0.0, 1.0]``.
    """
    _validate_bgr_image(image)
    if not (0.0 <= confidence_threshold <= 1.0):
        raise ValueError(f"confidence_threshold must be in [0.0, 1.0], got {confidence_threshold}")

    # TODO(#issue-number): Replace stub with actual model inference.
    raw_detections: list[Detection] = []

    detections = [d for d in raw_detections if d.confidence >= confidence_threshold]
    detections.sort(key=lambda d: d.confidence, reverse=True)

    logger.debug("Detected %d objects above threshold %.2f", len(detections), confidence_threshold)
    return detections


def apply_nms(
    detections: list[Detection],
    iou_threshold: float = NMS_IOU_THRESHOLD,
) -> list[Detection]:
    """Apply Non-Maximum Suppression to remove overlapping bounding boxes.

    Args:
        detections: List of detections to filter.
        iou_threshold: Maximum allowed IoU between kept boxes.

    Returns:
        Filtered list of :class:`Detection` objects.

    Raises:
        ValueError: If *iou_threshold* is outside ``[0.0, 1.0]``.
    """
    if not (0.0 <= iou_threshold <= 1.0):
        raise ValueError(f"iou_threshold must be in [0.0, 1.0], got {iou_threshold}")

    if not detections:
        return []

    def _iou(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
        ax1, ay1, ax2, ay2 = a
        bx1, by1, bx2, by2 = b
        inter_x1 = max(ax1, bx1)
        inter_y1 = max(ay1, by1)
        inter_x2 = min(ax2, bx2)
        inter_y2 = min(ay2, by2)
        iw = max(0, inter_x2 - inter_x1)
        ih = max(0, inter_y2 - inter_y1)
        inter = float(iw * ih)
        area_a = float(max(0, ax2 - ax1) * max(0, ay2 - ay1))
        area_b = float(max(0, bx2 - bx1) * max(0, by2 - by1))
        union = area_a + area_b - inter
        return 0.0 if union <= 0 else inter / union

    sorted_dets = sorted(detections, key=lambda d: d.confidence, reverse=True)
    kept: list[Detection] = []
    for cand in sorted_dets:
        if all(_iou(cand.bbox, k.bbox) <= iou_threshold for k in kept):
            kept.append(cand)

    return kept


def draw_bounding_boxes(
    image: np.ndarray,
    detections: list[Detection],
    color: tuple[int, int, int] = (0, 255, 0),
    thickness: int = 2,
    label_color: tuple[int, int, int] = (0, 0, 255),
    font_scale: float = 0.75,
) -> np.ndarray:
    """Draw bounding boxes and labels onto a copy of *image*.

    Labels are rendered in red above the bounding box by default.

    Args:
        image: BGR image array with shape ``(H, W, 3)``, dtype ``uint8``.
        detections: Detections to draw.
        color: BGR colour for the bounding box rectangle.
        thickness: Line thickness in pixels.
        label_color: BGR colour for the text label drawn above the box.
            Defaults to red ``(0, 0, 255)``.
        font_scale: Font scale factor for the label text.

    Returns:
        Copy of *image* with bounding boxes and labels drawn.

    Raises:
        TypeError: If *image* is not a ``np.ndarray``.
        ValueError: If *image* is not a 3-channel BGR array.
    """
    _validate_bgr_image(image)
    output: np.ndarray = image.copy()

    h, w = output.shape[:2]
    t = max(1, thickness)
    for det in detections:
        x1, y1, x2, y2 = det.bbox
        x1 = max(0, min(w - 1, x1))
        x2 = max(0, min(w, x2))
        y1 = max(0, min(h - 1, y1))
        y2 = max(0, min(h, y2))
        if x2 <= x1 or y2 <= y1:
            continue
        output[y1 : min(y1 + t, y2), x1:x2] = color
        output[max(y2 - t, y1) : y2, x1:x2] = color
        output[y1:y2, x1 : min(x1 + t, x2)] = color
        output[y1:y2, max(x2 - t, x1) : x2] = color

        label = f"{det.label} {det.confidence:.2f}"
        label_y = max(y1 - 6, 18)
        cv2.putText(
            output,
            label,
            (x1, label_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            font_scale,
            label_color,
            t,
        )

    return output


def _validate_bgr_image(image: np.ndarray) -> None:
    """Validate that *image* is a 3-channel BGR uint8 array.

    Args:
        image: Value to validate.

    Raises:
        TypeError: If *image* is not a ``np.ndarray``.
        ValueError: If *image* does not have shape ``(H, W, 3)``.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(f"Expected np.ndarray, got {type(image).__name__}")
    if image.ndim != 3 or image.shape[2] != 3:
        raise ValueError(
            f"Expected 3-channel BGR image with shape (H, W, 3), got shape {image.shape}"
        )
