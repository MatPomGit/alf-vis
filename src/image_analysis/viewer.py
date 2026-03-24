"""2-D image viewer for RGB and depth streams.

Provides lightweight display utilities for monitoring the Unitree G1 EDU
camera feeds during development and debugging.  Functions are designed to
work in a standard OpenCV ``imshow`` loop and can be embedded in a ROS2
visualisation node or a standalone Python script.

Depth visualisation
-------------------
Raw depth maps are single-channel float32 arrays (metres).  Before display
they are converted to a false-colour image using a configurable colormap
(default: ``cv2.COLORMAP_JET``).  Pixels with zero or NaN depth are rendered
in black.

Implementation notes:
    - ``cv2.imshow`` / ``cv2.waitKey`` for interactive display.
    - ``cv2.imencode`` for frame serialisation (JPEG streaming to a browser).
    - For headless environments, use ``render_rgb`` / ``render_depth`` to
      obtain annotated ``np.ndarray`` images that can be saved or streamed
      without a display.
"""

from __future__ import annotations

import logging

import cv2
import numpy as np

logger = logging.getLogger(__name__)

# Default colormap for depth visualisation.
DEFAULT_DEPTH_COLORMAP: int = cv2.COLORMAP_JET

# Clamp depth range for false-colour display (metres).
DEPTH_MIN_M: float = 0.1
DEPTH_MAX_M: float = 10.0


def render_rgb(
    image: np.ndarray,
    label: str = "",
    label_color: tuple[int, int, int] = (255, 255, 255),
) -> np.ndarray:
    """Return a copy of *image* with an optional text label.

    Args:
        image: BGR ``uint8`` image array of shape ``(H, W, 3)``.
        label: Optional text overlay drawn in the top-left corner.
        label_color: BGR text colour.

    Returns:
        Annotated copy of *image*.

    Raises:
        TypeError: If *image* is not a ``np.ndarray``.
        ValueError: If *image* is not a 3-channel BGR array.
    """
    _validate_bgr(image)
    out = image.copy()
    if label:
        cv2.putText(
            out, label, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, label_color, 2
        )
    return out


def render_depth(
    depth: np.ndarray,
    depth_min_m: float = DEPTH_MIN_M,
    depth_max_m: float = DEPTH_MAX_M,
    colormap: int = DEFAULT_DEPTH_COLORMAP,
) -> np.ndarray:
    """Convert a float32 depth map to a false-colour BGR visualisation.

    Values outside ``[depth_min_m, depth_max_m]`` are clamped.  Zero and NaN
    pixels are rendered black.

    Args:
        depth: Depth map of shape ``(H, W)``, dtype ``float32``, in metres.
        depth_min_m: Minimum depth value for colour scaling.
        depth_max_m: Maximum depth value for colour scaling.
        colormap: OpenCV colormap constant (e.g. ``cv2.COLORMAP_JET``).

    Returns:
        BGR ``uint8`` false-colour image of shape ``(H, W, 3)``.

    Raises:
        TypeError: If *depth* is not a ``np.ndarray``.
        ValueError: If *depth* is not a 2-D float32 array.
    """
    if not isinstance(depth, np.ndarray):
        raise TypeError(f"Expected np.ndarray, got {type(depth).__name__}")
    if depth.ndim != 2:
        raise ValueError(f"depth must be 2-D, got {depth.ndim}-D")
    if depth.dtype != np.float32:
        raise ValueError(f"depth must be float32, got dtype={depth.dtype}")

    valid_mask = np.isfinite(depth) & (depth > 0)
    normalised = np.zeros_like(depth)
    normalised[valid_mask] = np.clip(
        (depth[valid_mask] - depth_min_m) / (depth_max_m - depth_min_m), 0.0, 1.0
    )

    uint8_depth = (normalised * 255).astype(np.uint8)
    coloured = cv2.applyColorMap(uint8_depth, colormap)
    # Black out invalid pixels.
    coloured[~valid_mask] = 0
    return coloured


def render_rgbd_side_by_side(
    rgb: np.ndarray,
    depth: np.ndarray,
    depth_min_m: float = DEPTH_MIN_M,
    depth_max_m: float = DEPTH_MAX_M,
    colormap: int = DEFAULT_DEPTH_COLORMAP,
) -> np.ndarray:
    """Combine RGB and false-colour depth into a side-by-side image.

    Both frames are resized to the same height before concatenation.

    Args:
        rgb: BGR ``uint8`` image of shape ``(H, W, 3)``.
        depth: Depth map of shape ``(H', W')``, dtype ``float32``, in metres.
        depth_min_m: Minimum depth for colour scaling.
        depth_max_m: Maximum depth for colour scaling.
        colormap: OpenCV colormap constant.

    Returns:
        BGR ``uint8`` image of shape ``(H, W + W_d, 3)`` where *W_d* is the
        width of the resized depth visualisation.

    Raises:
        TypeError: If *rgb* or *depth* is not a ``np.ndarray``.
    """
    _validate_bgr(rgb)
    depth_vis = render_depth(depth, depth_min_m, depth_max_m, colormap)

    target_h = rgb.shape[0]
    if depth_vis.shape[0] != target_h:
        scale = target_h / depth_vis.shape[0]
        new_w = int(depth_vis.shape[1] * scale)
        depth_vis = cv2.resize(depth_vis, (new_w, target_h), interpolation=cv2.INTER_LINEAR)

    return np.concatenate([rgb, depth_vis], axis=1)


def show_image(
    image: np.ndarray,
    window_name: str = "Image",
    wait_ms: int = 1,
) -> int:
    """Display *image* in an OpenCV window and return the key pressed.

    Args:
        image: BGR ``uint8`` image array.
        window_name: Title of the display window.
        wait_ms: Milliseconds to wait for a key press.  Use ``0`` to block
            indefinitely, ``1`` for continuous playback.

    Returns:
        Key code returned by ``cv2.waitKey``.  Returns ``-1`` when no key
        was pressed within *wait_ms*.

    Raises:
        TypeError: If *image* is not a ``np.ndarray``.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(f"Expected np.ndarray, got {type(image).__name__}")
    cv2.imshow(window_name, image)
    return cv2.waitKey(wait_ms) & 0xFF


def encode_jpeg(image: np.ndarray, quality: int = 80) -> bytes:
    """Encode *image* to a JPEG byte string for streaming.

    Args:
        image: BGR ``uint8`` image array.
        quality: JPEG quality (0-100).

    Returns:
        JPEG-encoded bytes.

    Raises:
        TypeError: If *image* is not a ``np.ndarray``.
        RuntimeError: If encoding fails.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(f"Expected np.ndarray, got {type(image).__name__}")
    ok, buf = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, quality])
    if not ok:
        raise RuntimeError("JPEG encoding failed.")
    return buf.tobytes()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _validate_bgr(image: np.ndarray) -> None:
    """Validate that *image* is a 3-channel BGR uint8 array."""
    if not isinstance(image, np.ndarray):
        raise TypeError(f"Expected np.ndarray, got {type(image).__name__}")
    if image.ndim != 3 or image.shape[2] != 3:
        raise ValueError(
            f"Expected 3-channel BGR image (H, W, 3), got shape {image.shape}"
        )
