# https://docs.ros.org/en/humble/Tutorials/Beginner-Client-Libraries/Writing-A-Simple-Py-Publisher-And-Subscriber.html

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PointStamped

class PointLocationReceiver(Node):
    
    def __init__(self):
        super().__init__('receive_point_location')
        self.subscription = self.create_subscription(
            PointStamped,
            '/my_point',
            self.listener_callback,
            10)

    
    def listener_callback(self, msg):
        self.get_logger().info(f'Received: [{msg.point.x:.2f}, {msg.point.y:.2f}, {msg.point.z:.2f}]')


def main(args=None):
    rclpy.init(args=args)
    node = PointLocationReceiver()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()