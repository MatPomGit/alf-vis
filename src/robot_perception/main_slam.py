from __future__ import annotations


def main() -> None:
    """Punkt wejścia niezależnej warstwy SLAM-bridge.

    Importy ROS2 są wykonywane dopiero tutaj, aby samo załadowanie pliku
    nie wymagało środowiska ROS2.
    """
    import rclpy

    from common.ros_runtime import SharedRosContext
    from common.utils import load_config
    from slam.console import info
    from slam.ros2_node import SlamRosNode
    from slam.slam_runtime import SlamRuntime

    config = load_config("config/settings.yaml")
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