from __future__ import annotations
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2
from std_msgs.msg import String
from common.models import AppConfig, PerceptionSnapshot
from perception.publishers import PublisherFactory


class PerceptionRosNode(Node):
    """Node ROS2 odpowiedzialny za publikację stanu percepcji i chmury punktów."""

    def __init__(self, config: AppConfig) -> None:
        super().__init__("robot_perception_node")
        self.config = config
        self.state_publisher = self.create_publisher(String, config.perception_state_topic, 10)
        self.point_cloud_publisher = self.create_publisher(PointCloud2, config.point_cloud_topic, 10)

        # TODO: dodać subscriberów do topiców RTAB-Map, jeśli odczyt SLAM ma iść wyłącznie przez ROS2.
        # TODO: dodać diagnostykę ROS2 i heartbeat node.

    def publish_snapshot(self, snapshot: PerceptionSnapshot) -> None:
        """Publikuje pełny stan percepcji."""
        self.state_publisher.publish(PublisherFactory.snapshot_to_string(snapshot))

    def publish_point_cloud(self, snapshot: PerceptionSnapshot) -> None:
        """Publikuje chmurę punktów."""
        self.point_cloud_publisher.publish(
            PublisherFactory.point_cloud_to_msg(
                snapshot.point_cloud,
                frame_id=snapshot.point_cloud.coordinate_frame,
            )
        )




""" 
from __future__ import annotations
from typing import Optional
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2
from std_msgs.msg import String
from common.models import AppConfig, PerceptionSnapshot
from perception.publishers import PublisherFactory


class PerceptionRosNode(Node):
    ""Node ROS2 odpowiedzialny za publikację stanu percepcji i chmury punktów.""

    def __init__(self, config: AppConfig) -> None:
        super().__init__("robot_perception_node")
        self.config = config

        self.state_publisher = self.create_publisher(String, config.perception_state_topic, 10)
        self.point_cloud_publisher = self.create_publisher(PointCloud2, config.point_cloud_topic, 10)

        # TODO: dodać subscriberów do topiców RTAB-Map, jeśli odczyt SLAM ma iść wyłącznie przez ROS2.
        # TODO: dodać diagnostykę ROS2 i heartbeat node.

    def publish_snapshot(self, snapshot: PerceptionSnapshot) -> None:
        ""Publikuje stan percepcji jako JSON na topicu ROS2.""
        msg = PublisherFactory.snapshot_to_string(snapshot)
        self.state_publisher.publish(msg)

    def publish_point_cloud(self, snapshot: PerceptionSnapshot) -> None:
        ""Publikuje chmurę punktów na topicu ROS2.""
        msg = PublisherFactory.point_cloud_to_msg(snapshot.point_cloud, frame_id=snapshot.point_cloud.coordinate_frame)
        self.point_cloud_publisher.publish(msg)
 """