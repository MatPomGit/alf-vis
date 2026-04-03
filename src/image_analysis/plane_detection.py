"""Flat surface (plane) detection in 3-D point clouds.

Detects planar surfaces such as floors, walls, tables, and ceilings in 3-D
space using the RANSAC (Random Sample Consensus) algorithm.

The module provides both a pure-NumPy RANSAC implementation and a thin wrapper
around the Open3D plane-segmentation function for higher performance.

Plane representation
---------------------
A plane is described by its **normal equation**: ``ax + by + cz + d = 0``,
stored in :class:`Plane3D`.

Plane orientation
-----------------
* **Horizontal** - normal vector nearly parallel to the world Z-axis
  (``|n · [0,0,1]| > cos(angle_threshold)``).  Corresponds to floors,
  table tops, and ceilings.
* **Vertical** - normal vector nearly perpendicular to the world Z-axis.
  Corresponds to walls, doors, and large panels.

Implementation notes:
    - Pure-NumPy RANSAC is always available (no extra dependency).
    - Open3D-based segmentation: ``pip install open3d>=0.17``
    - For real-time use, call ``segment_plane_open3d`` which is significantly
      faster than the NumPy reference implementation.
    - Apply the detector iteratively (removing inliers after each detection)
      to find multiple planes in one scene.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import numpy as np

logger = logging.getLogger(__name__)

# RANSAC defaults.
RANSAC_DISTANCE_THRESHOLD_M: float = 0.02  # 2 cm inlier tolerance
RANSAC_NUM_ITERATIONS: int = 1000
RANSAC_MIN_INLIER_RATIO: float = 0.05  # at least 5 % of points

# Angle threshold for horizontal / vertical classification (degrees).
HORIZONTAL_ANGLE_DEG: float = 20.0
VERTICAL_ANGLE_DEG: float = 20.0


@dataclass
class Plane3D:
    """A detected planar surface.

    Attributes:
        normal: Unit normal vector ``(a, b, c)`` of the plane equation
            ``ax + by + cz + d = 0``, dtype ``float64``.
        d: Plane offset term in the equation ``ax + by + cz + d = 0``.
        inlier_indices: Indices into the source point cloud that are
            classified as inliers of this plane.
        inlier_ratio: Fraction of the source points that are inliers.
        centroid: Mean position ``(x, y, z)`` of the inlier points,
            dtype ``float64``.
    """

    normal: np.ndarray  # shape (3,), float64
    d: float
    inlier_indices: np.ndarray = field(default_factory=lambda: np.empty(0, dtype=np.int64))
    inlier_ratio: float = 0.0
    centroid: np.ndarray = field(default_factory=lambda: np.zeros(3, dtype=np.float64))

    @property
    def is_horizontal(self) -> bool:
        """Return ``True`` if the plane is approximately horizontal.

        A plane is horizontal when its normal is nearly parallel to the
        world Z-axis (up direction).  Uses :data:`HORIZONTAL_ANGLE_DEG` as
        the maximum deviation threshold.
        """
        cos_thresh = float(np.cos(np.radians(HORIZONTAL_ANGLE_DEG)))
        return float(abs(self.normal[2])) >= cos_thresh

    @property
    def is_vertical(self) -> bool:
        """Return ``True`` if the plane is approximately vertical.

        A plane is vertical when its normal is nearly perpendicular to the
        world Z-axis.  Uses :data:`VERTICAL_ANGLE_DEG` as the maximum
        deviation threshold.
        """
        cos_thresh = float(np.cos(np.radians(90.0 - VERTICAL_ANGLE_DEG)))
        return float(abs(self.normal[2])) <= cos_thresh


def fit_plane_ransac(
    points: np.ndarray,
    distance_threshold_m: float = RANSAC_DISTANCE_THRESHOLD_M,
    num_iterations: int = RANSAC_NUM_ITERATIONS,
    min_inlier_ratio: float = RANSAC_MIN_INLIER_RATIO,
    rng_seed: int | None = None,
) -> Plane3D | None:
    """Fit a plane to *points* using RANSAC.

    Pure-NumPy reference implementation.  For large point clouds, prefer
    :func:`segment_plane_open3d`.

    Args:
        points: 3-D point cloud array of shape ``(N, 3)``, dtype ``float32``
            or ``float64``.
        distance_threshold_m: Maximum point-to-plane distance (metres) for a
            point to be considered an inlier.
        num_iterations: Number of RANSAC iterations.
        min_inlier_ratio: Minimum inlier fraction required to accept a plane.
        rng_seed: Optional seed for reproducible results.

    Returns:
        :class:`Plane3D` with the best-fit plane, or ``None`` if no plane
        with sufficient inliers was found.

    Raises:
        TypeError: If *points* is not a ``np.ndarray``.
        ValueError: If *points* does not have shape ``(N, 3)``.
    """
    if not isinstance(points, np.ndarray):
        raise TypeError(f"Expected np.ndarray, got {type(points).__name__}")
    if points.ndim != 2 or points.shape[1] != 3:
        raise ValueError(f"points must have shape (N, 3), got {points.shape}")
    if len(points) < 3:
        logger.debug("Too few points for plane fitting (%d).", len(points))
        return None

    rng = np.random.default_rng(rng_seed)
    n_points = len(points)
    best_inliers = np.empty(0, dtype=np.int64)

    for _ in range(num_iterations):
        sample_idx = rng.choice(n_points, size=3, replace=False)
        p0, p1, p2 = points[sample_idx].astype(np.float64)

        v1 = p1 - p0
        v2 = p2 - p0
        normal = np.cross(v1, v2)
        norm_len = np.linalg.norm(normal)
        if norm_len < 1e-9:
            continue
        normal = normal / norm_len
        d = -float(np.dot(normal, p0))

        distances = np.abs(points.astype(np.float64) @ normal + d)
        inliers = np.where(distances < distance_threshold_m)[0]

        if len(inliers) > len(best_inliers):
            best_inliers = inliers

    if len(best_inliers) < min_inlier_ratio * n_points:
        logger.debug(
            "RANSAC found only %d inliers (%.1f%% < %.1f%% threshold).",
            len(best_inliers),
            100.0 * len(best_inliers) / n_points,
            100.0 * min_inlier_ratio,
        )
        return None

    # Refit plane to all inliers for better accuracy.
    inlier_pts = points[best_inliers].astype(np.float64)
    centroid = inlier_pts.mean(axis=0)
    _, _, vh = np.linalg.svd(inlier_pts - centroid)
    refined_normal = vh[-1]
    refined_d = -float(np.dot(refined_normal, centroid))

    logger.debug(
        "RANSAC plane found: normal=%s, d=%.4f, inliers=%d/%d.",
        refined_normal.round(3),
        refined_d,
        len(best_inliers),
        n_points,
    )
    return Plane3D(
        normal=refined_normal,
        d=refined_d,
        inlier_indices=best_inliers,
        inlier_ratio=float(len(best_inliers)) / n_points,
        centroid=centroid,
    )


def segment_plane_open3d(
    points: np.ndarray,
    distance_threshold_m: float = RANSAC_DISTANCE_THRESHOLD_M,
    num_iterations: int = RANSAC_NUM_ITERATIONS,
) -> Plane3D | None:
    """Fit a plane using Open3D's optimised RANSAC implementation.

    Requires the ``open3d`` package::

        pip install open3d>=0.17

    Args:
        points: 3-D point cloud array of shape ``(N, 3)``.
        distance_threshold_m: Inlier distance threshold in metres.
        num_iterations: Maximum number of RANSAC iterations.

    Returns:
        :class:`Plane3D`, or ``None`` if Open3D cannot fit a plane.

    Raises:
        ImportError: If ``open3d`` is not installed.
        TypeError: If *points* is not a ``np.ndarray``.
        ValueError: If *points* does not have shape ``(N, 3)``.
    """
    if not isinstance(points, np.ndarray):
        raise TypeError(f"Expected np.ndarray, got {type(points).__name__}")
    if points.ndim != 2 or points.shape[1] != 3:
        raise ValueError(f"points must have shape (N, 3), got {points.shape}")

    try:
        import open3d as o3d
    except ImportError as exc:
        raise ImportError(
            "segment_plane_open3d requires 'open3d'. Install it with: pip install open3d"
        ) from exc

    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(points.astype(np.float64))

    plane_model, inlier_idx = pcd.segment_plane(
        distance_threshold=distance_threshold_m,
        ransac_n=3,
        num_iterations=num_iterations,
    )
    a, b, c, d = plane_model
    normal = np.array([a, b, c], dtype=np.float64)
    inlier_pts = points[inlier_idx]

    return Plane3D(
        normal=normal,
        d=float(d),
        inlier_indices=np.array(inlier_idx, dtype=np.int64),
        inlier_ratio=float(len(inlier_idx)) / max(len(points), 1),
        centroid=inlier_pts.mean(axis=0).astype(np.float64),
    )


def detect_multiple_planes(
    points: np.ndarray,
    max_planes: int = 5,
    distance_threshold_m: float = RANSAC_DISTANCE_THRESHOLD_M,
    num_iterations: int = RANSAC_NUM_ITERATIONS,
    min_inlier_ratio: float = RANSAC_MIN_INLIER_RATIO,
) -> list[Plane3D]:
    """Iteratively detect multiple planes by removing inliers after each fit.

    Args:
        points: 3-D point cloud of shape ``(N, 3)``.
        max_planes: Maximum number of planes to extract.
        distance_threshold_m: Inlier distance threshold in metres.
        num_iterations: RANSAC iterations per plane.
        min_inlier_ratio: Minimum inlier ratio to accept a plane.

    Returns:
        List of detected :class:`Plane3D` objects (up to *max_planes*).

    Raises:
        TypeError: If *points* is not a ``np.ndarray``.
        ValueError: If *points* does not have shape ``(N, 3)``.
    """
    if not isinstance(points, np.ndarray):
        raise TypeError(f"Expected np.ndarray, got {type(points).__name__}")
    if points.ndim != 2 or points.shape[1] != 3:
        raise ValueError(f"points must have shape (N, 3), got {points.shape}")

    remaining = points.copy()
    original_indices = np.arange(len(points))
    planes: list[Plane3D] = []

    for _ in range(max_planes):
        if len(remaining) < 3:
            break
        plane = fit_plane_ransac(
            remaining,
            distance_threshold_m=distance_threshold_m,
            num_iterations=num_iterations,
            min_inlier_ratio=min_inlier_ratio,
        )
        if plane is None:
            break

        # Map local inlier indices back to original point cloud indices.
        global_inliers = original_indices[plane.inlier_indices]
        planes.append(
            Plane3D(
                normal=plane.normal,
                d=plane.d,
                inlier_indices=global_inliers,
                inlier_ratio=plane.inlier_ratio,
                centroid=plane.centroid,
            )
        )

        # Remove inliers from the remaining set.
        mask = np.ones(len(remaining), dtype=bool)
        mask[plane.inlier_indices] = False
        original_indices = original_indices[mask]
        remaining = remaining[mask]

    logger.debug("Detected %d planes.", len(planes))
    return planes
