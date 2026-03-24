"""Visual marker detection - AprilTag, ArUco, CCTag, and QR code.

Detects fiducial markers commonly used in robotics for pose estimation,
navigation, and environment mapping.

Supported marker families
--------------------------
* **ArUco** - built into ``opencv-contrib-python``; the fastest option.
* **AprilTag** - better detection in low light / high motion blur;
  requires the ``pupil-apriltags`` package.
* **CCTag** - circular coded tags; robust to heavy blur and partial occlusion;
  requires the ``cctag`` Python bindings or the ROS ``cctag_ros`` node.
* **QR code** - standard 2-D barcodes with embedded ASCII payload;
  detected via ``cv2.QRCodeDetector`` (no extra dependency).

Implementation notes:
    - ArUco: ``cv2.aruco.DetectorParameters`` + ``ArucoDetector`` (OpenCV ≥ 4.7)
    - AprilTag: ``pupil_apriltags.Detector(families="tag36h11")``
    - CCTag: ``cctag.CCTagDetector()`` - wrap the C++ CLI if bindings are
      unavailable.
    - QR: ``cv2.QRCodeDetector().detectAndDecodeMulti(image)``
    - All detectors return :class:`MarkerDetection` objects for a uniform API.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum, auto

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class MarkerType(Enum):
    """Supported visual marker families."""

    ARUCO = auto()
    APRIL_TAG = auto()
    CCTAG = auto()
    QR_CODE = auto()


@dataclass(frozen=True)
class MarkerDetection:
    """A single detected visual marker.

    Attributes:
        marker_type: Family of the detected marker.
        marker_id: Numeric identifier encoded in the marker.  For QR codes,
            this is ``-1``; use :attr:`payload` instead.
        corners: Corner points of the marker as shape ``(4, 2)`` float32 array
            in pixel coordinates, ordered top-left → top-right → bottom-right
            → bottom-left.
        payload: Decoded string payload (only for QR codes; ``""`` otherwise).
    """

    marker_type: MarkerType
    marker_id: int
    corners: np.ndarray  # shape (4, 2), float32
    payload: str = ""


# ---------------------------------------------------------------------------
# ArUco detection
# ---------------------------------------------------------------------------

# Default dictionary used on Unitree G1 EDU.
ARUCO_DICT_ID: int = cv2.aruco.DICT_4X4_50


def detect_aruco_markers(
    image: np.ndarray,
    dictionary_id: int = ARUCO_DICT_ID,
) -> list[MarkerDetection]:
    """Detect ArUco markers in *image*.

    Uses the OpenCV ArUco module (requires ``opencv-contrib-python``).

    Args:
        image: BGR ``uint8`` image array with shape ``(H, W, 3)``.
        dictionary_id: ArUco dictionary identifier constant, e.g.
            ``cv2.aruco.DICT_4X4_50`` or ``cv2.aruco.DICT_6X6_250``.

    Returns:
        List of :class:`MarkerDetection` instances sorted by *marker_id*.

    Raises:
        TypeError: If *image* is not a ``np.ndarray``.
        ValueError: If *image* is not a 3-channel BGR array.
    """
    _validate_bgr(image)

    aruco_dict = cv2.aruco.getPredefinedDictionary(dictionary_id)
    params = cv2.aruco.DetectorParameters()
    detector = cv2.aruco.ArucoDetector(aruco_dict, params)

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    corners_list, ids, _ = detector.detectMarkers(gray)

    detections: list[MarkerDetection] = []
    if ids is not None:
        for corners, marker_id in zip(corners_list, ids.flatten(), strict=True):
            detections.append(
                MarkerDetection(
                    marker_type=MarkerType.ARUCO,
                    marker_id=int(marker_id),
                    corners=corners.reshape(4, 2),
                )
            )

    detections.sort(key=lambda d: d.marker_id)
    logger.debug("Detected %d ArUco markers.", len(detections))
    return detections


# ---------------------------------------------------------------------------
# AprilTag detection
# ---------------------------------------------------------------------------


def detect_apriltag_markers(
    image: np.ndarray,
    families: str = "tag36h11",
) -> list[MarkerDetection]:
    """Detect AprilTag markers in *image*.

    Requires the ``pupil-apriltags`` package::

        pip install pupil-apriltags

    Args:
        image: BGR ``uint8`` image array with shape ``(H, W, 3)``.
        families: Space-separated AprilTag family names, e.g.
            ``"tag36h11 tag25h9"``.

    Returns:
        List of :class:`MarkerDetection` instances sorted by *marker_id*.

    Raises:
        TypeError: If *image* is not a ``np.ndarray``.
        ValueError: If *image* is not a 3-channel BGR array.
        ImportError: If ``pupil_apriltags`` is not installed.
    """
    _validate_bgr(image)

    try:
        import pupil_apriltags as apriltag  # type: ignore[import-untyped]
    except ImportError as exc:
        raise ImportError(
            "AprilTag detection requires 'pupil-apriltags'. "
            "Install it with: pip install pupil-apriltags"
        ) from exc

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    detector = apriltag.Detector(families=families)
    results = detector.detect(gray)

    detections: list[MarkerDetection] = [
        MarkerDetection(
            marker_type=MarkerType.APRIL_TAG,
            marker_id=r.tag_id,
            corners=np.array(r.corners, dtype=np.float32),
        )
        for r in results
    ]
    detections.sort(key=lambda d: d.marker_id)
    logger.debug("Detected %d AprilTag markers.", len(detections))
    return detections


# ---------------------------------------------------------------------------
# CCTag detection
# ---------------------------------------------------------------------------


def detect_cctag_markers(image: np.ndarray) -> list[MarkerDetection]:
    """Detect CCTag circular coded markers in *image*.

    CCTag markers are concentric circular patterns robust to blur and
    partial occlusion.  Detection requires the ``cctag`` C++ library with
    optional Python bindings.

    Args:
        image: BGR ``uint8`` image array with shape ``(H, W, 3)``.

    Returns:
        List of :class:`MarkerDetection` instances sorted by *marker_id*.

    Raises:
        TypeError: If *image* is not a ``np.ndarray``.
        ValueError: If *image* is not a 3-channel BGR array.
        ImportError: If the ``cctag`` Python bindings are not available.

    Note:
        TODO(#markers): Integrate with the ``cctag`` C++ library.  As a
        fallback, call the CLI tool ``cctag_detection`` and parse its output.
    """
    _validate_bgr(image)

    try:
        import cctag  # type: ignore[import-untyped]
    except ImportError as exc:
        raise ImportError(
            "CCTag detection requires the 'cctag' Python bindings. "
            "See https://github.com/alicevision/CCTag for build instructions."
        ) from exc

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # TODO(#markers): Adapt the API call to the installed cctag version.
    results = cctag.detect(gray)  # type: ignore[attr-defined]

    detections: list[MarkerDetection] = [
        MarkerDetection(
            marker_type=MarkerType.CCTAG,
            marker_id=r.id,
            corners=np.array(r.points, dtype=np.float32),
        )
        for r in results
    ]
    detections.sort(key=lambda d: d.marker_id)
    logger.debug("Detected %d CCTag markers.", len(detections))
    return detections


# ---------------------------------------------------------------------------
# QR code detection
# ---------------------------------------------------------------------------


def detect_qr_codes(image: np.ndarray) -> list[MarkerDetection]:
    """Detect and decode QR codes in *image*.

    Uses the built-in ``cv2.QRCodeDetector`` - no extra dependency required.

    Args:
        image: BGR ``uint8`` image array with shape ``(H, W, 3)``.

    Returns:
        List of :class:`MarkerDetection` instances.  The decoded ASCII payload
        is stored in :attr:`MarkerDetection.payload`; :attr:`marker_id` is
        set to ``-1`` for all QR detections.

    Raises:
        TypeError: If *image* is not a ``np.ndarray``.
        ValueError: If *image* is not a 3-channel BGR array.
    """
    _validate_bgr(image)

    detector = cv2.QRCodeDetector()
    ok, decoded_list, points_array, _ = detector.detectAndDecodeMulti(image)

    detections: list[MarkerDetection] = []
    if ok and points_array is not None:
        for decoded, pts in zip(decoded_list, points_array, strict=True):
            if pts is None:
                continue
            detections.append(
                MarkerDetection(
                    marker_type=MarkerType.QR_CODE,
                    marker_id=-1,
                    corners=pts.astype(np.float32).reshape(4, 2),
                    payload=decoded,
                )
            )

    logger.debug("Detected %d QR codes.", len(detections))
    return detections


# ---------------------------------------------------------------------------
# Combined detection
# ---------------------------------------------------------------------------


def detect_all_markers(
    image: np.ndarray,
    *,
    aruco: bool = True,
    apriltag: bool = False,
    cctag: bool = False,
    qr: bool = True,
) -> list[MarkerDetection]:
    """Run all enabled marker detectors and return merged results.

    Args:
        image: BGR ``uint8`` image array with shape ``(H, W, 3)``.
        aruco: Enable ArUco detection.
        apriltag: Enable AprilTag detection (requires ``pupil-apriltags``).
        cctag: Enable CCTag detection (requires ``cctag`` bindings).
        qr: Enable QR code detection.

    Returns:
        Combined list of :class:`MarkerDetection` instances from all enabled
        detectors.

    Raises:
        TypeError: If *image* is not a ``np.ndarray``.
        ValueError: If *image* is not a 3-channel BGR array.
    """
    _validate_bgr(image)

    results: list[MarkerDetection] = []

    if aruco:
        results.extend(detect_aruco_markers(image))
    if apriltag:
        results.extend(detect_apriltag_markers(image))
    if cctag:
        results.extend(detect_cctag_markers(image))
    if qr:
        results.extend(detect_qr_codes(image))

    logger.debug("Total markers detected: %d.", len(results))
    return results


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
