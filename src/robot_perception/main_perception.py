from __future__ import annotations

import argparse


def parse_args() -> argparse.Namespace:
    """Parsuje argumenty startowe programu percepcji."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source",
        choices=["rgbd", "rgb"],
        default=None,
        help="Wybór źródła kamer na starcie programu. 'rgbd' próbuje użyć RGB + depth, 'rgb' wymusza tryb bez depth.",
    )
    parser.add_argument("--config", default="config/settings.yaml")
    return parser.parse_args()


def main() -> None:
    """Punkt wejścia niezależnej warstwy percepcji.

    Importy ROS2 są wykonywane dopiero tutaj, aby samo załadowanie pliku
    nie wymagało środowiska ROS2.
    """
    import rclpy

    from common.ros_runtime import SharedRosContext
    from common.utils import load_config
    from perception.console import info
    from perception.ros2_node import PerceptionRosNode
    from perception.state_machine import RobotPerceptionStateMachine

    args = parse_args()
    config = load_config(args.config)
    selected_source = args.source or config.default_camera_source

    SharedRosContext.ensure_initialized()
    node = PerceptionRosNode(config)
    machine = RobotPerceptionStateMachine(config, node, selected_source=selected_source)

    info(f"Uruchomiono niezależny proces percepcji. Wybrane źródło: {selected_source}")
    try:
        while rclpy.ok():
            machine.run_once()
            rclpy.spin_once(node, timeout_sec=0.01)
    finally:
        machine.shutdown()
        node.destroy_node()
        SharedRosContext.shutdown()
        info("Proces percepcji został poprawnie zatrzymany.")
        print("Proces percepcji został poprawnie zatrzymany")


if __name__ == "__main__":
    main()