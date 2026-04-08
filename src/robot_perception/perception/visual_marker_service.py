from __future__ import annotations
from typing import List, Optional
import cv2
import numpy as np
from pupil_apriltags import Detector
from common.models import CameraCalibration, Pose3D, ROI, VisualMarker
from perception.console import info, warn
class VisualMarkerService:
    def __init__(self, apriltag_family: str='tag36h11', apriltag_size_m: float=0.162, apriltag_enabled: bool=True, cctag_enabled: bool=True, qr_enabled: bool=True) -> None:
        self.apriltag_size_m = apriltag_size_m; self.apriltag_enabled = apriltag_enabled; self.cctag_enabled = cctag_enabled; self.qr_enabled = qr_enabled
        self.apriltag_detector = Detector(families=apriltag_family, nthreads=2, quad_decimate=1.0, quad_sigma=0.0, refine_edges=1, decode_sharpening=0.25, debug=0)
        self.qr_detector = cv2.QRCodeDetector()
        info(f"Zainicjalizowano markery: AprilTag={apriltag_enabled}, CCTag={cctag_enabled}, QR={qr_enabled}")
    @staticmethod
    def _rotation_matrix_to_rpy(rotation_matrix: np.ndarray) -> tuple[float,float,float]:
        sy = float(np.sqrt(rotation_matrix[0,0]**2 + rotation_matrix[1,0]**2)); singular = sy < 1e-6
        if not singular:
            roll = float(np.arctan2(rotation_matrix[2,1], rotation_matrix[2,2])); pitch = float(np.arctan2(-rotation_matrix[2,0], sy)); yaw = float(np.arctan2(rotation_matrix[1,0], rotation_matrix[0,0]))
        else:
            roll = float(np.arctan2(-rotation_matrix[1,2], rotation_matrix[1,1])); pitch = float(np.arctan2(-rotation_matrix[2,0], sy)); yaw = 0.0
        return roll, pitch, yaw
    @staticmethod
    def _compute_reprojection_error(object_points: np.ndarray, image_points: np.ndarray, rvec: np.ndarray, tvec: np.ndarray, camera_matrix: np.ndarray, dist_coeffs: np.ndarray) -> float:
        reprojected, _ = cv2.projectPoints(object_points, rvec, tvec, camera_matrix, dist_coeffs)
        reprojected = reprojected.reshape(-1,2); image_points_2d = image_points.reshape(-1,2); errors = np.linalg.norm(image_points_2d - reprojected, axis=1); return float(np.mean(errors))
    def _estimate_pose_from_square(self, image_points: np.ndarray, calibration: CameraCalibration, marker_size_m: float) -> tuple[Optional[Pose3D], Optional[list[float]], Optional[list[float]], Optional[float], Optional[str]]:
        half = marker_size_m / 2.0
        object_points = np.array([[-half,-half,0.0],[half,-half,0.0],[half,half,0.0],[-half,half,0.0]], dtype=np.float64)
        camera_matrix = np.array(calibration.camera_matrix, dtype=np.float64); dist_coeffs = np.array(calibration.distortion_coefficients, dtype=np.float64)
        ok, rvec, tvec = cv2.solvePnP(object_points, image_points, camera_matrix, dist_coeffs, flags=cv2.SOLVEPNP_IPPE_SQUARE)
        if not ok: return None, None, None, None, None
        rotation_matrix, _ = cv2.Rodrigues(rvec); roll, pitch, yaw = self._rotation_matrix_to_rpy(rotation_matrix)
        error_px = self._compute_reprojection_error(object_points, image_points, rvec, tvec, camera_matrix, dist_coeffs)
        quality = 'GOOD' if error_px <= 1.5 else ('WARN' if error_px <= 4.0 else 'BAD')
        pose = Pose3D(x=float(tvec[0][0]), y=float(tvec[1][0]), z=float(tvec[2][0]), roll=roll, pitch=pitch, yaw=yaw)
        return pose, tvec.flatten().tolist(), rvec.flatten().tolist(), error_px, quality
    def _prepare_work_image(self, frame_bgr: np.ndarray, roi: ROI | None) -> tuple[np.ndarray,int,int]:
        if roi is None: return frame_bgr, 0, 0
        return frame_bgr[roi.y:roi.y+roi.height, roi.x:roi.x+roi.width], roi.x, roi.y
    def _detect_apriltag(self, frame_bgr: np.ndarray, calibration: CameraCalibration, roi: ROI | None) -> List[VisualMarker]:
        markers=[]
        if not self.apriltag_enabled: return markers
        work, ox, oy = self._prepare_work_image(frame_bgr, roi); gray = cv2.cvtColor(work, cv2.COLOR_BGR2GRAY); tags = self.apriltag_detector.detect(gray, estimate_tag_pose=False)
        for tag in tags:
            image_points = np.array([[tag.corners[0][0]+ox, tag.corners[0][1]+oy],[tag.corners[1][0]+ox, tag.corners[1][1]+oy],[tag.corners[2][0]+ox, tag.corners[2][1]+oy],[tag.corners[3][0]+ox, tag.corners[3][1]+oy]], dtype=np.float64)
            pose,tvec,rvec,err,q = self._estimate_pose_from_square(image_points, calibration, self.apriltag_size_m)
            markers.append(VisualMarker(tag_id=int(tag.tag_id), family=f'APRILTAG::{tag.tag_family}', center=(float(tag.center[0]+ox), float(tag.center[1]+oy)), corners=[(float(pt[0]+ox), float(pt[1]+oy)) for pt in tag.corners], decision_margin=float(tag.decision_margin), hamming=int(tag.hamming), pose=pose, translation_vector=tvec, rotation_vector=rvec, reprojection_error_px=err, pose_quality=q))
        return markers
    def _detect_qr(self, frame_bgr: np.ndarray, calibration: CameraCalibration, roi: ROI | None) -> List[VisualMarker]:
        markers=[]
        if not self.qr_enabled: return markers
        work, ox, oy = self._prepare_work_image(frame_bgr, roi); ok, _, points, _ = self.qr_detector.detectAndDecodeMulti(work)
        if not ok or points is None: return markers
        for idx, quad in enumerate(points):
            quad = np.array(quad, dtype=np.float64)
            image_points = np.array([[quad[0][0]+ox, quad[0][1]+oy],[quad[1][0]+ox, quad[1][1]+oy],[quad[2][0]+ox, quad[2][1]+oy],[quad[3][0]+ox, quad[3][1]+oy]], dtype=np.float64)
            pose,tvec,rvec,err,q = self._estimate_pose_from_square(image_points, calibration, self.apriltag_size_m)
            center = tuple(map(float, np.mean(image_points, axis=0)))
            markers.append(VisualMarker(tag_id=idx, family='QRCODE', center=center, corners=[tuple(map(float, pt)) for pt in image_points], pose=pose, translation_vector=tvec, rotation_vector=rvec, reprojection_error_px=err, pose_quality=q))
        return markers
    def _detect_cctag(self, frame_bgr: np.ndarray, calibration: CameraCalibration, roi: ROI | None) -> List[VisualMarker]:
        if not self.cctag_enabled: return []
        warn('Integracja CCTag nie jest jeszcze gotowa. Pomijam ten typ znacznika.')
        # TODO: podpiąć rzeczywistą bibliotekę / bindingi CCTag.
        return []
    def detect(self, frame_bgr: np.ndarray, calibration: CameraCalibration, roi: ROI | None = None) -> List[VisualMarker]:
        info('Rozpoczynam wielomodalną detekcję markerów wizyjnych...')
        markers=[]; markers.extend(self._detect_apriltag(frame_bgr, calibration, roi)); markers.extend(self._detect_qr(frame_bgr, calibration, roi)); markers.extend(self._detect_cctag(frame_bgr, calibration, roi)); info(f'Łączna liczba markerów: {len(markers)}'); return markers
