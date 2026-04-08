from __future__ import annotations
import rclpy
from common.ros_runtime import SharedRosContext
from common.utils import load_config
from slam.console import info
from slam.ros2_node import SlamRosNode
from slam.slam_runtime import SlamRuntime

def main() -> None:
    config = load_config("config/settings.yaml")
    SharedRosContext.ensure_initialized()
    node = SlamRosNode(config)
    runtime = SlamRuntime(config, node)
    info("Uruchomiono SLAM bridge.")
    try:
        while rclpy.ok():
            rclpy.spin_once(node, timeout_sec=0.05)
            runtime.step()
    finally:
        node.destroy_node()
        SharedRosContext.shutdown()
        info("SLAM bridge zatrzymany.")

if __name__ == "__main__":
    main()
