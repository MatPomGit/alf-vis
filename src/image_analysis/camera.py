"""Camera capture module for Unitree G1 EDU robot.

Provides an interface for capturing RGB and depth frames from the Unitree G1 EDU
camera system.  The robot exposes its cameras either through the Unitree SDK2
(``unitree_sdk2_python``) or as standard V4L2/network streams accessible via
``cv2.VideoCapture``.

Implementation notes:
    - Unitree SDK2: https://github.com/unitreerobotics/unitree_sdk2_python
    - The G1 EDU front camera is typically reachable at the robot's IP address
      over a dedicated UDP channel (port 9871 by default).
    - Depth data comes from an onboard ToF / structured-light sensor streamed
      in sync with the RGB frames.
    - Both streams should be time-stamped and synchronised before RGBD fusion.
    - Fall back to ``cv2.VideoCapture`` for desktop testing with a USB camera.
"""

from __future__ import annotations

import logging
from collections.abc import Generator
from dataclasses import dataclass, field
from pathlib import Path

import cv2
import numpy as np

logger = logging.getLogger(__name__)

# Default camera parameters for Unitree G1 EDU front camera.
DEFAULT_FRAME_WIDTH: int = 1280
DEFAULT_FRAME_HEIGHT: int = 720
DEFAULT_FPS: int = 30

# Network stream defaults when using the Unitree SDK.
DEFAULT_ROBOT_IP: str = "192.168.123.161"
DEFAULT_CAMERA_PORT: int = 9871


@dataclass
class CameraConfig:
    """Configuration for a single camera stream.

    Attributes:
        source: Camera source identifier.  Either an integer (local device
            index for ``cv2.VideoCapture``) or a string URI
            (``"rtsp://…"``, ``"unitree://192.168.123.161"``).
        frame_width: Requested frame width in pixels.
        frame_height: Requested frame height in pixels.
        fps: Requested frames per second.
        enable_depth: Whether to also capture the paired depth stream.
        calibration_file: Optional path to a ``CalibrationResult`` YAML
            previously saved by :func:`~image_analysis.calibration.save_calibration`.
    """

    source: int | str = 0
    frame_width: int = DEFAULT_FRAME_WIDTH
    frame_height: int = DEFAULT_FRAME_HEIGHT
    fps: int = DEFAULT_FPS
    enable_depth: bool = False
    calibration_file: Path | None = None


@dataclass
class RgbdFrame:
    """A single synchronised RGB + depth frame pair.

    Attributes:
        rgb: BGR image array with shape ``(H, W, 3)``, dtype ``uint8``.
        depth: Depth map with shape ``(H, W)``, dtype ``float32``.
            Each element stores the metric distance in metres.
            Pixels with no depth reading contain ``NaN``.
        timestamp_ns: Capture timestamp in nanoseconds (monotonic clock).
    """

    rgb: np.ndarray
    depth: np.ndarray
    timestamp_ns: int = field(default=0)


