from __future__ import annotations

from common.models import CameraCalibration
from common.utils import load_camera_calibration


class CameraCalibrationService:
    """Usługa ładowania i udostępniania parametrów kalibracji kamery."""

    def __init__(self, calibration_file: str) -> None:
        self.calibration_file = calibration_file
        self._calibration = load_camera_calibration(calibration_file)

    @property
    def calibration(self) -> CameraCalibration:
        """Zwraca kalibrację kamery."""
        return self._calibration