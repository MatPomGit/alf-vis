from __future__ import annotations

from typing import List

import cv2
import numpy as np
from pupil_apriltags import Detector

from common.models import ROI, Pose3D, VisualMarker


class AprilTagService:
    """Usługa detekcji markerów AprilTag w obrazie."""

    def __init__(self, family: str = "tag36h11") -> None:
        self.detector = Detector(
            families=family,
            nthreads=2,
            quad_decimate=1.0,
            quad_sigma=0.0,
            refine_edges=1,
            decode_sharpening=0.25,
            debug=0,
        )

    def detect(self, frame_bgr: np.ndarray, roi: ROI | None = None) -> List[VisualMarker]:
        """Wykrywa AprilTagi w całym obrazie lub we wskazanym ROI."""
        work = frame_bgr
        offset_x = 0
        offset_y = 0

        if roi is not None:
            work = frame_bgr[roi.y:roi.y + roi.height, roi.x:roi.x + roi.width]
            offset_x = roi.x
            offset_y = roi.y

        gray = cv2.cvtColor(work, cv2.COLOR_BGR2GRAY)
        tags = self.detector.detect(gray, estimate_tag_pose=False)

        markers: List[VisualMarker] = []
        for tag in tags:
            corners = [
                (float(pt[0] + offset_x), float(pt[1] + offset_y))
                for pt in tag.corners
            ]
            center = (float(tag.center[0] + offset_x), float(tag.center[1] + offset_y))

            markers.append(
                VisualMarker(
                    tag_id=int(tag.tag_id),
                    family=str(tag.tag_family),
                    center=center,
                    corners=corners,
                    pose=None,
                    decision_margin=float(tag.decision_margin),
                    hamming=int(tag.hamming),
                )
            )

        # TODO: dodać estymację pozy markera na podstawie kalibracji kamery.
        return markers