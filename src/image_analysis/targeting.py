"""Target offset calculation - deviation of detected objects from image centre.

Computes the horizontal and vertical pixel offset between the bounding-box
centre of a detected object and the image centre point (the "crosshair" or
"reticle" placed at the middle of the viewport).

This information is used by the robot's navigation layer to:
- Decide how much to rotate left / right (yaw) to centre the target.
- Decide how much to tilt up / down (pitch) to align vertically.
- Determine which detection is "most centred" when several objects are visible.

Coordinate conventions
-----------------------
* ``dx > 0`` → target is to the right of centre.
* ``dx < 0`` → target is to the left of centre.
* ``dy > 0`` → target is below centre (image Y axis points downward).
* ``dy < 0`` → target is above centre.
* Normalised offsets are in ``[-1.0, 1.0]`` relative to half the image size.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np

from image_analysis.detection import Detection

logger = logging.getLogger(__name__)

# BGR colour of the crosshair drawn on the image.
CROSSHAIR_COLOR: tuple[int, int, int] = (0, 255, 255)  # yellow
CROSSHAIR_THICKNESS: int = 1
CROSSHAIR_RADIUS: int = 20


@dataclass(frozen=True)
class TargetOffset:
    """Pixel and normalised offset of a detection from the image centre.

    Attributes:
        detection: The source detection.
        dx_px: Horizontal pixel offset (positive = right).
        dy_px: Vertical pixel offset (positive = down).
        dx_norm: Horizontal offset normalised to ``[-1.0, 1.0]``.
        dy_norm: Vertical offset normalised to ``[-1.0, 1.0]``.
        distance_px: Euclidean distance from image centre in pixels.
    """

    detection: Detection
    dx_px: float
    dy_px: float
    dx_norm: float
    dy_norm: float
    distance_px: float


def compute_center_offset(
    detection: Detection,
    image_width: int,
    image_height: int,
) -> TargetOffset:
    """Compute the offset of *detection* from the image centre.

    Args:
        detection: A detection whose :attr:`~Detection.bbox` is in
            ``(x1, y1, x2, y2)`` pixel coordinates.
        image_width: Width of the source image in pixels.  Must be positive.
        image_height: Height of the source image in pixels.  Must be positive.

    Returns:
        :class:`TargetOffset` with pixel and normalised offsets.

    Raises:
        ValueError: If *image_width* or *image_height* is not positive.
    """
    if image_width <= 0 or image_height <= 0:
        raise ValueError(
            f"image_width and image_height must be positive, got {image_width}x{image_height}"
        )

    x1, y1, x2, y2 = detection.bbox
    bbox_cx = (x1 + x2) / 2.0
    bbox_cy = (y1 + y2) / 2.0

    img_cx = image_width / 2.0
    img_cy = image_height / 2.0

    dx_px = bbox_cx - img_cx
    dy_px = bbox_cy - img_cy

    dx_norm = dx_px / (image_width / 2.0)
    dy_norm = dy_px / (image_height / 2.0)
    dist = float(np.hypot(dx_px, dy_px))

    return TargetOffset(
        detection=detection,
        dx_px=dx_px,
        dy_px=dy_px,
        dx_norm=dx_norm,
        dy_norm=dy_norm,
        distance_px=dist,
    )


def compute_offsets(
    detections: list[Detection],
    image_width: int,
    image_height: int,
) -> list[TargetOffset]:
    """Compute centre offsets for all *detections*.

    Args:
        detections: List of detections from a single frame.
        image_width: Width of the source image in pixels.
        image_height: Height of the source image in pixels.

    Returns:
        List of :class:`TargetOffset` objects in the same order as
        *detections*.

    Raises:
        ValueError: If *image_width* or *image_height* is not positive.
    """
    return [compute_center_offset(d, image_width, image_height) for d in detections]


def get_most_centered(offsets: list[TargetOffset]) -> TargetOffset | None:
    """Return the detection closest to the image centre.

    Args:
        offsets: List of :class:`TargetOffset` objects.

    Returns:
        The :class:`TargetOffset` with the smallest
        :attr:`~TargetOffset.distance_px`, or ``None`` if *offsets* is empty.
    """
    if not offsets:
        return None
    return min(offsets, key=lambda o: o.distance_px)


def draw_crosshair(
    image: np.ndarray,
    color: tuple[int, int, int] = CROSSHAIR_COLOR,
    radius: int = CROSSHAIR_RADIUS,
    thickness: int = CROSSHAIR_THICKNESS,
) -> np.ndarray:
    """Draw a crosshair at the centre of *image*.

    Args:
        image: BGR ``uint8`` image array with shape ``(H, W, 3)``.
        color: BGR line colour.
        radius: Half-length of each crosshair arm in pixels.
        thickness: Line thickness in pixels.

    Returns:
        Copy of *image* with the crosshair drawn.

    Raises:
        TypeError: If *image* is not a ``np.ndarray``.
        ValueError: If *image* is not a 3-channel BGR array.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(f"Expected np.ndarray, got {type(image).__name__}")
    if image.ndim != 3 or image.shape[2] != 3:
        raise ValueError(f"Expected 3-channel BGR image (H, W, 3), got shape {image.shape}")

    out: np.ndarray = image.copy()
    h, w = out.shape[:2]
    cx, cy = w // 2, h // 2

    _draw_line(out, cx - radius, cy, cx + radius, cy, color, thickness)
    _draw_line(out, cx, cy - radius, cx, cy + radius, color, thickness)

    ring_r = max(1, radius // 2)
    steps = max(16, ring_r * 8)
    angles = np.linspace(0.0, 2.0 * np.pi, steps, endpoint=False)
    xs = (cx + ring_r * np.cos(angles)).astype(int)
    ys = (cy + ring_r * np.sin(angles)).astype(int)
    valid = (xs >= 0) & (xs < w) & (ys >= 0) & (ys < h)
    out[ys[valid], xs[valid]] = color

    return out


def draw_target_line(
    image: np.ndarray,
    offset: TargetOffset,
    color: tuple[int, int, int] = (0, 0, 255),
    thickness: int = 1,
) -> np.ndarray:
    """Draw a line from the image centre to the target detection centre.

    Args:
        image: BGR ``uint8`` image array.
        offset: The :class:`TargetOffset` whose detection centre to point at.
        color: BGR line colour.
        thickness: Line thickness in pixels.

    Returns:
        Copy of *image* with the line drawn.

    Raises:
        TypeError: If *image* is not a ``np.ndarray``.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(f"Expected np.ndarray, got {type(image).__name__}")

    out: np.ndarray = image.copy()
    h, w = out.shape[:2]
    cx, cy = w // 2, h // 2

    x1, y1, x2, y2 = offset.detection.bbox
    tx = int((x1 + x2) / 2)
    ty = int((y1 + y2) / 2)

    _draw_line(out, cx, cy, tx, ty, color, thickness)
    return out


def _draw_line(
    image: np.ndarray,
    x0: int,
    y0: int,
    x1: int,
    y1: int,
    color: tuple[int, int, int],
    thickness: int,
) -> None:
    """Draw a simple clipped line on an image in-place using linear interpolation."""
    h, w = image.shape[:2]
    steps = int(max(abs(x1 - x0), abs(y1 - y0), 1))
    t = max(1, thickness)
    for i in range(steps + 1):
        x = round(x0 + (x1 - x0) * i / steps)
        y = round(y0 + (y1 - y0) * i / steps)
        if 0 <= x < w and 0 <= y < h:
            y0c = max(0, y - t // 2)
            y1c = min(h, y + (t + 1) // 2)
            x0c = max(0, x - t // 2)
            x1c = min(w, x + (t + 1) // 2)
            image[y0c:y1c, x0c:x1c] = color
