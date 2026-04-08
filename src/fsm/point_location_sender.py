# https://docs.ros.org/en/humble/Tutorials/Beginner-Client-Libraries/Creating-A-Workspace/Creating-A-Workspace.html#new-directory
# https://docs.ros.org/en/humble/Tutorials/Beginner-Client-Libraries/Writing-A-Simple-Py-Publisher-And-Subscriber.html
# https://docs.ros.org/en/iron/p/rclpy/rclpy.task.html

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PointStamped

class PointLocationSender(Node):
    
    def __init__(self):
        super().__init__('send_point_location') # Initializes ROS2 node with unique name
        self.publisher_ = self.create_publisher(PointStamped, '/my_point', 10) # sets up ROS2 publisher
        self.timer = self.create_timer(0.5, self.timer_callback)  # Calls timer_callback every 0.5 seconds (2 Hz)

    
    def timer_callback(self):
        msg = PointStamped() # creates a new ROS2 message of type PointStamped
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "odom"
        msg.point.x = 1.0
        msg.point.y = 2.0
        msg.point.z = 0.0
        self.publisher_.publish(msg) # publishes the message
        self.get_logger().info(f'Publishing: [{msg.point.x}, {msg.point.y}, {msg.point.z}]') # log to the console



def main(args=None):
    rclpy.init(args=args) # Initializes the ROS2 Python client library
    node = PointLocationSender() # Creates an instance of our custom node class
    rclpy.spin(node) # Keeps the node running 
    node.destroy_node() # Cleans up the node
    rclpy.shutdown() # Shuts down the ROS2 Python client library


if __name__ == '__main__':
    main()