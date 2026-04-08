from __future__ import annotations
import argparse
import rclpy
from common.ros_runtime import SharedRosContext
from common.utils import load_config
from perception.camera_calibration_service import CameraCalibrationService
from perception.camera_service import CameraService
from perception.point_cloud_service import PointCloudService
from perception.rgbd_service import RGBDService
from perception.visual_marker_service import VisualMarkerService
from slam.ros2_node import SlamRosNode
from slam.rtabmap_ros_bridge import RTABMapRosBridge
from slam.tf_service import TfService

def run_markers(config_path: str) -> None:
    config = load_config(config_path)
    camera = CameraService(config.camera_id, config.camera_width, config.camera_height, config.output_dir)
    calibration = CameraCalibrationService(config.calibration_file).calibration
    service = VisualMarkerService(
        apriltag_family=config.april_tag_family,
        apriltag_size_m=config.april_tag_size_m,
        apriltag_enabled=config.apriltag_enabled,
        cctag_enabled=config.cctag_enabled,
        qr_enabled=config.qr_enabled,
    )
    frame, _, _ = camera.capture(frame_id=1)
    markers = service.detect(frame, calibration)
    print([m.model_dump() for m in markers])
    camera.close()

def run_rgbd(config_path: str) -> None:
    config = load_config(config_path)
    camera = CameraService(config.camera_id, config.camera_width, config.camera_height, config.output_dir)
    depth = RGBDService(config.depth_camera_id, config.camera_width, config.camera_height, config.output_dir)
    calibration = CameraCalibrationService(config.calibration_file).calibration
    pc_service = PointCloudService(config.output_dir)
    frame, _, _ = camera.capture(frame_id=1)
    if depth.is_available():
        depth_frame, _, depth_meta = depth.capture_depth(frame_id=1)
        cloud = pc_service.build_from_rgbd(frame, depth_frame, calibration, depth_meta.depth_scale)
    else:
        cloud = pc_service.build_sparse_from_rgb_only(frame, calibration)
    print({"point_count": cloud.point_count, "frame": cloud.coordinate_frame})
    camera.close(); depth.close()

def run_rtabmap_bridge(config_path: str) -> None:
    config = load_config(config_path)
    SharedRosContext.ensure_initialized()
    node = SlamRosNode(config)
    tf_service = TfService(node)
    bridge = RTABMapRosBridge(node=node, tf_service=tf_service,
                              odom_info_topic=config.rtabmap_odom_topic,
                              map_data_topic=config.rtabmap_mapdata_topic,
                              info_topic=config.rtabmap_localization_topic)
    try:
        for _ in range(20):
            rclpy.spin_once(node, timeout_sec=0.1)
        print(bridge.get_status().model_dump())
    finally:
        node.destroy_node()
        SharedRosContext.shutdown()

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("module", choices=["markers", "rgbd", "rtabmap_bridge", "perception", "slam", "gui"])
    parser.add_argument("--config", default="config/settings.yaml")
    args = parser.parse_args()
    if args.module == "markers":
        run_markers(args.config)
    elif args.module == "rgbd":
        run_rgbd(args.config)
    elif args.module == "rtabmap_bridge":
        run_rtabmap_bridge(args.config)
    elif args.module == "perception":
        from main_perception import main as perception_main
        perception_main()
    elif args.module == "slam":
        from main_slam import main as slam_main
        slam_main()
    elif args.module == "gui":
        from gui.app import main as gui_main
        gui_main()

if __name__ == "__main__":
    main()
