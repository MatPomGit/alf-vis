from __future__ import annotations
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2
from std_msgs.msg import String
from common.models import AppConfig, PerceptionSnapshot
from perception.publishers import PublisherFactory
class PerceptionRosNode(Node):
    def __init__(self, config: AppConfig) -> None:
        super().__init__('robot_perception_node')
        self.state_publisher = self.create_publisher(String, config.perception_state_topic, 10)
        self.point_cloud_publisher = self.create_publisher(PointCloud2, config.point_cloud_topic, 10)
    def publish_snapshot(self, snapshot: PerceptionSnapshot) -> None:
        self.state_publisher.publish(PublisherFactory.snapshot_to_string(snapshot))
    def publish_point_cloud(self, snapshot: PerceptionSnapshot) -> None:
        self.point_cloud_publisher.publish(PublisherFactory.point_cloud_to_msg(snapshot.point_cloud, frame_id=snapshot.point_cloud.coordinate_frame))
