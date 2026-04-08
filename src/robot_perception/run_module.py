from __future__ import annotations
import argparse
import rclpy
from common.utils import load_config
from perception.april_tag_service import AprilTagService
from perception.camera_calibration_service import CameraCalibrationService
from perception.camera_service import CameraService
from perception.point_cloud_service import PointCloudService
from perception.rgbd_service import RGBDService
from perception.ros2_node import PerceptionRosNode
from perception.rtabmap_ros_bridge import RTABMapRosBridge


def run_apriltag(config_path: str) -> None:
    """Uruchamia tylko detekcję AprilTag na jednej ramce."""
    config = load_config(config_path)
    camera = CameraService(config.camera_id, config.camera_width, config.camera_height, config.output_dir)
    calibration = CameraCalibrationService(config.calibration_file).calibration
    service = AprilTagService(config.april_tag_family, config.april_tag_size_m)

    frame, path, _ = camera.capture(frame_id=1)
    markers = service.detect(frame, calibration)
    print([m.model_dump() for m in markers])
    camera.close()


def run_rgbd(config_path: str) -> None:
    """Uruchamia tylko przechwycenie RGB-D i budowę chmury punktów."""
    config = load_config(config_path)
    camera = CameraService(config.camera_id, config.camera_width, config.camera_height, config.output_dir)
    depth = RGBDService(config.depth_camera_id, config.camera_width, config.camera_height, config.output_dir)
    calibration = CameraCalibrationService(config.calibration_file).calibration
    pc_service = PointCloudService(config.output_dir)

    frame, _, _ = camera.capture(frame_id=1)
    depth_frame, _, depth_meta = depth.capture_depth(frame_id=1)
    cloud = pc_service.build_from_rgbd(frame, depth_frame, calibration, depth_meta.depth_scale)
    print({"point_count": cloud.point_count})

    camera.close()
    depth.close()


def run_rtabmap_bridge(config_path: str) -> None:
    """Uruchamia tylko adapter RTAB-Map i wypisuje jego stan."""
    config = load_config(config_path)
    rclpy.init()
    node = PerceptionRosNode(config)
    bridge = RTABMapRosBridge(
        node=node,
        odom_info_topic=config.rtabmap_odom_topic,
        map_data_topic=config.rtabmap_mapdata_topic,
        info_topic=config.rtabmap_localization_topic,
    )

    try:
        for _ in range(20):
            rclpy.spin_once(node, timeout_sec=0.1)
        print(bridge.get_status().model_dump())
    finally:
        node.destroy_node()
        rclpy.shutdown()


def main() -> None:
    """CLI do uruchamiania pojedynczych modułów."""
    parser = argparse.ArgumentParser()
    parser.add_argument("module", choices=["apriltag", "rgbd", "rtabmap_bridge"])
    parser.add_argument("--config", default="config/settings.yaml")
    args = parser.parse_args()

    if args.module == "apriltag":
        run_apriltag(args.config)
    elif args.module == "rgbd":
        run_rgbd(args.config)
    elif args.module == "rtabmap_bridge":
        run_rtabmap_bridge(args.config)


if __name__ == "__main__":
    main()