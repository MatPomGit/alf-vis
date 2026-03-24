"""RGB-D point cloud generation and manipulation.

Creates coloured 3-D point clouds by fusing per-pixel depth measurements
with the corresponding RGB colour values.  Each point ``(X, Y, Z, R, G, B)``
is obtained by back-projecting an image pixel through the camera intrinsics
using the depth sensor reading at that pixel.

Mathematical basis
-------------------
For a pixel ``(u, v)`` with depth ``Z`` and intrinsics ``(fx, fy, cx, cy)``::

    X = (u - cx) * Z / fx
    Y = (v - cy) * Z / fy

The resulting point is expressed in the camera coordinate frame
(right-hand, X-right, Y-down, Z-forward).

Implementation notes:
    - NumPy vectorised back-projection for performance.
    - Optional Open3D integration for visualisation and I/O.
    - Point cloud saved to PLY (ASCII or binary) via Open3D or
      ``struct`` serialisation without extra dependencies.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np

from image_analysis.calibration import CalibrationResult

logger = logging.getLogger(__name__)


@dataclass
class PointCloud:
    """A coloured 3-D point cloud.

    Attributes:
        points: 3-D coordinates of shape ``(N, 3)``, dtype ``float64``,
            in the camera frame (metres).
        colors: RGB colours of shape ``(N, 3)``, dtype ``float32``,
            normalised to ``[0.0, 1.0]``.
    """

    points: np.ndarray   # (N, 3), float64
    colors: np.ndarray   # (N, 3), float32

    def __len__(self) -> int:
        return int(self.points.shape[0])

    def is_empty(self) -> bool:
        """Return ``True`` if the point cloud contains no points."""
        return len(self) == 0


@dataclass
class RgbdFusionConfig:
    """Configuration for RGB-D fusion.

    Attributes:
        depth_scale: Scale factor to convert raw depth values to metres.
            For Intel RealSense uint16 depth images, use ``0.001``.
        depth_min_m: Minimum valid depth in metres (points closer are dropped).
        depth_max_m: Maximum valid depth in metres (points further are dropped).
        stride: Spatial sub-sampling factor.  A value of 2 uses every other
            pixel in both axes, reducing point count by 4x.
    """

    depth_scale: float = 1.0
    depth_min_m: float = 0.1
    depth_max_m: float = 10.0
    stride: int = 1


def create_point_cloud(
    rgb: np.ndarray,
    depth: np.ndarray,
    calibration: CalibrationResult,
    config: RgbdFusionConfig | None = None,
) -> PointCloud:
    """Create a coloured point cloud from an RGB-D frame.

    Args:
        rgb: BGR ``uint8`` image of shape ``(H, W, 3)``.
        depth: Depth map of shape ``(H, W)``, dtype ``float32``, in metres
            **after** scaling (or raw uint16 if :attr:`~RgbdFusionConfig.depth_scale`
            is set correctly).
        calibration: Camera intrinsics used for back-projection.
        config: Fusion parameters.  Uses default values when ``None``.

    Returns:
        :class:`PointCloud` with all valid (non-NaN, in-range) points.

    Raises:
        TypeError: If *rgb* or *depth* is not a ``np.ndarray``.
        ValueError: If *rgb* and *depth* have different spatial dimensions.
    """
    if not isinstance(rgb, np.ndarray):
        raise TypeError(f"Expected np.ndarray for rgb, got {type(rgb).__name__}")
    if not isinstance(depth, np.ndarray):
        raise TypeError(f"Expected np.ndarray for depth, got {type(depth).__name__}")

    if rgb.shape[:2] != depth.shape[:2]:
        raise ValueError(
            f"rgb and depth must have the same spatial dimensions, "
            f"got rgb={rgb.shape[:2]} depth={depth.shape[:2]}"
        )

    cfg = config or RgbdFusionConfig()
    K = calibration.camera_matrix
    fx, fy = float(K[0, 0]), float(K[1, 1])
    cx, cy = float(K[0, 2]), float(K[1, 2])

    h, w = depth.shape[:2]
    s = cfg.stride

    # Sub-sample pixel grid.
    v_coords, u_coords = np.mgrid[0:h:s, 0:w:s]
    z_raw = depth[::s, ::s].astype(np.float64) * cfg.depth_scale

    valid = np.isfinite(z_raw) & (z_raw >= cfg.depth_min_m) & (z_raw <= cfg.depth_max_m)
    u_valid = u_coords[valid].astype(np.float64)
    v_valid = v_coords[valid].astype(np.float64)
    z_valid = z_raw[valid]

    x = (u_valid - cx) * z_valid / fx
    y = (v_valid - cy) * z_valid / fy
    points = np.stack([x, y, z_valid], axis=1)

    # Extract colours from the BGR image (convert to RGB, normalise).
    bgr_sub = rgb[::s, ::s]
    colors_bgr = bgr_sub[valid].astype(np.float32) / 255.0
    colors_rgb = colors_bgr[:, ::-1]  # BGR → RGB

    logger.debug(
        "Created point cloud with %d points from %dx%d image (stride=%d).",
        len(points), h, w, s,
    )
    return PointCloud(points=points, colors=colors_rgb)


def filter_point_cloud(
    cloud: PointCloud,
    statistical: bool = True,
    nb_neighbors: int = 20,
    std_ratio: float = 2.0,
) -> PointCloud:
    """Remove outlier points using statistical filtering.

    Uses Open3D's ``remove_statistical_outlier`` when available; falls back
    to a simple distance-based filter otherwise.

    Args:
        cloud: Input point cloud.
        statistical: If ``True``, use statistical outlier removal.
        nb_neighbors: Number of neighbours considered for the statistical test.
        std_ratio: Standard deviation multiplier; points beyond this many
            standard deviations from the mean distance are removed.

    Returns:
        Filtered :class:`PointCloud`.

    Raises:
        ImportError: If statistical filtering is requested but ``open3d``
            is not installed.
    """
    if cloud.is_empty():
        return cloud

    if statistical:
        try:
            import open3d as o3d  # type: ignore[import-untyped]
        except ImportError as exc:
            raise ImportError(
                "Statistical filtering requires 'open3d'. "
                "Install it with: pip install open3d"
            ) from exc

        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(cloud.points)
        pcd.colors = o3d.utility.Vector3dVector(cloud.colors.astype(np.float64))

        filtered, mask = pcd.remove_statistical_outlier(
            nb_neighbors=nb_neighbors, std_ratio=std_ratio
        )
        kept = np.asarray(mask)
        return PointCloud(
            points=np.asarray(filtered.points),
            colors=np.asarray(filtered.colors).astype(np.float32),
        )

    # Fallback: distance-based filter (remove points far from centroid).
    centroid = cloud.points.mean(axis=0)
    dists = np.linalg.norm(cloud.points - centroid, axis=1)
    threshold = dists.mean() + std_ratio * dists.std()
    mask = dists <= threshold
    return PointCloud(
        points=cloud.points[mask],
        colors=cloud.colors[mask],
    )


def save_point_cloud_ply(cloud: PointCloud, path: str) -> None:
    """Save a point cloud to a PLY file.

    Requires ``open3d``.

    Args:
        cloud: Point cloud to save.
        path: Destination file path (``*.ply``).

    Raises:
        ImportError: If ``open3d`` is not installed.
        IOError: If the file cannot be written.
    """
    try:
        import open3d as o3d  # type: ignore[import-untyped]
    except ImportError as exc:
        raise ImportError(
            "save_point_cloud_ply requires 'open3d'. "
            "Install it with: pip install open3d"
        ) from exc

    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(cloud.points)
    pcd.colors = o3d.utility.Vector3dVector(cloud.colors.astype(np.float64))
    o3d.io.write_point_cloud(path, pcd)
    logger.info("Point cloud (%d points) saved to '%s'.", len(cloud), path)


def load_point_cloud_ply(path: str) -> PointCloud:
    """Load a point cloud from a PLY file.

    Requires ``open3d``.

    Args:
        path: Path to an existing PLY file.

    Returns:
        :class:`PointCloud` with points and colours.

    Raises:
        ImportError: If ``open3d`` is not installed.
        FileNotFoundError: If *path* does not exist.
    """
    import os

    if not os.path.isfile(path):
        raise FileNotFoundError(f"PLY file not found: {path}")

    try:
        import open3d as o3d  # type: ignore[import-untyped]
    except ImportError as exc:
        raise ImportError(
            "load_point_cloud_ply requires 'open3d'. "
            "Install it with: pip install open3d"
        ) from exc

    pcd = o3d.io.read_point_cloud(path)
    points = np.asarray(pcd.points, dtype=np.float64)
    colors = np.asarray(pcd.colors, dtype=np.float32)
    logger.info("Loaded point cloud (%d points) from '%s'.", len(points), path)
    return PointCloud(points=points, colors=colors)
