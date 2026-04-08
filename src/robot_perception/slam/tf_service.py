from __future__ import annotations
from typing import Optional
from rclpy.duration import Duration
from rclpy.node import Node
from rclpy.time import Time
import tf2_ros
from transforms3d.euler import quat2euler
from common.models import Pose3D
from slam.console import info, warn
class TfService:
    def __init__(self, node: Node) -> None:
        self.node = node
        self.buffer = tf2_ros.Buffer()
        self.listener = tf2_ros.TransformListener(self.buffer, node)
        info("Zainicjalizowano TF2.")
    def lookup_pose(self, target_frame: str, source_frame: str, timeout_sec: float = 0.2) -> Optional[Pose3D]:
        try:
            transform = self.buffer.lookup_transform(target_frame, source_frame, Time(), timeout=Duration(seconds=timeout_sec))
        except Exception as exc:
            warn(f"Brak transformacji {source_frame}->{target_frame}: {exc}")
            return None
        t = transform.transform.translation
        q = transform.transform.rotation
        roll, pitch, yaw = quat2euler([q.w, q.x, q.y, q.z], axes='sxyz')
        return Pose3D(x=float(t.x), y=float(t.y), z=float(t.z), roll=float(roll), pitch=float(pitch), yaw=float(yaw))
    def can_transform(self, target_frame: str, source_frame: str, timeout_sec: float = 0.2) -> bool:
        try:
            return self.buffer.can_transform(target_frame, source_frame, Time(), timeout=Duration(seconds=timeout_sec))
        except Exception:
            return False
