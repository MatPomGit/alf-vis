from __future__ import annotations

from typing import Optional

from geometry_msgs.msg import Pose as RosPose
from nav_msgs.msg import Odometry
import rclpy
from rclpy.node import Node

from common.models import Pose3D, SlamStatus

try:
    from rtabmap_msgs.msg import Info, MapData, OdomInfo
except Exception:
    Info = None
    MapData = None
    OdomInfo = None


class RTABMapRosBridge:
    """Adapter pobierający stan RTAB-Map z topiców ROS2.

    To jest jedyna warstwa odpowiedzialna za komunikację z RTAB-Map.
    FSM dostaje już gotowy, zmapowany `SlamStatus`.
    """

    def __init__(
        self,
        node: Node,
        odom_info_topic: str,
        map_data_topic: str,
        info_topic: str,
    ) -> None:
        self.node = node

        self.last_pose: Optional[Pose3D] = None
        self.last_map_point_count: int = 0
        self.last_odom_lost: bool = False
        self.last_inliers: int = 0
        self.last_matches: int = 0
        self.last_localization_id: int = 0
        self.last_loop_closure_id: int = 0
        self.initialized = False

        if OdomInfo is not None:
            self.node.create_subscription(OdomInfo, odom_info_topic, self._on_odom_info, 10)
        if MapData is not None:
            self.node.create_subscription(MapData, map_data_topic, self._on_map_data, 10)
        if Info is not None:
            self.node.create_subscription(Info, info_topic, self._on_info, 10)

        # TODO: dodać fallback na inne topici RTAB-Map, jeśli konkretna konfiguracja robota ich używa.

    def _on_odom_info(self, msg) -> None:
        """Obsługuje wiadomości odometrii RTAB-Map."""
        self.last_odom_lost = bool(getattr(msg, "lost", False))
        self.last_inliers = int(getattr(msg, "inliers", 0))
        self.last_matches = int(getattr(msg, "matches", 0))
        self.initialized = True

        transform = getattr(msg, "transform", None)
        if transform is not None:
            translation = transform.translation
            self.last_pose = Pose3D(
                x=float(translation.x),
                y=float(translation.y),
                z=float(translation.z),
            )

    def _on_map_data(self, msg) -> None:
        """Obsługuje stan mapy RTAB-Map."""
        nodes = getattr(msg, "nodes", [])
        self.last_map_point_count = len(nodes)
        self.initialized = True

    def _on_info(self, msg) -> None:
        """Obsługuje dodatkowe informacje lokalizacyjne RTAB-Map."""
        self.last_localization_id = int(getattr(msg, "proximity_detection_id", 0))
        self.last_loop_closure_id = int(getattr(msg, "loop_closure_id", 0))
        self.initialized = True

    def get_status(self) -> SlamStatus:
        """Mapuje ostatni znany stan topiców RTAB-Map do `SlamStatus`."""
        status = "UPDATED" if self.initialized else "WAITING_FOR_RTABMAP"
        return SlamStatus(
            initialized=self.initialized,
            status=status,
            pose=self.last_pose,
            map_point_count=self.last_map_point_count,
            odom_lost=self.last_odom_lost,
            inliers=self.last_inliers,
            matches=self.last_matches,
            localization_id=self.last_localization_id,
            loop_closure_id=self.last_loop_closure_id,
            database_path=None,
        )