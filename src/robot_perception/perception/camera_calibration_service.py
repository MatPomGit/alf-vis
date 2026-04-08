from __future__ import annotations
from common.models import CameraCalibration
from common.utils import load_camera_calibration
class CameraCalibrationService:
    def __init__(self, calibration_file: str) -> None:
        self._calibration = load_camera_calibration(calibration_file)
    @property
    def calibration(self) -> CameraCalibration:
        return self._calibration
