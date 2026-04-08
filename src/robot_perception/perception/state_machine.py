from __future__ import annotations
import time
import traceback
from typing import List
from common.enums import PerceptionState
from common.models import AppConfig, DetectedObject, PerceptionSnapshot
from common.utils import timed_call
from perception.active_vision_service import ActiveVisionService
from perception.april_tag_service import AprilTagService
from perception.camera_calibration_service import CameraCalibrationService
from perception.camera_service import CameraService
from perception.kalman_tracker_service import SimpleKalmanTrackerService
from perception.novelty_service import NoveltyService
from perception.path_deviation_service import PathDeviationService
from perception.point_cloud_service import PointCloudService
from perception.rgbd_service import RGBDService
from perception.ros2_node import PerceptionRosNode
from perception.rtabmap_ros_bridge import RTABMapRosBridge
from perception.yolo_service import YoloService


class RobotPerceptionStateMachine:
    """Produkcyjna maszyna stanów percepcji robota."""

    def __init__(self, config: AppConfig, ros_node: PerceptionRosNode) -> None:
        self.config = config
        self.ros_node = ros_node
        self.state = PerceptionState.IDLE
        self.snapshot = PerceptionSnapshot(camera_id=config.camera_id)

        self.camera_service = CameraService(
            camera_id=config.camera_id,
            width=config.camera_width,
            height=config.camera_height,
            output_dir=config.output_dir,
        )
        self.rgbd_service = RGBDService(
            depth_camera_id=config.depth_camera_id,
            width=config.camera_width,
            height=config.camera_height,
            output_dir=config.output_dir,
        )
        self.calibration_service = CameraCalibrationService(config.calibration_file)
        self.active_vision_service = ActiveVisionService()
        self.april_tag_service = AprilTagService(config.april_tag_family, config.april_tag_size_m)
        self.yolo_service = YoloService(config.yolo_model_path)
        self.novelty_service = NoveltyService()
        self.kalman_service = SimpleKalmanTrackerService()
        self.path_deviation_service = PathDeviationService(config.planned_path_y_tolerance)
        self.point_cloud_service = PointCloudService(config.output_dir)
        self.rtabmap_bridge = RTABMapRosBridge(
            node=ros_node,
            odom_info_topic=config.rtabmap_odom_topic,
            map_data_topic=config.rtabmap_mapdata_topic,
            info_topic=config.rtabmap_localization_topic,
        )

        self.current_frame = None
        self.current_depth = None
        self.current_detections: List[DetectedObject] = []
        self.snapshot.calibration = self.calibration_service.calibration

    def _record_time(self, name: str, value_ms: float) -> None:
        self.snapshot.processing_times_ms[name] = value_ms

    def transition_to(self, next_state: PerceptionState) -> None:
        self.state = next_state

    def run_once(self) -> None:
        """Wykonuje jeden pełny cykl automatu stanów."""
        try:
            if self.state == PerceptionState.IDLE:
                self.snapshot.frame_id += 1
                self.snapshot.timestamp_sec = time.time()
                self.transition_to(PerceptionState.CAPTURE_RGBD_FRAME)

            elif self.state == PerceptionState.CAPTURE_RGBD_FRAME:
                (frame, image_path, image_meta), elapsed_rgb = timed_call(
                    self.camera_service.capture,
                    self.snapshot.frame_id,
                )
                (depth, depth_path, depth_meta), elapsed_depth = timed_call(
                    self.rgbd_service.capture_depth,
                    self.snapshot.frame_id,
                )

                self.current_frame = frame
                self.current_depth = depth
                self.snapshot.image_path = image_path
                self.snapshot.depth_path = depth_path
                self.snapshot.image_meta = image_meta
                self.snapshot.depth_meta = depth_meta
                self._record_time("capture_rgb_frame", elapsed_rgb)
                self._record_time("capture_depth_frame", elapsed_depth)
                self.transition_to(PerceptionState.INIT_RTABMAP_BRIDGE)

            elif self.state == PerceptionState.INIT_RTABMAP_BRIDGE:
                self.snapshot.slam = self.rtabmap_bridge.get_status()
                self._record_time("init_rtabmap_bridge", 0.0)
                self.transition_to(PerceptionState.ACTIVE_VISION)

            elif self.state == PerceptionState.ACTIVE_VISION:
                roi, elapsed = timed_call(self.active_vision_service.select_roi, self.current_frame)
                self.snapshot.roi = roi
                self._record_time("active_vision", elapsed)
                self.transition_to(PerceptionState.DETECT_VISUAL_MARKERS)

            elif self.state == PerceptionState.DETECT_VISUAL_MARKERS:
                markers, elapsed = timed_call(
                    self.april_tag_service.detect,
                    self.current_frame,
                    self.snapshot.calibration,
                    self.snapshot.roi,
                )
                self.snapshot.markers = markers
                self._record_time("detect_visual_markers", elapsed)
                self.transition_to(PerceptionState.DETECT_HUMAN)

            elif self.state == PerceptionState.DETECT_HUMAN:
                humans, elapsed = timed_call(self.yolo_service.detect_humans, self.current_frame)
                self.snapshot.humans = humans
                self._record_time("detect_human", elapsed)
                self.transition_to(PerceptionState.DETECT_OBSTACLE)

            elif self.state == PerceptionState.DETECT_OBSTACLE:
                obstacles, elapsed = timed_call(self.yolo_service.detect_obstacles, self.current_frame)
                self.snapshot.obstacles = obstacles
                self.current_detections = obstacles
                self._record_time("detect_obstacle", elapsed)
                self.transition_to(PerceptionState.DETECT_NEW_OBJECTS)

            elif self.state == PerceptionState.DETECT_NEW_OBJECTS:
                new_objects, elapsed = timed_call(
                    self.novelty_service.detect_new_objects,
                    self.current_detections,
                    self.snapshot.tracked_objects,
                )
                self.snapshot.new_objects = new_objects
                self._record_time("detect_new_objects", elapsed)
                self.transition_to(PerceptionState.TRACK_OBJECTS_KALMAN)

            elif self.state == PerceptionState.TRACK_OBJECTS_KALMAN:
                tracked, elapsed = timed_call(
                    self.kalman_service.update_tracks,
                    self.current_detections,
                    self.snapshot.tracked_objects,
                )
                self.snapshot.tracked_objects = tracked
                self._record_time("track_objects_kalman", elapsed)
                self.transition_to(PerceptionState.UPDATE_SLAM_FROM_RTABMAP)

            elif self.state == PerceptionState.UPDATE_SLAM_FROM_RTABMAP:
                slam_status, elapsed = timed_call(self.rtabmap_bridge.get_status)
                self.snapshot.slam = slam_status
                self._record_time("update_slam_from_rtabmap", elapsed)
                self.transition_to(PerceptionState.CHECK_PATH_DEVIATION)

            elif self.state == PerceptionState.CHECK_PATH_DEVIATION:
                (flag, value), elapsed = timed_call(
                    self.path_deviation_service.check,
                    self.snapshot.slam.pose,
                )
                self.snapshot.path_deviation_detected = flag
                self.snapshot.path_deviation_value = value
                self._record_time("check_path_deviation", elapsed)
                self.transition_to(PerceptionState.BUILD_POINT_CLOUD)

            elif self.state == PerceptionState.BUILD_POINT_CLOUD:
                point_cloud, elapsed = timed_call(
                    self.point_cloud_service.build_from_rgbd,
                    self.current_frame,
                    self.current_depth,
                    self.snapshot.calibration,
                    self.snapshot.depth_meta.depth_scale if self.snapshot.depth_meta else 1000.0,
                )
                self.snapshot.point_cloud = point_cloud
                self._record_time("build_point_cloud", elapsed)
                self.transition_to(PerceptionState.SAVE_POINT_CLOUD_IF_READY)

            elif self.state == PerceptionState.SAVE_POINT_CLOUD_IF_READY:
                if self.snapshot.point_cloud.point_count >= self.config.point_cloud_save_threshold:
                    save_path, elapsed = timed_call(
                        self.point_cloud_service.save_ply,
                        self.snapshot.point_cloud,
                        self.snapshot.frame_id,
                    )
                    self.snapshot.point_cloud_save_path = save_path
                    self._record_time("save_point_cloud", elapsed)
                self.transition_to(PerceptionState.PRINT_STATE)

            elif self.state == PerceptionState.PRINT_STATE:
                self.print_snapshot()
                self.transition_to(PerceptionState.PUBLISH_ROS2_STATE)

            elif self.state == PerceptionState.PUBLISH_ROS2_STATE:
                self.ros_node.publish_snapshot(self.snapshot)
                self.ros_node.publish_point_cloud(self.snapshot)
                self.transition_to(PerceptionState.IDLE)

            elif self.state == PerceptionState.ERROR:
                self.print_snapshot()

            else:
                raise ValueError(f"Nieobsługiwany stan: {self.state}")

        except Exception as exc:
            self.snapshot.system_ok = False
            self.snapshot.error_message = f"{exc}{traceback.format_exc()}"
            self.transition_to(PerceptionState.ERROR)

    def print_snapshot(self) -> None:
        """Wypisuje snapshot percepcji do terminala."""
        print("=== AKTUALNY STAN PERCEPCJI ===")
        print(self.snapshot.model_dump_json(indent=2))

    def shutdown(self) -> None:
        """Porządkuje zasoby przy kończeniu pracy."""
        self.camera_service.close()
        self.rgbd_service.close()




