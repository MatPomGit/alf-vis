from __future__ import annotations
from common.models import Pose3D
class PathDeviationService:
    def __init__(self, y_tolerance: float=0.5) -> None:
        self.y_tolerance = y_tolerance
    def check(self, pose: Pose3D | None) -> tuple[bool,float]:
        if pose is None: return False, 0.0
        deviation = abs(pose.y); return deviation > self.y_tolerance, float(deviation)
