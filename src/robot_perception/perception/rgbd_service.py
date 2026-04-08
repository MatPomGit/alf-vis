from __future__ import annotations
from pathlib import Path
from typing import Optional, Tuple
import cv2
import numpy as np
from common.models import DepthMeta
from common.utils import ensure_dir
from perception.console import info, warn
class RGBDService:
    def __init__(self, depth_camera_id: int, width: int, height: int, output_dir: str) -> None:
        self.depth_dir = ensure_dir(Path(output_dir) / 'depth')
        self.cap = cv2.VideoCapture(depth_camera_id)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width); self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.available = self.cap.isOpened()
        if self.available: info(f"Źródło depth zostało otwarte poprawnie (ID={depth_camera_id}).")
        else: warn(f"Nie udało się otworzyć źródła depth o ID={depth_camera_id}. System może przejść do trybu RGB-only.")
        self._kalman_initialized = False; self._depth_state = None; self._depth_cov = None; self._process_noise = 25.0; self._measurement_noise = 100.0
    def is_available(self) -> bool:
        return self.available
    def _kalman_filter_depth(self, depth_mm: np.ndarray) -> np.ndarray:
        measurement = depth_mm.astype(np.float32)
        if not self._kalman_initialized:
            self._depth_state = measurement.copy(); self._depth_cov = np.full_like(measurement, 1.0, dtype=np.float32); self._kalman_initialized = True; info('Zainicjalizowano filtr Kalmana dla mapy głębi.'); return depth_mm
        predicted_state = self._depth_state; predicted_cov = self._depth_cov + self._process_noise
        kalman_gain = predicted_cov / (predicted_cov + self._measurement_noise)
        updated_state = predicted_state + kalman_gain * (measurement - predicted_state)
        updated_cov = (1.0 - kalman_gain) * predicted_cov
        self._depth_state = updated_state; self._depth_cov = updated_cov
        return np.clip(updated_state, 0, np.iinfo(np.uint16).max).astype(np.uint16)
    def capture_depth(self, frame_id: int) -> Tuple[np.ndarray, str, DepthMeta]:
        if not self.available: raise RuntimeError('Źródło depth nie jest dostępne.')
        ok, depth_frame = self.cap.read()
        if not ok or depth_frame is None: raise RuntimeError('Nie udało się pobrać mapy głębi.')
        if len(depth_frame.shape) == 3:
            depth_gray = cv2.cvtColor(depth_frame, cv2.COLOR_BGR2GRAY); depth_mm = depth_gray.astype(np.uint16) * 10
        else:
            depth_mm = depth_frame.astype(np.uint16)
        depth_mm = self._kalman_filter_depth(depth_mm)
        depth_path = self.depth_dir / f'depth_{frame_id:06d}.png'
        cv2.imwrite(str(depth_path), depth_mm)
        meta = DepthMeta(width=depth_mm.shape[1], height=depth_mm.shape[0], encoding='16UC1', depth_scale=1000.0, depth_unit_m=0.001)
        return depth_mm, str(depth_path), meta
    def close(self) -> None:
        if self.available: self.cap.release()
