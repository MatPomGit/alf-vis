from __future__ import annotations
from rclpy.node import Node
from std_msgs.msg import String
from common.models import AppConfig, SlamStatus
from slam.console import info
class SlamRosNode(Node):
    def __init__(self, config: AppConfig) -> None:
        super().__init__('robot_slam_bridge_node')
        self.status_publisher = self.create_publisher(String, '/slam/status', 10)
        info('Utworzono node SLAM bridge.')
    def publish_status(self, status: SlamStatus) -> None:
        msg = String(); msg.data = status.model_dump_json(); self.status_publisher.publish(msg)
