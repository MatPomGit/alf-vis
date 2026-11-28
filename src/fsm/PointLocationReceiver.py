"""ROS 2 stamped point receiver."""

# https://docs.ros.org/en/humble/Tutorials/Beginner-Client-Libraries/Writing-A-Simple-Py-Publisher-And-Subscriber.html

import rclpy
from geometry_msgs.msg import PointStamped
from rclpy.node import Node


class PointLocationReceiver(Node):
    """ROS 2 stamped point receiver."""
    def __init__(self) -> None:
        super().__init__("receive_point_location")
        self.subscription = self.create_subscription(
            PointStamped, "/my_point", self.listener_callback, 10
        )

    def listener_callback(self, msg: PointStamped) -> None:
        """Log a received point."""
        self.get_logger().info(
            f"Received: [{msg.point.x:.2f}, {msg.point.y:.2f}, {msg.point.z:.2f}]"
        )


def main(args: list[str] | None = None) -> None:
    """Initialize ROS, run the node and shut down."""
    rclpy.init(args=args)
    node = PointLocationReceiver()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
