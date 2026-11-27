import rclpy
from rclpy.node import Node
from tutorial_interfaces.msg import Num


class MinimalSubscriber(Node):
    """Subscribe to numeric ROS messages."""

    def __init__(self) -> None:
        super().__init__("minimal_subscriber")
        self.subscription = self.create_subscription(
            Num,
            "topic",
            self.listener_callback,
            10,
        )

    def listener_callback(self, msg: Num) -> None:
        """Log a received message."""
        self.get_logger().info(f'I heard: "{msg.num}"')


def main(args: list[str] | None = None) -> None:
    """Run the ROS subscriber and release resources on exit."""
    rclpy.init(args=args)
    node = None
    try:
        node = MinimalSubscriber()
        rclpy.spin(node)
    finally:
        if node is not None:
            node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
