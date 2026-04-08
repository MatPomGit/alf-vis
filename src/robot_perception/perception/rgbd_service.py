from __future__ import annotations

from pathlib import Path
from typing import Tuple

import cv2
import numpy as np

from common.models import DepthMeta
from common.utils import ensure_dir


class RGBDService:
    """Usługa przechwytywania depth / RGB-D.

    Wersja bazowa zakłada osobne źródło depth. W realnym robocie ten moduł
    najczęściej podmienia się na adapter dla RealSense / ZED / topiców ROS2.
    """

    def __init__(self, depth_camera_id: int, width: int, height: int, output_dir: str) -> None:
        self.depth_camera_id = depth_camera_id
        self.width = width
        self.height = height
        self.depth_dir = ensure_dir(Path(output_dir) / "depth")

        self.cap = cv2.VideoCapture(depth_camera_id)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

        if not self.cap.isOpened():
            raise RuntimeError(f"Nie udało się otworzyć źródła depth o ID={depth_camera_id}.")

    def capture_depth(self, frame_id: int) -> Tuple[np.ndarray, str, DepthMeta]:
        """Pobiera pojedynczą mapę głębi.

        Uwaga: dla zwykłego OpenCV `VideoCapture` to będzie zwykle obraz 8-bit.
        W docelowym wdrożeniu należy tu podłączyć rzeczywiste źródło depth.
        """
        ok, depth_frame = self.cap.read()
        if not ok or depth_frame is None:
            raise RuntimeError("Nie udało się pobrać mapy głębi.")

        if len(depth_frame.shape) == 3:
            depth_gray = cv2.cvtColor(depth_frame, cv2.COLOR_BGR2GRAY)
            depth_mm = depth_gray.astype(np.uint16) * 10
        else:
            depth_mm = depth_frame.astype(np.uint16)

        depth_path = self.depth_dir / f"depth_{frame_id:06d}.png"
        cv2.imwrite(str(depth_path), depth_mm)

        meta = DepthMeta(
            width=depth_mm.shape[1],
            height=depth_mm.shape[0],
            encoding="16UC1",
            depth_scale=1000.0,
            depth_unit_m=0.001,
        )
        return depth_mm, str(depth_path), meta

    def close(self) -> None:
        """Zamyka źródło depth."""
        self.cap.release()

    # TODO: dodać adapter dla Intel RealSense / ROS2 Image + CameraInfo.