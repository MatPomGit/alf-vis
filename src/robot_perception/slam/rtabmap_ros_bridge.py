from __future__ import annotations
from rclpy.node import Node
from common.models import SlamStatus
from slam.console import info, warn
from slam.tf_service import TfService
try:
    from rtabmap_msgs.msg import OdomInfo, Info, MapData
except Exception:
    OdomInfo = None
    Info = None
    MapData = None
class RTABMapRosBridge:
    def __init__(self, node: Node, tf_service: TfService, odom_info_topic: str='/rtabmap/odom_info', map_data_topic: str='/rtabmap/mapData', info_topic: str='/rtabmap/info', map_frame: str='map', odom_frame: str='odom', camera_frame: str='camera_link') -> None:
        self.node = node; self.tf_service = tf_service; self.map_frame = map_frame; self.odom_frame = odom_frame; self.camera_frame = camera_frame
        self.last_map_point_count = 0; self.last_odom_lost = False; self.last_inliers = 0; self.last_matches = 0; self.last_localization_id = 0; self.last_loop_closure_id = 0; self.initialized = False
        info(f"Podpinanie RTAB-Map do topiców: {odom_info_topic}, {map_data_topic}, {info_topic}")
        if OdomInfo is not None: node.create_subscription(OdomInfo, odom_info_topic, self._on_odom_info, 10)
        else: warn('Brak rtabmap_msgs/OdomInfo')
        if MapData is not None: node.create_subscription(MapData, map_data_topic, self._on_map_data, 10)
        else: warn('Brak rtabmap_msgs/MapData')
        if Info is not None: node.create_subscription(Info, info_topic, self._on_info, 10)
        else: warn('Brak rtabmap_msgs/Info')
    def _on_odom_info(self, msg) -> None:
        self.last_odom_lost = bool(msg.lost); self.last_inliers = int(msg.inliers); self.last_matches = int(msg.matches); self.initialized = True
    def _on_map_data(self, msg) -> None:
        self.last_map_point_count = len(msg.nodes); self.initialized = True
    def _on_info(self, msg) -> None:
        self.last_localization_id = int(getattr(msg, 'proximity_detection_id', 0)); self.last_loop_closure_id = int(getattr(msg, 'loop_closure_id', 0)); self.initialized = True
    def get_status(self) -> SlamStatus:
        pose = self.tf_service.lookup_pose(self.map_frame, self.camera_frame)
        return SlamStatus(initialized=self.initialized, status='UPDATED' if self.initialized else 'WAITING_FOR_RTABMAP', pose=pose, map_point_count=self.last_map_point_count, odom_lost=self.last_odom_lost, inliers=self.last_inliers, matches=self.last_matches, localization_id=self.last_localization_id, loop_closure_id=self.last_loop_closure_id, map_to_odom_available=self.tf_service.can_transform(self.map_frame, self.odom_frame), camera_to_map_available=self.tf_service.can_transform(self.map_frame, self.camera_frame))
