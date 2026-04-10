from __future__ import annotations

import argparse

from common.env_guard import env_guard_enabled, validate_host_conda_env
from common.versioning import get_version_banner


def parse_args() -> argparse.Namespace:
    """Parsuje argumenty startowe programu SLAM."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--version",
        action="version",
        version=get_version_banner(),
    )
    parser.add_argument(
        "--guard-env",
        action="store_true",
        help=(
            "Wymusza walidację środowiska Conda poza kontenerem. "
            "Można też użyć flagi środowiskowej ROBOT_PERCEPTION_ENV_GUARD=1."
        ),
    )
    return parser.parse_args()


def main() -> None:
    """Punkt wejścia niezależnej warstwy SLAM-bridge.

    Importy ROS2 są wykonywane dopiero tutaj, aby samo załadowanie pliku
    nie wymagało środowiska ROS2.
    """
    from common.utils import load_config

    args = parse_args()
    if args.guard_env or env_guard_enabled():
        is_valid, message = validate_host_conda_env()
        if not is_valid:
            raise RuntimeError(f"[ENV_GUARD] {message}")

    config = load_config("config/settings.yaml")

    import rclpy
    from common.ros_runtime import SharedRosContext
    from slam.console import info
    from slam.ros2_node import SlamRosNode
    from slam.slam_runtime import SlamRuntime

    SharedRosContext.ensure_initialized()
    node = SlamRosNode(config)
    runtime = SlamRuntime(config, node)

    info("Uruchomiono niezależny proces SLAM-bridge.")
    try:
        while rclpy.ok():
            rclpy.spin_once(node, timeout_sec=0.05)
            runtime.step()
    finally:
        node.destroy_node()
        SharedRosContext.shutdown()
        info("Proces SLAM-bridge został poprawnie zatrzymany.")


if __name__ == "__main__":
    main()
