from __future__ import annotations
import argparse
import rclpy
from common.ros_runtime import SharedRosContext
from common.utils import load_config
from perception.console import info
from perception.ros2_node import PerceptionRosNode
from perception.state_machine import RobotPerceptionStateMachine

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", choices=["rgbd", "rgb"], default=None)
    parser.add_argument("--config", default="config/settings.yaml")
    return parser.parse_args()

def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    selected_source = args.source or config.default_camera_source
    SharedRosContext.ensure_initialized()
    node = PerceptionRosNode(config)
    machine = RobotPerceptionStateMachine(config, node, selected_source=selected_source)
    info(f"Uruchomiono percepcję. Źródło: {selected_source}")
    try:
        while rclpy.ok():
            machine.run_once()
            rclpy.spin_once(node, timeout_sec=0.01)
    finally:
        machine.shutdown()
        node.destroy_node()
        SharedRosContext.shutdown()
        info("Percepcja zatrzymana.")

if __name__ == "__main__":
    main()
