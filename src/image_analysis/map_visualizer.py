"""Real-time 3-D map visualisation.

Provides tools for displaying and interacting with the 3-D SLAM map
produced by :mod:`~image_analysis.slam`.  The visualisation is updated
incrementally as new frames are processed.

Back-ends
---------
* **Open3D** (``pip install open3d``) - interactive ``Visualizer`` window;
  runs in the main thread and supports mouse navigation.
* **PyVista** (``pip install pyvista``) - richer rendering with lighting,
  mesh shading, and off-screen rendering.
* **Matplotlib** - basic fallback; suitable for offline snapshots only.

Implementation notes:
    - The visualiser runs in a background thread so it does not block the
      main capture / processing loop.
    - Map geometry (point cloud + camera trajectory) is updated via a thread-
      safe queue.
    - A ``MapVisualizerConfig.snapshot_dir`` can be specified to auto-save
      PNG screenshots at regular intervals.
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from image_analysis.point_cloud import PointCloud
from image_analysis.slam import SlamMap

logger = logging.getLogger(__name__)

# Supported visualisation back-ends.
BACKEND_OPEN3D: str = "open3d"
BACKEND_PYVISTA: str = "pyvista"
BACKEND_MATPLOTLIB: str = "matplotlib"

SUPPORTED_BACKENDS: tuple[str, ...] = (
    BACKEND_OPEN3D,
    BACKEND_PYVISTA,
    BACKEND_MATPLOTLIB,
)


@dataclass
class MapVisualizerConfig:
    """Configuration for the 3-D map visualiser.

    Attributes:
        backend: Rendering back-end.  One of :data:`SUPPORTED_BACKENDS`.
        window_title: Title of the visualisation window.
        point_size: Rendered point size in pixels.
        background_color: RGB background colour in ``[0.0, 1.0]``.
        show_trajectory: Overlay the camera trajectory as a line.
        show_axes: Show world-frame coordinate axes.
        snapshot_dir: If set, PNG snapshots are saved here every
            *snapshot_interval_s* seconds.
        snapshot_interval_s: Auto-snapshot interval in seconds.
        update_interval_ms: Target visualisation refresh interval in
            milliseconds.
    """

    backend: str = BACKEND_OPEN3D
    window_title: str = "ALF-Nav 3-D Map"
    point_size: float = 1.5
    background_color: tuple[float, float, float] = (0.1, 0.1, 0.1)
    show_trajectory: bool = True
    show_axes: bool = True
    snapshot_dir: str = ""
    snapshot_interval_s: float = 60.0
    update_interval_ms: int = 33  # ~30 FPS


class MapVisualizer:
    """Background 3-D map visualiser.

    Opens a visualisation window in a background thread and provides
    :meth:`update` to push new map geometry without blocking the main loop.

    Example::

        config = MapVisualizerConfig(backend="open3d")
        viz = MapVisualizer(config)
        viz.start()

        for frame in camera.stream_rgbd():
            slam.process_frame(...)
            cloud = create_point_cloud(frame.rgb, frame.depth, calibration)
            viz.update(slam.get_map(), cloud)

        viz.stop()

    Args:
        config: Visualiser configuration.

    Raises:
        ValueError: If the configured back-end is not supported.
    """

    def __init__(self, config: MapVisualizerConfig | None = None) -> None:
        self._config = config or MapVisualizerConfig()
        if self._config.backend not in SUPPORTED_BACKENDS:
            raise ValueError(
                f"Unsupported backend '{self._config.backend}'. "
                f"Choose one of: {SUPPORTED_BACKENDS}"
            )
        self._thread: threading.Thread | None = None
        self._running = threading.Event()
        self._pending_cloud: PointCloud | None = None
        self._pending_map: SlamMap | None = None
        self._lock = threading.Lock()

    def start(self) -> None:
        """Open the visualisation window in a background thread.

        Note:
            TODO(#map-viz): Implement the Open3D / PyVista rendering loop.
            The background thread should call :func:`_render_loop` with the
            configured back-end.
        """
        self._running.set()
        self._thread = threading.Thread(
            target=self._render_loop, daemon=True, name="map-visualizer"
        )
        self._thread.start()
        logger.info("Map visualiser started (backend='%s').", self._config.backend)

    def stop(self) -> None:
        """Stop the visualisation window and join the background thread."""
        self._running.clear()
        if self._thread is not None:
            self._thread.join(timeout=5.0)
            self._thread = None
        logger.info("Map visualiser stopped.")

    def update(
        self,
        slam_map: SlamMap | None = None,
        cloud: PointCloud | None = None,
    ) -> None:
        """Push new geometry to the visualiser.

        Thread-safe.  The new data will be rendered on the next visualiser
        refresh cycle.

        Args:
            slam_map: Latest SLAM map snapshot (keyframes + map points).
            cloud: Latest dense point cloud from RGB-D fusion.
        """
        with self._lock:
            if slam_map is not None:
                self._pending_map = slam_map
            if cloud is not None:
                self._pending_cloud = cloud

    def save_snapshot(self, path: str | Path) -> None:
        """Save a screenshot of the current map view to *path*.

        Args:
            path: Destination PNG file path.

        Note:
            TODO(#map-viz): Implement screenshot capture for each back-end.
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        logger.info("Snapshot requested: '%s' (not yet implemented).", path)

    # ------------------------------------------------------------------
    # Internal render loop
    # ------------------------------------------------------------------

    def _render_loop(self) -> None:
        """Background thread: initialise and run the rendering back-end.

        Note:
            TODO(#map-viz): Implement Open3D / PyVista / Matplotlib render
            loop.  The loop should run while ``self._running.is_set()``,
            consume geometry from ``self._pending_cloud`` / ``_pending_map``
            under ``self._lock``, and refresh the window.
        """
        logger.debug(
            "Render loop started (backend='%s'). Stub - no window opened.",
            self._config.backend,
        )
        while self._running.is_set():
            self._running.wait(timeout=self._config.update_interval_ms / 1000.0)


def create_trajectory_line_set(
    trajectory: list[np.ndarray],
) -> tuple[np.ndarray, np.ndarray]:
    """Convert a list of 4x4 camera poses to a line-set representation.

    Args:
        trajectory: List of 4x4 camera-to-world transformation matrices.

    Returns:
        Tuple ``(points, lines)`` where *points* has shape ``(N, 3)`` and
        *lines* has shape ``(N-1, 2)`` as arrays of integer indices.
        Returns empty arrays when the trajectory has fewer than 2 poses.
    """
    if len(trajectory) < 2:
        return np.empty((0, 3), dtype=np.float64), np.empty((0, 2), dtype=np.int64)

    # Extract camera positions (last column of each pose matrix).
    positions = np.array([T[:3, 3] for T in trajectory], dtype=np.float64)
    n = len(positions)
    lines = np.array([[i, i + 1] for i in range(n - 1)], dtype=np.int64)
    return positions, lines


@dataclass
class VisualizerSnapshot:
    """A serialised snapshot of the current visualiser state.

    Attributes:
        timestamp_s: Monotonic timestamp when the snapshot was taken.
        num_points: Number of points in the cloud at snapshot time.
        num_keyframes: Number of SLAM keyframes at snapshot time.
        camera_position: Camera position ``(x, y, z)`` in metres.
    """

    timestamp_s: float = 0.0
    num_points: int = 0
    num_keyframes: int = 0
    camera_position: tuple[float, float, float] = field(default_factory=lambda: (0.0, 0.0, 0.0))
