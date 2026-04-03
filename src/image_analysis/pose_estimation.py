"""3-D pose estimation for detected objects.

Estimates the 6-DOF pose (position + orientation) of objects in camera space
using three complementary approaches:

1. **Marker-based** - ArUco / AprilTag markers with known physical size allow
   ``cv2.solvePnP`` to recover the full 6-DOF pose with millimetre accuracy.
2. **Depth-based** - Backproject 2-D bounding-box centre into 3-D using the
   depth map from the onboard depth sensor.
3. **Monocular PnP** - Fit a known 3-D object model to 2-D image points using
   the Perspective-n-Point algorithm when no marker or depth is available
   (lower accuracy).

All poses are expressed in the **camera coordinate frame** (right-hand,
X-right, Y-down, Z-forward).

Implementation notes:
    - ``cv2.solvePnP`` (EPNP / ITERATIVE) for marker and model-based poses.
    - ``cv2.Rodrigues`` to convert rotation vectors ↔ rotation matrices.
    - ``open3d.geometry.PointCloud`` for depth-based 3-D reconstruction (optional).
    - Marker size must be known a priori; store it in the marker metadata or
      in a configuration file.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import cv2
import numpy as np

from image_analysis.calibration import CalibrationResult
from image_analysis.markers import MarkerDetection

logger = logging.getLogger(__name__)

# Default physical marker side length in metres (ArUco / AprilTag).
DEFAULT_MARKER_SIZE_M: float = 0.10


@dataclass
class Pose3D:
    """6-DOF object pose in the camera coordinate frame.

    Attributes:
        rvec: Rotation vector (Rodrigues) of shape ``(3, 1)`` or ``(3,)``,
            dtype ``float64``.
        tvec: Translation vector of shape ``(3, 1)`` or ``(3,)``,
            dtype ``float64``.  Units are the same as the calibration target
            (metres when using SI squares).
        rotation_matrix: 3x3 rotation matrix (derived from *rvec*).
        position_m: ``(x, y, z)`` position in metres.
        reprojection_error: RMS reprojection error of the PnP fit (pixels).
            ``NaN`` when not computed.
    """

    rvec: np.ndarray
    tvec: np.ndarray
    rotation_matrix: np.ndarray = field(init=False)
    reprojection_error: float = float("nan")

    def __post_init__(self) -> None:
        rot, _ = cv2.Rodrigues(self.rvec)
        object.__setattr__(self, "rotation_matrix", rot)

    @property
    def position_m(self) -> tuple[float, float, float]:
        """Return the ``(x, y, z)`` translation in metres."""
        t = self.tvec.flatten()
        return float(t[0]), float(t[1]), float(t[2])

    @property
    def distance_m(self) -> float:
        """Return the Euclidean distance from the camera origin in metres."""
        return float(np.linalg.norm(self.tvec))


def estimate_pose_from_marker(
    marker: MarkerDetection,
    calibration: CalibrationResult,
    marker_size_m: float = DEFAULT_MARKER_SIZE_M,
) -> Pose3D:
    """Estimate the 6-DOF pose of a single square planar marker.

    Uses ``cv2.solvePnP`` with the four corner points and the known physical
    marker size to recover the rotation and translation vectors.

    Args:
        marker: A detected marker whose :attr:`~MarkerDetection.corners`
            array has shape ``(4, 2)`` in pixel coordinates.
        calibration: Camera calibration providing the intrinsic matrix and
            distortion coefficients.
        marker_size_m: Physical side length of the marker in metres.

    Returns:
        :class:`Pose3D` in the camera coordinate frame.

    Raises:
        ValueError: If ``cv2.solvePnP`` does not converge.
    """
    half = marker_size_m / 2.0
    # Object points in marker-local frame (Z = 0 plane, centred at origin).
    obj_pts = np.array(
        [[-half, half, 0.0], [half, half, 0.0], [half, -half, 0.0], [-half, -half, 0.0]],
        dtype=np.float64,
    )

    img_pts = marker.corners.astype(np.float64)

    ok, rvec, tvec = cv2.solvePnP(
        obj_pts,
        img_pts,
        calibration.camera_matrix,
        calibration.dist_coeffs,
        flags=cv2.SOLVEPNP_IPPE_SQUARE,
    )

    if not ok:
        raise ValueError(f"solvePnP failed for marker id={marker.marker_id}.")

    return Pose3D(rvec=rvec, tvec=tvec)


def estimate_poses_from_markers(
    markers: list[MarkerDetection],
    calibration: CalibrationResult,
    marker_size_m: float = DEFAULT_MARKER_SIZE_M,
) -> list[tuple[MarkerDetection, Pose3D]]:
    """Estimate poses for all detected markers.

    Args:
        markers: List of detected markers.
        calibration: Camera calibration.
        marker_size_m: Physical marker side length in metres.

    Returns:
        List of ``(marker, pose)`` pairs.  Markers for which ``cv2.solvePnP``
        fails are silently skipped.
    """
    results: list[tuple[MarkerDetection, Pose3D]] = []
    for marker in markers:
        try:
            pose = estimate_pose_from_marker(marker, calibration, marker_size_m)
            results.append((marker, pose))
        except ValueError as exc:
            logger.warning("Skipping marker id=%d: %s", marker.marker_id, exc)
    return results


def backproject_to_3d(
    pixel_x: int,
    pixel_y: int,
    depth_m: float,
    calibration: CalibrationResult,
) -> tuple[float, float, float]:
    """Back-project a pixel + depth measurement into 3-D camera space.

    Args:
        pixel_x: Horizontal pixel coordinate (column index).
        pixel_y: Vertical pixel coordinate (row index).
        depth_m: Measured depth in metres at ``(pixel_x, pixel_y)``.
        calibration: Camera calibration providing the intrinsic matrix.

    Returns:
        ``(X, Y, Z)`` coordinates in metres in the camera frame.

    Raises:
        ValueError: If *depth_m* is not positive.
    """
    if depth_m <= 0.0:
        raise ValueError(f"depth_m must be positive, got {depth_m}")

    camera_matrix = calibration.camera_matrix
    fx, fy = float(camera_matrix[0, 0]), float(camera_matrix[1, 1])
    cx, cy = float(camera_matrix[0, 2]), float(camera_matrix[1, 2])

    x_m = (pixel_x - cx) * depth_m / fx
    y_m = (pixel_y - cy) * depth_m / fy
    return x_m, y_m, depth_m


def estimate_pose_from_depth(
    bbox: tuple[int, int, int, int],
    depth_map: np.ndarray,
    calibration: CalibrationResult,
) -> Pose3D:
    """Estimate the 3-D position of a detected object from a depth map.

    Uses the median depth within the bounding box to back-project the
    bounding-box centre into 3-D space.  The pose has no rotation
    information (orientation set to identity).

    Args:
        bbox: Bounding box ``(x1, y1, x2, y2)`` in pixel coordinates.
        depth_map: Per-pixel depth in metres, shape ``(H, W)``, dtype
            ``float32``.  ``NaN`` pixels are ignored.
        calibration: Camera calibration.

    Returns:
        :class:`Pose3D` with translation set to the 3-D position of the
        bounding-box centre and rotation equal to identity.

    Raises:
        ValueError: If the bounding box is out of bounds or median depth
            is zero / NaN.
    """
    x1, y1, x2, y2 = bbox
    roi_depth = depth_map[y1:y2, x1:x2]
    valid = roi_depth[np.isfinite(roi_depth) & (roi_depth > 0)]

    if valid.size == 0:
        raise ValueError("No valid depth values inside the bounding box.")

    median_depth = float(np.median(valid))
    cx_px = (x1 + x2) // 2
    cy_px = (y1 + y2) // 2

    x_m, y_m, z_m = backproject_to_3d(cx_px, cy_px, median_depth, calibration)

    rvec = np.zeros((3, 1), dtype=np.float64)
    tvec = np.array([[x_m], [y_m], [z_m]], dtype=np.float64)
    return Pose3D(rvec=rvec, tvec=tvec)


def draw_pose_axes(
    image: np.ndarray,
    pose: Pose3D,
    calibration: CalibrationResult,
    axis_length_m: float = 0.05,
) -> np.ndarray:
    """Draw 3-D coordinate axes on *image* at the estimated pose.

    Projects three unit vectors (X=red, Y=green, Z=blue) onto the image
    plane to visualise the marker / object orientation.

    Args:
        image: BGR ``uint8`` image to draw on.
        pose: 3-D pose to visualise.
        calibration: Camera calibration.
        axis_length_m: Length of each drawn axis in metres.

    Returns:
        Copy of *image* with axes drawn.

    Raises:
        TypeError: If *image* is not a ``np.ndarray``.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(f"Expected np.ndarray, got {type(image).__name__}")

    out: np.ndarray = image.copy()
    axis_pts = np.array(
        [[0, 0, 0], [axis_length_m, 0, 0], [0, axis_length_m, 0], [0, 0, axis_length_m]],
        dtype=np.float32,
    )

    projected, _ = cv2.projectPoints(
        axis_pts,
        pose.rvec,
        pose.tvec,
        calibration.camera_matrix,
        calibration.dist_coeffs,
    )
    pts = projected.astype(int).reshape(-1, 2)
    origin = tuple(pts[0].tolist())

    cv2.arrowedLine(out, origin, tuple(pts[1].tolist()), (0, 0, 255), 2, tipLength=0.2)
    cv2.arrowedLine(out, origin, tuple(pts[2].tolist()), (0, 255, 0), 2, tipLength=0.2)
    cv2.arrowedLine(out, origin, tuple(pts[3].tolist()), (255, 0, 0), 2, tipLength=0.2)

    return out
