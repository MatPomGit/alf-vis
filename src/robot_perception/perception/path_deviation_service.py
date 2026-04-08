from __future__ import annotations

from common.models import Pose3D

class PathDeviationService:
    """Usługa sprawdzania odchylenia od planowanej ścieżki."""

    def __init__(self, y_tolerance: float = 0.5) -> None:
        self.y_tolerance = y_tolerance

    def check(self, pose: Pose3D | None) -> tuple[bool, float]:
        """Sprawdza odchylenie od ścieżki."""
        if pose is None:
            return False, 0.0

        deviation = abs(pose.y)
        return deviation > self.y_tolerance, float(deviation)

    # TODO: zintegrować z globalnym plannerem Nav2 i prawdziwą trajektorią referencyjną.





""" from __future__ import annotations
from common.protocol import read_stdin_json, write_stdout_json, ok_response

def main() -> None:
    payload = read_stdin_json()
    slam_pose = payload.get("slam_pose") or {"y": 0.0}
    deviation = abs(float(slam_pose.get("y", 0.0)))

    write_stdout_json(
        ok_response(
            path_deviation_detected=deviation > 0.5,
            path_deviation_value=deviation,
        )
    )

if __name__ == "__main__":
    main() """

""" 
import json
import sys
def main() -> None:
    payload = json.load(sys.stdin)
    slam_pose = payload.get("slam_pose") or {"x": 0.0, "y": 0.0, "theta": 0.0}

    deviation = abs(float(slam_pose.get("y", 0.0)))
    response = {
        "status": "ok",
        "path_deviation_detected": deviation > 0.5,
        "path_deviation_value": deviation
    }
    print(json.dumps(response, ensure_ascii=False))
 """