#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Point


class PositionPublisher(Node):
    def __init__(self):
        super().__init__('position_publisher')

        # Parametr: okres publikacji [s]
        self.declare_parameter('dt', 0.1)
        dt = self.get_parameter('dt').value

        # Nowy topic ROS2
        self.publisher_ = self.create_publisher(Point, '/object_position', 10)

        # Timer wywoływany co dt sekund
        self.timer = self.create_timer(dt, self.timer_callback)

        # Przykładowa pozycja początkowa
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0

        self.get_logger().info(f'Start publikacji na /object_position co {dt:.3f} s')

    def get_current_position(self):
        """
        Tu podmień logikę pobierania aktualnej pozycji obiektu.
        Na razie: przykład, który zmienia pozycję w czasie.
        """
        self.x += 0.01
        self.y += 0.02
        self.z += 0.00
        return self.x, self.y, self.z

    def timer_callback(self):
        x, y, z = self.get_current_position()

        msg = Point()
        msg.x = x
        msg.y = y
        msg.z = z

        self.publisher_.publish(msg)
        self.get_logger().info(f'Published: x={x:.3f}, y={y:.3f}, z={z:.3f}')


def main(args=None):
    rclpy.init(args=args)
    node = PositionPublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()