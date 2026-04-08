from __future__ import annotations

from pathlib import Path
from typing import Tuple

import cv2
import numpy as np

from common.models import ImageMeta
from common.utils import ensure_dir


class VideoFileCameraService:
    """Serwis kamery oparty o plik wideo (np. MP4) zamiast kamery na żywo."""

    def __init__(self, video_path: str | Path, output_dir: str, loop: bool = False) -> None:
        self.video_path = Path(video_path)
        self.loop = loop
        self.frames_dir = ensure_dir(Path(output_dir) / "frames")
        self.cap = cv2.VideoCapture(str(self.video_path))
        self.last_video_timestamp_sec = 0.0
        if not self.cap.isOpened():
            raise RuntimeError(f"Nie udało się otworzyć pliku wideo: {self.video_path}")

    def capture(self, frame_id: int) -> Tuple[np.ndarray, str, ImageMeta]:
        ok, frame = self.cap.read()
        if not ok or frame is None:
            if self.loop:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ok, frame = self.cap.read()
            if not ok or frame is None:
                raise StopIteration("Koniec nagrania wideo.")

        image_path = self.frames_dir / f"frame_{frame_id:06d}.png"
        cv2.imwrite(str(image_path), frame)

        self.last_video_timestamp_sec = float(self.cap.get(cv2.CAP_PROP_POS_MSEC) or 0.0) / 1000.0
        fps = float(self.cap.get(cv2.CAP_PROP_FPS) or 0.0)
        meta = ImageMeta(
            width=frame.shape[1],
            height=frame.shape[0],
            encoding="bgr8",
            fps=fps,
            camera_id=-1,
        )
        return frame, str(image_path), meta

    def get_current_video_timestamp_sec(self) -> float:
        return self.last_video_timestamp_sec

    def close(self) -> None:
        self.cap.release()