""" 
from __future__ import annotations
import traceback
import time
from typing import List
from common.enums import PerceptionState
from common.models import AppConfig, DetectedObject, PerceptionSnapshot, TrackedObject
from common.utils import timed_call
from perception.active_vision_service import ActiveVisionService
from perception.april_tag_service import AprilTagService
from perception.camera_service import CameraService
from perception.kalman_tracker_service import SimpleKalmanTrackerService
from perception.novelty_service import NoveltyService
from perception.path_deviation_service import PathDeviationService
from perception.point_cloud_service import PointCloudService
from perception.ros2_node import PerceptionRosNode
from perception.rtabmap_service import RTABMapService
from perception.yolo_service import YoloService


class RobotPerceptionStateMachine:
    ""Produkcyjna maszyna stanów dla percepcji robota.""

    def __init__(self, config: AppConfig, ros_node: PerceptionRosNode) -> None:
        self.config = config
        self.ros_node = ros_node
        self.state = PerceptionState.IDLE
        self.snapshot = PerceptionSnapshot(camera_id=config.camera_id)

        self.camera_service = CameraService(
            camera_id=config.camera_id,
            width=config.camera_width,
            height=config.camera_height,
            output_dir=config.output_dir,
        )
        self.active_vision_service = ActiveVisionService()
        self.april_tag_service = AprilTagService(config.april_tag_family)
        self.yolo_service = YoloService(config.yolo_model_path)
        self.novelty_service = NoveltyService()
        self.kalman_service = SimpleKalmanTrackerService()
        self.path_deviation_service = PathDeviationService(config.planned_path_y_tolerance)
        self.rtabmap_service = RTABMapService(
            database_path=config.rtabmap_database_path,
            launch_package=config.rtabmap_launch_package,
            launch_file=config.rtabmap_launch_file,
        )
        self.point_cloud_service = PointCloudService(config.output_dir)

        self.current_frame = None
        self.current_detections: List[DetectedObject] = []

    def _record_time(self, name: str, value_ms: float) -> None:
        self.snapshot.processing_times_ms[name] = value_ms

    def transition_to(self, next_state: PerceptionState) -> None:
        self.state = next_state

    def run_once(self) -> None:
        ""Wykonuje jeden pełny krok automatu stanów.""
        try:
            if self.state == PerceptionState.IDLE:
                self.snapshot.frame_id += 1
                self.snapshot.timestamp_sec = time.time()
                self.transition_to(PerceptionState.CAPTURE_CAMERA_FRAME)

            elif self.state == PerceptionState.CAPTURE_CAMERA_FRAME:
                (frame, image_path, meta), elapsed = timed_call(
                    self.camera_service.capture,
                    self.snapshot.frame_id,
                )
                self.current_frame = frame
                self.snapshot.image_path = image_path
                self.snapshot.image_meta = meta
                self._record_time("capture_camera_frame", elapsed)
                self.transition_to(PerceptionState.INIT_VISUAL_SLAM)

            elif self.state == PerceptionState.INIT_VISUAL_SLAM:
                if not self.snapshot.slam.initialized:
                    slam_status, elapsed = timed_call(self.rtabmap_service.ensure_started)
                    self.snapshot.slam = slam_status
                    self._record_time("init_visual_slam", elapsed)
                self.transition_to(PerceptionState.ACTIVE_VISION)

            elif self.state == PerceptionState.ACTIVE_VISION:
                roi, elapsed = timed_call(self.active_vision_service.select_roi, self.current_frame)
                self.snapshot.roi = roi
                self._record_time("active_vision", elapsed)
                self.transition_to(PerceptionState.DETECT_VISUAL_MARKERS)

            elif self.state == PerceptionState.DETECT_VISUAL_MARKERS:
                markers, elapsed = timed_call(self.april_tag_service.detect, self.current_frame, self.snapshot.roi)
                self.snapshot.markers = markers
                self._record_time("detect_visual_markers", elapsed)
                self.transition_to(PerceptionState.DETECT_HUMAN)

            elif self.state == PerceptionState.DETECT_HUMAN:
                humans, elapsed = timed_call(self.yolo_service.detect_humans, self.current_frame)
                self.snapshot.humans = humans
                self._record_time("detect_human", elapsed)
                self.transition_to(PerceptionState.DETECT_OBSTACLE)

            elif self.state == PerceptionState.DETECT_OBSTACLE:
                obstacles, elapsed = timed_call(self.yolo_service.detect_obstacles, self.current_frame)
                self.snapshot.obstacles = obstacles
                self.current_detections = obstacles
                self._record_time("detect_obstacle", elapsed)
                self.transition_to(PerceptionState.DETECT_NEW_OBJECTS)

            elif self.state == PerceptionState.DETECT_NEW_OBJECTS:
                new_objects, elapsed = timed_call(
                    self.novelty_service.detect_new_objects,
                    self.current_detections,
                    self.snapshot.tracked_objects,
                )
                self.snapshot.new_objects = new_objects
                self._record_time("detect_new_objects", elapsed)
                self.transition_to(PerceptionState.TRACK_OBJECTS_KALMAN)

            elif self.state == PerceptionState.TRACK_OBJECTS_KALMAN:
                tracked, elapsed = timed_call(
                    self.kalman_service.update_tracks,
                    self.current_detections,
                    self.snapshot.tracked_objects,
                )
                self.snapshot.tracked_objects = tracked
                self._record_time("track_objects_kalman", elapsed)
                self.transition_to(PerceptionState.CHECK_PATH_DEVIATION)

            elif self.state == PerceptionState.CHECK_PATH_DEVIATION:
                (flag, value), elapsed = timed_call(
                    self.path_deviation_service.check,
                    self.snapshot.slam.pose,
                )
                self.snapshot.path_deviation_detected = flag
                self.snapshot.path_deviation_value = value
                self._record_time("check_path_deviation", elapsed)
                self.transition_to(PerceptionState.UPDATE_VISUAL_SLAM)

            elif self.state == PerceptionState.UPDATE_VISUAL_SLAM:
                slam_status, elapsed = timed_call(self.rtabmap_service.update)
                self.snapshot.slam = slam_status
                self._record_time("update_visual_slam", elapsed)
                self.transition_to(PerceptionState.BUILD_POINT_CLOUD)

            elif self.state == PerceptionState.BUILD_POINT_CLOUD:
                point_cloud, elapsed = timed_call(
                    self.point_cloud_service.build_from_slam_status,
                    self.snapshot.slam,
                )
                self.snapshot.point_cloud = point_cloud
                self._record_time("build_point_cloud", elapsed)
                self.transition_to(PerceptionState.SAVE_POINT_CLOUD_IF_READY)

            elif self.state == PerceptionState.SAVE_POINT_CLOUD_IF_READY:
                if self.snapshot.point_cloud.point_count >= self.config.point_cloud_save_threshold:
                    save_path, elapsed = timed_call(
                        self.point_cloud_service.save_ply,
                        self.snapshot.point_cloud,
                        self.snapshot.frame_id,
                    )
                    self.snapshot.point_cloud_save_path = save_path
                    self._record_time("save_point_cloud", elapsed)
                self.transition_to(PerceptionState.PRINT_STATE)

            elif self.state == PerceptionState.PRINT_STATE:
                self.print_snapshot()
                self.transition_to(PerceptionState.PUBLISH_ROS2_STATE)

            elif self.state == PerceptionState.PUBLISH_ROS2_STATE:
                self.ros_node.publish_snapshot(self.snapshot)
                self.ros_node.publish_point_cloud(self.snapshot)
                self.transition_to(PerceptionState.IDLE)

            elif self.state == PerceptionState.ERROR:
                self.print_snapshot()

            else:
                raise ValueError(f"Nieobsługiwany stan: {self.state}")

        except Exception as exc:
            self.snapshot.system_ok = False
            self.snapshot.error_message = f"{exc}\n{traceback.format_exc()}"
            self.transition_to(PerceptionState.ERROR)

    def print_snapshot(self) -> None:
        ""Wypisuje aktualny snapshot percepcji do terminala.""
        
        print("\n=== AKTUALNY STAN PERCEPCJI ===")
        print(self.snapshot.model_dump_json(indent=2))

    def shutdown(self) -> None:
        ""Porządkuje zasoby przy zamknięciu aplikacji.""
        self.camera_service.close()
        self.rtabmap_service.shutdown()

 """