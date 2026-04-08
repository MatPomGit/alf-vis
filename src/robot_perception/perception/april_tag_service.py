from __future__ import annotations

from typing import List

import cv2
import numpy as np
from pupil_apriltags import Detector

from common.models import CameraCalibration, Pose3D, ROI, VisualMarker


class AprilTagService:
    """Usługa detekcji AprilTag i estymacji pozy na podstawie kalibracji kamery."""

    def __init__(self, family: str = "tag36h11", tag_size_m: float = 0.162) -> None:
        self.tag_size_m = tag_size_m
        self.detector = Detector(
            families=family,
            nthreads=2,
            quad_decimate=1.0,
            quad_sigma=0.0,
            refine_edges=1,
            decode_sharpening=0.25,
            debug=0,
        )

    def detect(
        self,
        frame_bgr: np.ndarray,
        calibration: CameraCalibration,
        roi: ROI | None = None,
    ) -> List[VisualMarker]:
        """Wykrywa tagi i estymuje ich pozę względem kamery."""
        work = frame_bgr
        offset_x = 0
        offset_y = 0

        if roi is not None:
            work = frame_bgr[roi.y:roi.y + roi.height, roi.x:roi.x + roi.width]
            offset_x = roi.x
            offset_y = roi.y

        gray = cv2.cvtColor(work, cv2.COLOR_BGR2GRAY)
        tags = self.detector.detect(gray, estimate_tag_pose=False)

        camera_matrix = np.array(calibration.camera_matrix, dtype=np.float64)
        dist_coeffs = np.array(calibration.distortion_coefficients, dtype=np.float64)

        half = self.tag_size_m / 2.0
        object_points = np.array([
            [-half, -half, 0.0],
            [ half, -half, 0.0],
            [ half,  half, 0.0],
            [-half,  half, 0.0],
        ], dtype=np.float64)

        markers: List[VisualMarker] = []
        for tag in tags:
            image_points = np.array([
                [tag.corners[0][0] + offset_x, tag.corners[0][1] + offset_y],
                [tag.corners[1][0] + offset_x, tag.corners[1][1] + offset_y],
                [tag.corners[2][0] + offset_x, tag.corners[2][1] + offset_y],
                [tag.corners[3][0] + offset_x, tag.corners[3][1] + offset_y],
            ], dtype=np.float64)

            ok, rvec, tvec = cv2.solvePnP(
                object_points,
                image_points,
                camera_matrix,
                dist_coeffs,
                flags=cv2.SOLVEPNP_IPPE_SQUARE,
            )

            pose = None
            translation_vector = None
            rotation_vector = None

            if ok:
                translation_vector = tvec.flatten().tolist()
                rotation_vector = rvec.flatten().tolist()
                pose = Pose3D(
                    x=float(tvec[0][0]),
                    y=float(tvec[1][0]),
                    z=float(tvec[2][0]),
                )

            markers.append(
                VisualMarker(
                    tag_id=int(tag.tag_id),
                    family=str(tag.tag_family),
                    center=(float(tag.center[0] + offset_x), float(tag.center[1] + offset_y)),
                    corners=[
                        (float(pt[0] + offset_x), float(pt[1] + offset_y))
                        for pt in tag.corners
                    ],
                    decision_margin=float(tag.decision_margin),
                    hamming=int(tag.hamming),
                    pose=pose,
                    translation_vector=translation_vector,
                    rotation_vector=rotation_vector,
                )
            )

        return markers

    # TODO: dodać konwersję rvec na roll/pitch/yaw.
    # TODO: dodać filtrację tagów po reprojection error.