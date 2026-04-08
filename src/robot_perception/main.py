from __future__ import annotations
import rclpy
from common.utils import load_config
from perception.ros2_node import PerceptionRosNode
from perception.state_machine import RobotPerceptionStateMachine


def main() -> None:
    """Punkt wejścia pełnej aplikacji percepcji."""
    config = load_config("config/settings.yaml")

    rclpy.init()
    node = PerceptionRosNode(config)
    machine = RobotPerceptionStateMachine(config, node)

    try:
        while rclpy.ok():
            machine.run_once()
            rclpy.spin_once(node, timeout_sec=0.01)
    finally:
        machine.shutdown()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()