"""ROS 2 asynchronous service client."""

import sys

import rclpy
from rclpy.node import Node
from tutorial_interfaces.srv import AddThreeInts  # CHANGE


class MinimalClientAsync(Node):
    """ROS 2 asynchronous service client."""
    def __init__(self) -> None:
        super().__init__("minimal_client_async")
        self.cli = self.create_client(AddThreeInts, "add_three_ints")  # CHANGE
        while not self.cli.wait_for_service(timeout_sec=1.0):
            self.get_logger().info("service not available, waiting again...")
        self.req = AddThreeInts.Request()  # CHANGE

    def send_request(self) -> None:
        """Send an asynchronous addition request."""
        self.req.a = int(sys.argv[1])
        self.req.b = int(sys.argv[2])
        self.req.c = int(sys.argv[3])  # CHANGE
        self.future = self.cli.call_async(self.req)


def main(args: list[str] | None = None) -> None:
    """Initialize ROS, run the node and shut down."""
    rclpy.init(args=args)

    minimal_client = MinimalClientAsync()
    minimal_client.send_request()

    while rclpy.ok():
        rclpy.spin_once(minimal_client)
        if minimal_client.future.done():
            try:
                response = minimal_client.future.result()
            except Exception as e:
                minimal_client.get_logger().info(f"Service call failed {e!r}")
            else:
                minimal_client.get_logger().info(
                    f"Result of add_three_ints: for {minimal_client.req.a} + "
                    f"{minimal_client.req.b} + {minimal_client.req.c} = {response.sum}"
                )  # CHANGE
            break

    minimal_client.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
