"""Real-time SLAM - Simultaneous Localisation and Mapping.

Builds a 3-D map of the robot's surroundings while simultaneously tracking
its camera pose.  The module wraps third-party SLAM back-ends behind a
common interface so that the back-end can be swapped without changing the
rest of the pipeline.

Supported back-ends (choose at runtime via :attr:`SlamConfig.backend`)
----------------------------------------------------------------------
* **``"orb_slam3"``** - ORB-SLAM3 via its Python bindings.
  Repository: https://github.com/UZ-SLAMLab/ORB_SLAM3
* **``"rtabmap"``** - RTAB-Map via the ``rtabmap_ros`` ROS2 package or the
  standalone ``rtabmap`` Python bindings.
  Repository: https://github.com/introlab/rtabmap
* **``"open3d"``** - Open3D Reconstruction System (dense RGB-D SLAM).
  Works without ROS; suitable for offline processing.
  Repository: http://www.open3d.org

Implementation notes:
    - All back-ends receive synchronised RGB-D frames (:class:`SlamFrame`).
    - The output is a sparse or dense :class:`SlamMap` with keyframe poses
      and optionally a 3-D point cloud or mesh.
    - Camera trajectory is stored as a list of 4x4 transformation matrices
      in the world frame.
    - Loop-closure detection is handled internally by each back-end.
    - When running on the Unitree G1 EDU, use ``"rtabmap"`` via ROS2 for best
      integration with the robot's navigation stack.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import numpy as np

logger = logging.getLogger(__name__)

# Supported SLAM back-end identifiers.
BACKEND_ORB_SLAM3: str = "orb_slam3"
BACKEND_RTABMAP: str = "rtabmap"
BACKEND_OPEN3D: str = "open3d"

SUPPORTED_BACKENDS: tuple[str, ...] = (
    BACKEND_ORB_SLAM3,
    BACKEND_RTABMAP,
    BACKEND_OPEN3D,
)


@dataclass
class SlamConfig:
    """Configuration for the SLAM subsystem.

    Attributes:
        backend: SLAM back-end to use.  One of :data:`SUPPORTED_BACKENDS`.
        vocabulary_path: Path to the BoW vocabulary file required by
            ORB-SLAM3 (ignored for other back-ends).
        settings_path: Path to the SLAM settings YAML file.
        enable_viewer: Whether to open the built-in 3-D map viewer.
        map_save_path: If set, the map is saved to this path when
            :meth:`SlamSession.stop` is called.
    """

    backend: str = BACKEND_OPEN3D
    vocabulary_path: str = ""
    settings_path: str = ""
    enable_viewer: bool = False
    map_save_path: str = ""


@dataclass
class SlamFrame:
    """A single RGB-D frame submitted to the SLAM system.

    Attributes:
        rgb: BGR ``uint8`` image array of shape ``(H, W, 3)``.
        depth: Depth map of shape ``(H, W)``, dtype ``float32``, in metres.
        timestamp_s: Frame timestamp in seconds (monotonic clock).
    """

    rgb: np.ndarray
    depth: np.ndarray
    timestamp_s: float = 0.0


@dataclass
class SlamKeyframe:
    """A keyframe stored in the SLAM map.

    Attributes:
        frame_id: Unique keyframe index.
        pose_world: 4x4 camera-to-world transformation matrix, dtype
            ``float64``.
        timestamp_s: Capture timestamp in seconds.
    """

    frame_id: int
    pose_world: np.ndarray  # shape (4, 4), float64
    timestamp_s: float = 0.0


@dataclass
class SlamMap:
    """Snapshot of the current SLAM map state.

    Attributes:
        keyframes: List of keyframes with estimated camera poses.
        map_points: Sparse 3-D map points as ``(N, 3)`` float64 array.
            May be empty when using a dense back-end.
        trajectory: List of consecutive 4x4 camera poses (world frame).
        is_lost: ``True`` if tracking was lost in the last update.
    """

    keyframes: list[SlamKeyframe] = field(default_factory=list)
    map_points: np.ndarray = field(
        default_factory=lambda: np.empty((0, 3), dtype=np.float64)
    )
    trajectory: list[np.ndarray] = field(default_factory=list)
    is_lost: bool = False


class SlamSession:
    """Manages the lifecycle of a SLAM back-end session.

    Example::

        config = SlamConfig(backend="open3d")
        with SlamSession(config) as slam:
            for rgbd_frame in camera.stream_rgbd():
                slam_frame = SlamFrame(rgb=rgbd_frame.rgb, depth=rgbd_frame.depth)
                current_pose = slam.process_frame(slam_frame)
            slam_map = slam.get_map()

    Args:
        config: SLAM configuration.

    Raises:
        ValueError: If the configured back-end is not supported.
    """

    def __init__(self, config: SlamConfig | None = None) -> None:
        self._config = config or SlamConfig()
        self._backend_instance: object | None = None
        self._map = SlamMap()

        if self._config.backend not in SUPPORTED_BACKENDS:
            raise ValueError(
                f"Unsupported SLAM backend '{self._config.backend}'. "
                f"Choose one of: {SUPPORTED_BACKENDS}"
            )

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def __enter__(self) -> SlamSession:
        self.start()
        return self

    def __exit__(self, *_: object) -> None:
        self.stop()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Initialise the SLAM back-end.

        Raises:
            ImportError: If the required back-end library is not installed.
            RuntimeError: If the back-end fails to initialise.

        Note:
            TODO(#slam): Implement back-end initialisation for each of
            ``orb_slam3``, ``rtabmap``, and ``open3d``.
        """
        logger.info("Starting SLAM session (backend='%s').", self._config.backend)
        # TODO(#slam): Initialise self._backend_instance here.
        # Example for open3d:
        #   import open3d as o3d
        #   self._backend_instance = o3d.pipelines.odometry.RGBDOdometry(...)
        logger.warning(
            "SLAM backend '%s' is not yet implemented. "
            "process_frame() will return identity poses.",
            self._config.backend,
        )

    def stop(self) -> None:
        """Shutdown the SLAM back-end and optionally save the map."""
        if self._config.map_save_path:
            self.save_map(self._config.map_save_path)
        self._backend_instance = None
        logger.info("SLAM session stopped.")

    # ------------------------------------------------------------------
    # Frame processing
    # ------------------------------------------------------------------

    def process_frame(self, frame: SlamFrame) -> np.ndarray:
        """Submit a new RGB-D frame to the SLAM back-end.

        Args:
            frame: An :class:`SlamFrame` containing a synchronised RGB and
                depth image pair.

        Returns:
            4x4 camera-to-world transformation matrix (``float64``) for the
            current frame.  Returns the identity matrix when tracking is lost
            or the back-end is a stub.

        Note:
            TODO(#slam): Forward *frame* to the active back-end and parse the
            returned camera pose.
        """
        # TODO(#slam): Replace stub with actual back-end call.
        identity = np.eye(4, dtype=np.float64)
        self._map.trajectory.append(identity)
        return identity

    # ------------------------------------------------------------------
    # Map access
    # ------------------------------------------------------------------

    def get_map(self) -> SlamMap:
        """Return a snapshot of the current map state.

        Returns:
            :class:`SlamMap` with keyframes, map points, and trajectory.
        """
        return self._map

    def save_map(self, path: str) -> None:
        """Persist the current map to *path*.

        Args:
            path: Destination file path.  The format depends on the back-end
                (PLY point cloud for Open3D, binary for ORB-SLAM3).

        Note:
            TODO(#slam): Implement map serialisation for each back-end.
        """
        logger.info("Saving SLAM map to '%s' (not yet implemented).", path)
