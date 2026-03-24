import logging
import time
from collections.abc import Generator
from dataclasses import dataclass, field
from pathlib import Path

import cv2
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- DEFAULTS ---
DEFAULT_FRAME_WIDTH = 640
DEFAULT_FRAME_HEIGHT = 480
DEFAULT_FPS = 30


# --- CONFIG ---
@dataclass
class CameraConfig:
    source: int | str = 0
    frame_width: int = DEFAULT_FRAME_WIDTH
    frame_height: int = DEFAULT_FRAME_HEIGHT
    fps: int = DEFAULT_FPS
    enable_depth: bool = True
    calibration_file: Path | None = None


@dataclass
class RgbdFrame:
    rgb: np.ndarray
    depth: np.ndarray
    timestamp_ns: int = field(default=0)


# --- CAMERA CLASS ---
class UnitreeCamera:
    def __init__(self, config: CameraConfig) -> None:
        self._config = config
        self._cap: cv2.VideoCapture | None = None

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, *_):
        self.close()

    def open(self):
        self._cap = cv2.VideoCapture(self._config.source)
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self._config.frame_width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self._config.frame_height)
        self._cap.set(cv2.CAP_PROP_FPS, self._config.fps)
        self._cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        print(self._cap.get(cv2.CAP_PROP_FPS))


        if not self._cap.isOpened():
            raise RuntimeError(f"Cannot open camera: {self._config.source}")

        logger.info(
            "Camera opened: %s (%dx%d @ %dfps)",
            self._config.source,
            self._config.frame_width,
            self._config.frame_height,
            self._config.fps,
        )

    def close(self):
        if self._cap:
            self._cap.release()
            self._cap = None
            logger.info("Camera released")

    @property
    def is_open(self):
        return self._cap is not None and self._cap.isOpened()

    def read_rgb(self):
        if not self.is_open:
            raise RuntimeError("Camera not open")

        ok, frame = self._cap.read()
        if not ok:
            logger.warning("Frame read failed")
        return ok, frame

    def stream_rgb(self) -> Generator[np.ndarray, None, None]:
        while True:
            ok, frame = self.read_rgb()
            if not ok:
                break
            yield frame


# --- UTILS ---
def list_available_cameras(max_index: int = 8):
    available = []
    for i in range(max_index):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            available.append(i)
            cap.release()
    return available

# frame = draw_overlay(frame, fps)
# --- OVERLAY ---
def draw_overlay(frame, fps):
    h, w = frame.shape[:2]

    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    res_text = f"{w}x{h}"
    fps_text = f"{fps:.1f}"

    # półprzezroczyste tło
    overlay = frame.copy()
    cv2.rectangle(overlay, (5, 5), (310, 100), (0, 0, 0), -1)
    alpha = 0.2
    frame = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)

    # tekst
    cv2.putText(frame, f"Time: {timestamp}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    cv2.putText(frame, f"Res: {res_text}", (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    cv2.putText(frame, f"FPS: {fps_text}", (10, 90),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    return frame


# --- MAIN ---
if __name__ == "__main__":
    print("Available cameras:", list_available_cameras())

    config = CameraConfig(source=0)

    with UnitreeCamera(config) as cam:
        prev_time = time.time()
        fps = 0.0

        #for frame in cam.stream_rgb():
        for frame in cam.stream_rgb():
            # FPS
            now = time.time()
            dt = now - prev_time
            prev_time = now

            if dt > 0:
                fps = 0.9 * fps + 0.1 * (1.0 / dt)

            # overlay
            frame = draw_overlay(frame, fps)
            

            # show
            cv2.imshow("Camera", frame)

            if frame_id % 2 == 0:
                cv2.imshow(...)

            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC
                break

    cv2.destroyAllWindows()