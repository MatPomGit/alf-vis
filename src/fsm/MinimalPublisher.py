"""ROS 2 numeric message publisher."""

import rclpy
from rclpy.node import Node
from tutorial_interfaces.msg import Num  # CHANGE


class MinimalPublisher(Node):
    """ROS 2 numeric message publisher."""
    def __init__(self) -> None:
        super().__init__("minimal_publisher")
        self.publisher_ = self.create_publisher(Num, "topic", 10)  # CHANGE
        timer_period = 0.5
        self.timer = self.create_timer(timer_period, self.timer_callback)
        self.i = 0

    def timer_callback(self) -> None:
        """Publish the next message."""
        msg = Num()  # CHANGE
        msg.num = self.i  # CHANGE
        self.publisher_.publish(msg)
        self.get_logger().info(f'Publishing: "{msg.num}"')  # CHANGE
        self.i += 1


def main(args: list[str] | None = None) -> None:
    """Initialize ROS, run the node and shut down."""
    rclpy.init(args=args)

    minimal_publisher = MinimalPublisher()

    rclpy.spin(minimal_publisher)

    minimal_publisher.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
