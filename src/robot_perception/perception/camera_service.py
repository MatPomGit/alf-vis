from __future__ import annotations
from pathlib import Path
from typing import Tuple
import cv2
import numpy as np
from common.models import ImageMeta
from common.utils import ensure_dir
class CameraService:
    def __init__(self, camera_id: int, width: int, height: int, output_dir: str) -> None:
        self.camera_id = camera_id
        self.frames_dir = ensure_dir(Path(output_dir) / 'frames')
        self.cap = cv2.VideoCapture(camera_id)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width); self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        if not self.cap.isOpened(): raise RuntimeError(f"Nie udało się otworzyć kamery RGB o ID={camera_id}.")
    def capture(self, frame_id: int) -> Tuple[np.ndarray, str, ImageMeta]:
        ok, frame = self.cap.read()
        if not ok or frame is None: raise RuntimeError('Nie udało się pobrać obrazu RGB z kamery.')
        image_path = self.frames_dir / f'frame_{frame_id:06d}.png'
        cv2.imwrite(str(image_path), frame)
        meta = ImageMeta(width=frame.shape[1], height=frame.shape[0], encoding='bgr8', fps=float(self.cap.get(cv2.CAP_PROP_FPS) or 0.0), camera_id=self.camera_id)
        return frame, str(image_path), meta
    def close(self) -> None:
        self.cap.release()
