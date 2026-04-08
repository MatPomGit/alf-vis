from __future__ import annotations

import cv2
import numpy as np

from common.models import ROI


class ActiveVisionService:
    """Usługa wyboru obszaru zainteresowania do dalszej analizy."""

    def select_roi(self, frame_bgr: np.ndarray) -> ROI:
        """Wybiera ROI na podstawie mapy saliency.

        To jest rozsądna implementacja bazowa. W systemie docelowym można ją
        zastąpić polityką task-guided active vision.
        """
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        saliency = cv2.GaussianBlur(gray, (21, 21), 0)
        _, _, _, max_loc = cv2.minMaxLoc(saliency)

        h, w = gray.shape
        roi_w = max(64, w // 2)
        roi_h = max(64, h // 2)

        x = max(0, min(max_loc[0] - roi_w // 2, w - roi_w))
        y = max(0, min(max_loc[1] - roi_h // 2, h - roi_h))

        # TODO: dodać sprzężenie zwrotne z plannerem zadań i polityką uwagi.
        return ROI(x=x, y=y, width=roi_w, height=roi_h)