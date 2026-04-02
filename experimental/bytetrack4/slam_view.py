"""Interactive 3-D SLAM visualisation using matplotlib.

Provides an interactive matplotlib window with 3D axes that dynamically
displays the robot's pose and detected markers as a point cloud. The
view supports interactive rotation, zoom, and pan.

Usage::

    from robo_vision.slam_view import SlamView3D

    view = SlamView3D()
    view.update(markers=marker_list, robot_pose=pose)
    # ... in a loop ...
    view.close()

This module is optional and only available when ``matplotlib`` is
installed.
"""

from __future__ import annotations

import logging
from typing import List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    # These imports are only for type checking, not executed at runtime
    from robo_vision.marker_map import MarkerPose3D, RobotPose3D

logger = logging.getLogger("robo_vision.slam_view")


def _matplotlib_available() -> bool:
    """Return ``True`` if matplotlib is importable."""
    try:
        import importlib.util
        return importlib.util.find_spec("matplotlib") is not None
    except (ImportError, ModuleNotFoundError):
        return False


class SlamView3D:
    """Interactive 3-D visualisation of SLAM map and robot pose.

    When ``matplotlib`` is not installed, all methods are safe no-ops.

    Parameters
    ----------
    title
        Window title.
    figsize
        Figure size in inches ``(width, height)``.
    backend
        Matplotlib backend to use (e.g., 'TkAgg', 'Qt5Agg'). If None,
        the default backend is used.
    show_orientation
        If True, draw arrows indicating orientation (requires objects
        to have an ``orientation`` attribute).
    xlim, ylim, zlim
        Fixed axis limits. If None, limits are automatically adjusted.
    """

    def __init__(
        self,
        title: str = "SLAM 3D View",
        figsize: Tuple[float, float] = (6, 5),
        backend: Optional[str] = None,
        show_orientation: bool = False,
        xlim: Optional[Tuple[float, float]] = None,
        ylim: Optional[Tuple[float, float]] = None,
        zlim: Optional[Tuple[float, float]] = None,
    ) -> None:
        self._title = title
        self._figsize = figsize
        self._backend = backend
        self._show_orientation = show_orientation
        self._xlim = xlim
        self._ylim = ylim
        self._zlim = zlim
        self._available = _matplotlib_available()
        self._fig = None
        self._ax = None
        self._initialized = False

    @property
    def available(self) -> bool:
        """``True`` when matplotlib is importable."""
        return self._available

    def _init_figure(self) -> bool:
        """Create the matplotlib figure and 3D axes.

        Returns ``True`` on success.
        """
        if not self._available:
            return False

        try:
            import matplotlib
            if self._backend is not None:
                matplotlib.use(self._backend)
            import matplotlib.pyplot as plt
            from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

            self._fig = plt.figure(
                num=self._title, figsize=self._figsize
            )
            self._ax = self._fig.add_subplot(111, projection="3d")
            self._ax.set_xlabel("X (cm)")
            self._ax.set_ylabel("Y (cm)")
            self._ax.set_zlabel("Z (cm)")
            self._ax.set_title("SLAM Map")

            # Apply fixed limits if provided
            if self._xlim:
                self._ax.set_xlim(self._xlim)
            if self._ylim:
                self._ax.set_ylim(self._ylim)
            if self._zlim:
                self._ax.set_zlim(self._zlim)

            self._fig.tight_layout()
            self._initialized = True
            logger.info("SLAM 3D view initialized.")
            return True

        except Exception as exc:
            logger.warning("Could not initialize 3D view: %s", exc)
            self._available = False
            return False

    def update(
        self,
        markers: Optional[List[MarkerPose3D]] = None,
        robot_pose: Optional[RobotPose3D] = None,
    ) -> None:
        """Update the 3D plot with current marker and robot positions.

        Parameters
        ----------
        markers
            List of :class:`~robo_vision.marker_map.MarkerPose3D` objects.
        robot_pose
            A :class:`~robo_vision.marker_map.RobotPose3D` object, or
            ``None`` if the robot pose is unknown.
        """
        if not self._available:
            return

        if not self._initialized:
            if not self._init_figure():
                return

        try:
            import matplotlib.pyplot as plt

            self._ax.cla()  # For simplicity; can be optimised later
            self._ax.set_xlabel("X (cm)")
            self._ax.set_ylabel("Y (cm)")
            self._ax.set_zlabel("Z (cm)")
            self._ax.set_title("SLAM Map")

            # Restore fixed limits if any
            if self._xlim:
                self._ax.set_xlim(self._xlim)
            if self._ylim:
                self._ax.set_ylim(self._ylim)
            if self._zlim:
                self._ax.set_zlim(self._zlim)

            # Draw markers as green triangles
            if markers:
                xs = [m.position[0] for m in markers]
                ys = [m.position[1] for m in markers]
                zs = [m.position[2] for m in markers]
                self._ax.scatter(
                    xs, ys, zs, c="green", marker="^", s=60,
                    label="Markers", depthshade=True,
                )
                for m in markers:
                    self._ax.text(
                        m.position[0], m.position[1], m.position[2],
                        f"  {m.marker_id}", fontsize=7, color="green",
                    )
                # Optionally draw orientation arrows
                if self._show_orientation:
                    for m in markers:
                        if hasattr(m, "orientation") and m.orientation is not None:
                            # Assume orientation is a 3D vector (dx, dy, dz)
                            dx, dy, dz = m.orientation
                            self._ax.quiver(
                                m.position[0], m.position[1], m.position[2],
                                dx, dy, dz, length=10, color="green", arrow_length_ratio=0.1
                            )

            # Draw robot pose as a red dot
            if robot_pose is not None and robot_pose.visible_markers > 0:
                rx, ry, rz = robot_pose.position
                self._ax.scatter(
                    [rx], [ry], [rz], c="red", marker="o", s=100,
                    label="Robot", depthshade=True,
                )
                # Optionally draw orientation arrow
                if self._show_orientation and hasattr(robot_pose, "orientation"):
                    dx, dy, dz = robot_pose.orientation
                    self._ax.quiver(
                        rx, ry, rz, dx, dy, dz,
                        length=15, color="red", arrow_length_ratio=0.2
                    )

            if markers or (robot_pose and robot_pose.visible_markers > 0):
                self._ax.legend(loc="upper left", fontsize=8)

            self._fig.canvas.draw_idle()
            plt.pause(0.001)

        except Exception as exc:
            # Log as warning to make issues visible, but don't crash
            logger.warning("3D view update error: %s", exc)

    def save_snapshot(self, filename: str) -> None:
        """Save the current view to an image file.

        Parameters
        ----------
        filename
            Path where the image will be saved (e.g., 'snapshot.png').
        """
        if self._fig is not None:
            try:
                self._fig.savefig(filename)
                logger.info("Snapshot saved to %s", filename)
            except Exception as exc:
                logger.warning("Could not save snapshot: %s", exc)

    def close(self) -> None:
        """Close the matplotlib window."""
        if self._fig is not None:
            try:
                import matplotlib.pyplot as plt
                plt.close(self._fig)
            except Exception:
                pass
            self._fig = None
            self._ax = None
            self._initialized = False

    def __enter__(self) -> SlamView3D:
        """Enter the runtime context for the with statement."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the runtime context and close the view."""
        self.close()