class UnitreeCamera:
    """Camera interface for the Unitree G1 EDU robot.

    Wraps ``cv2.VideoCapture`` for desktop testing and can be subclassed to
    add Unitree SDK2 transport when running on the robot.

    Example::

        config = CameraConfig(source=0, enable_depth=False)
        with UnitreeCamera(config) as cam:
            for frame in cam.stream_rgb():
                process(frame)

    Args:
        config: Camera configuration.

    Raises:
        RuntimeError: If the camera stream cannot be opened.
    """

    def __init__(self, config: CameraConfig) -> None:
        self._config = config
        self._cap: cv2.VideoCapture | None = None

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def __enter__(self) -> UnitreeCamera:
        self.open()
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def open(self) -> None:
        """Open the camera stream.

        Raises:
            RuntimeError: If the stream cannot be opened with the given
                :attr:`CameraConfig.source`.
        """
        logger.debug("Available cameras: %s", list_available_cameras())
        
        # TODO(#camera): Replace with Unitree SDK2 transport when running on
        # the robot.  For desktop testing, fall back to cv2.VideoCapture.
        self._cap = cv2.VideoCapture(self._config.source)
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self._config.frame_width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self._config.frame_height)
        self._cap.set(cv2.CAP_PROP_FPS, self._config.fps)

        if not self._cap.isOpened():
            raise RuntimeError(
                f"Failed to open camera source: {self._config.source!r}"
            )
        logger.info(
            "Camera opened: source=%r  %dx%d @ %d fps",
            self._config.source,
            self._config.frame_width,
            self._config.frame_height,
            self._config.fps,
        )

    def close(self) -> None:
        """Release the camera stream."""
        if self._cap is not None:
            self._cap.release()
            self._cap = None
            logger.info("Camera released.")

    @property
    def is_open(self) -> bool:
        """Return ``True`` if the camera stream is currently open."""
        return self._cap is not None and self._cap.isOpened()

    # ------------------------------------------------------------------
    # Frame capture
    # ------------------------------------------------------------------

    def read_rgb(self) -> tuple[bool, np.ndarray]:
        """Read a single RGB frame.

        Returns:
            Tuple ``(ok, frame)`` where *ok* is ``True`` on success and
            *frame* is a BGR ``uint8`` array of shape ``(H, W, 3)``.
            On failure *frame* is an empty array.

        Raises:
            RuntimeError: If the camera stream is not open.
        """
        if not self.is_open or self._cap is None:
            raise RuntimeError("Camera stream is not open. Call open() first.")
        ok, frame = self._cap.read()
        if not ok:
            logger.warning("Failed to read frame from camera.")
        return ok, frame

    def read_rgbd(self) -> RgbdFrame:
        """Read a synchronised RGB + depth frame.

        Returns:
            An :class:`RgbdFrame` with both RGB and depth data.

        Raises:
            RuntimeError: If the camera stream is not open.
            NotImplementedError: If depth capture is not yet implemented for
                the configured source.

        Note:
            TODO(#camera): Implement depth capture for the Unitree G1 EDU
            depth sensor.  The depth channel is currently a placeholder
            filled with zeros.
        """
        ok, rgb = self.read_rgb()
        if not ok:
            raise RuntimeError("Failed to capture RGB frame.")

        h, w = rgb.shape[:2]
        depth = np.zeros((h, w), dtype=np.float32)
        logger.debug("Depth capture not yet implemented; returning zeros.")

        return RgbdFrame(rgb=rgb, depth=depth)

    def stream_rgb(self) -> Generator[np.ndarray, None, None]:
        """Yield BGR frames continuously until the stream ends.

        Yields:
            BGR ``uint8`` arrays of shape ``(H, W, 3)``.

        Raises:
            RuntimeError: If the camera stream is not open.
        """
        while True:
            ok, frame = self.read_rgb()
            if not ok:
                break
            yield frame

    def stream_rgbd(self) -> Generator[RgbdFrame, None, None]:
        """Yield synchronised RGB+depth frames continuously.

        Yields:
            :class:`RgbdFrame` instances.

        Raises:
            RuntimeError: If the camera stream is not open.
        """
        while True:
            try:
                frame = self.read_rgbd()
            except RuntimeError:
                break
            yield frame


def list_available_cameras(max_index: int = 8) -> list[int]:
    """Return a list of working local camera device indices.

    Probes ``cv2.VideoCapture`` for indices 0 … *max_index* - 1.

    Args:
        max_index: Upper bound (exclusive) of device indices to probe.

    Returns:
        Sorted list of device indices that can be opened successfully.
    """
    available: list[int] = []
    for idx in range(max_index):
        cap = cv2.VideoCapture(idx)
        if cap.isOpened():
            available.append(idx)
            cap.release()
    logger.debug("Available cameras: %s", available)
    return available

if __name__ == "__main__":
    config = CameraConfig(source=0)

    with UnitreeCamera(config) as cam:
        for frame in cam.stream_rgb():
            cv2.imshow("Camera", frame)

            if cv2.waitKey(1) & 0xFF == 27:  # ESC
                break

    cv2.destroyAllWindows()