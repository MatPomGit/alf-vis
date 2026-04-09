from __future__ import annotations

from typing import Optional, Sequence

import cv2
import numpy as np

from common.models import LightTarget, ROI
from perception.console import info


class LightTargetService:
    def __init__(self, threshold: int = 230, min_area_px: float = 40.0, hsv_lower: Sequence[int] | None = None, hsv_upper: Sequence[int] | None = None) -> None:
        self.threshold = int(np.clip(threshold, 0, 255))
        self.min_area_px = max(float(min_area_px), 1.0)
        self.hsv_lower, self.hsv_upper = self._normalize_hsv_bounds(hsv_lower, hsv_upper)
        color_filter_status = f"hsv={self.hsv_lower.tolist()}..{self.hsv_upper.tolist()}" if self.hsv_lower is not None and self.hsv_upper is not None else "hsv=off"
        info(f"Zainicjalizowano detekcję jasnej plamy (threshold={self.threshold}, min_area={self.min_area_px:.1f}px, {color_filter_status}).")

    @staticmethod
    def _normalize_hsv_bounds(hsv_lower: Sequence[int] | None, hsv_upper: Sequence[int] | None) -> tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        if hsv_lower is None or hsv_upper is None:
            return None, None
        if len(hsv_lower) != 3 or len(hsv_upper) != 3:
            return None, None
        lower = np.array([np.clip(int(hsv_lower[0]), 0, 179), np.clip(int(hsv_lower[1]), 0, 255), np.clip(int(hsv_lower[2]), 0, 255)], dtype=np.uint8)
        upper = np.array([np.clip(int(hsv_upper[0]), 0, 179), np.clip(int(hsv_upper[1]), 0, 255), np.clip(int(hsv_upper[2]), 0, 255)], dtype=np.uint8)
        return lower, upper

    def detect(self, frame_bgr: np.ndarray, roi: ROI | None = None) -> Optional[LightTarget]:
        if frame_bgr is None or frame_bgr.size == 0:
            return None
        if roi is None:
            work = frame_bgr
            offset_x, offset_y = 0, 0
        else:
            h, w = frame_bgr.shape[:2]
            x0 = max(0, min(roi.x, w - 1))
            y0 = max(0, min(roi.y, h - 1))
            x1 = max(x0 + 1, min(roi.x + roi.width, w))
            y1 = max(y0 + 1, min(roi.y + roi.height, h))
            work = frame_bgr[y0:y1, x0:x1]
            offset_x, offset_y = x0, y0
        gray = cv2.cvtColor(work, cv2.COLOR_BGR2GRAY)
        _, mask = cv2.threshold(gray, self.threshold, 255, cv2.THRESH_BINARY)
        if self.hsv_lower is not None and self.hsv_upper is not None:
            hsv = cv2.cvtColor(work, cv2.COLOR_BGR2HSV)
            mask_color = cv2.inRange(hsv, self.hsv_lower, self.hsv_upper)
            mask = cv2.bitwise_and(mask, mask_color)
        kernel = np.ones((3, 3), dtype=np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
        mask = cv2.morphologyEx(mask, cv2.MORPH_DILATE, kernel, iterations=1)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        valid = [c for c in contours if cv2.contourArea(c) >= self.min_area_px and len(c) >= 5]
        if not valid:
            return None
        best = max(valid, key=cv2.contourArea)
        (cx, cy), (axis_w, axis_h), angle = cv2.fitEllipse(best)
        return LightTarget(
            center_xy=(float(cx + offset_x), float(cy + offset_y)),
            axes_xy=(float(axis_w), float(axis_h)),
            angle_deg=float(angle),
            area_px=float(cv2.contourArea(best)),
            contour_points=int(len(best)),
        )
