from __future__ import annotations
from common.models import AppConfig
from slam.console import info
from slam.ros2_node import SlamRosNode
from slam.rtabmap_ros_bridge import RTABMapRosBridge
from slam.tf_service import TfService
class SlamRuntime:
    def __init__(self, config: AppConfig, node: SlamRosNode) -> None:
        self.node = node
        self.tf_service = TfService(node)
        self.bridge = RTABMapRosBridge(node=node, tf_service=self.tf_service, odom_info_topic=config.rtabmap_odom_topic, map_data_topic=config.rtabmap_mapdata_topic, info_topic=config.rtabmap_localization_topic)
        info('Runtime SLAM uruchomiony.')
    def step(self) -> None:
        status = self.bridge.get_status()
        info(f"Stan RTAB-Map: initialized={status.initialized}, map_point_count={status.map_point_count}, camera_to_map_available={status.camera_to_map_available}")
        self.node.publish_status(status)
