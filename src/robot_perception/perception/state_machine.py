from __future__ import annotations
import time
import traceback
from typing import Any, Dict, List, Optional
from common.enums import PerceptionState
from common.models import AppConfig, DetectedObject, PerceptionSnapshot
from common.utils import timed_call
from perception.active_vision_service import ActiveVisionService
from perception.camera_calibration_service import CameraCalibrationService
from perception.camera_service import CameraService
from perception.console import info, warn, error
from perception.kalman_tracker_service import SimpleKalmanTrackerService
from perception.light_target_service import LightTargetService
from perception.novelty_service import NoveltyService
from perception.path_deviation_service import PathDeviationService
from perception.point_cloud_service import PointCloudService
from perception.rgbd_service import RGBDService
from perception.ros2_node import PerceptionRosNode
from perception.visual_marker_service import VisualMarkerService
from perception.yolo_service import YoloService
from slam.rtabmap_ros_bridge import RTABMapRosBridge
from slam.tf_service import TfService
class RobotPerceptionStateMachine:
    def __init__(
        self,
        config: AppConfig,
        ros_node: PerceptionRosNode,
        selected_source: str='rgbd',
        camera_service: Optional[CameraService] = None,
    ) -> None:
        self.config=config; self.ros_node=ros_node; self.selected_source=selected_source; self.state=PerceptionState.IDLE; self.snapshot=PerceptionSnapshot(camera_id=config.camera_id); self.last_module_inputs: Dict[str, Dict[str, Any]] = {}
        self.camera_service = camera_service or CameraService(config.camera_id, config.camera_width, config.camera_height, config.output_dir)
        self.rgbd_service=RGBDService(config.depth_camera_id, config.camera_width, config.camera_height, config.output_dir)
        self.depth_enabled = selected_source == 'rgbd' and self.rgbd_service.is_available()
        if selected_source == 'rgbd' and not self.depth_enabled and config.allow_rgb_fallback: warn('Wybrano RGB-D, ale depth nie działa. Przechodzę do RGB-only.')
        elif selected_source == 'rgb': info('Wymuszono tryb RGB-only.')
        self.calibration_service=CameraCalibrationService(config.calibration_file)
        self.active_vision_service=ActiveVisionService()
        self.light_target_service=LightTargetService(config.light_spot_threshold, config.light_spot_min_area_px)
        self.visual_marker_service=VisualMarkerService(apriltag_family=config.april_tag_family, apriltag_size_m=config.april_tag_size_m, apriltag_enabled=config.apriltag_enabled, cctag_enabled=config.cctag_enabled, qr_enabled=config.qr_enabled)
        self.yolo_service=YoloService(config.yolo_model_path)
        self.novelty_service=NoveltyService(); self.kalman_service=SimpleKalmanTrackerService(); self.path_deviation_service=PathDeviationService(config.planned_path_y_tolerance); self.point_cloud_service=PointCloudService(config.output_dir)
        self.tf_service=TfService(ros_node); self.rtabmap_bridge=RTABMapRosBridge(node=ros_node, tf_service=self.tf_service, odom_info_topic=config.rtabmap_odom_topic, map_data_topic=config.rtabmap_mapdata_topic, info_topic=config.rtabmap_localization_topic)
        self.current_frame=None; self.current_depth=None; self.current_detections: List[DetectedObject]=[]; self.snapshot.calibration=self.calibration_service.calibration
    def _record_time(self, name: str, value_ms: float) -> None: self.snapshot.processing_times_ms[name]=value_ms
    def _remember_inputs(self, module_name: str, **kwargs: Any) -> None: self.last_module_inputs[module_name]=kwargs
    def get_debug_view(self) -> Dict[str, Any]:
        return {"current_state": self.state.name, "frame_id": self.snapshot.frame_id, "selected_source": self.selected_source, "depth_enabled": self.depth_enabled, "processing_times_ms": self.snapshot.processing_times_ms, "last_module_inputs": self.last_module_inputs, "slam_initialized": self.snapshot.slam.initialized, "map_point_count": self.snapshot.slam.map_point_count, "tracked_objects": len(self.snapshot.tracked_objects), "markers": len(self.snapshot.markers), "humans": len(self.snapshot.humans), "obstacles": len(self.snapshot.obstacles), "light_target_detected": self.snapshot.light_target is not None, "point_cloud_points": self.snapshot.point_cloud.point_count, "point_cloud_frame": self.snapshot.point_cloud.coordinate_frame}
    def transition_to(self, next_state: PerceptionState) -> None:
        info(f"Przejście stanu: {self.state.name} -> {next_state.name}"); self.state=next_state
    def run_once(self) -> bool:
        try:
            if self.state == PerceptionState.IDLE:
                self.snapshot.frame_id += 1; self.snapshot.timestamp_sec=time.time(); self.transition_to(PerceptionState.CAPTURE_RGBD_FRAME)
            elif self.state == PerceptionState.CAPTURE_RGBD_FRAME:
                self._remember_inputs('camera_service.capture', frame_id=self.snapshot.frame_id)
                (frame, image_path, image_meta), elapsed_rgb = timed_call(self.camera_service.capture, self.snapshot.frame_id)
                self.current_frame=frame; self.snapshot.image_path=image_path; self.snapshot.image_meta=image_meta; self._record_time('capture_rgb_frame', elapsed_rgb)
                if self.depth_enabled:
                    self._remember_inputs('rgbd_service.capture_depth', frame_id=self.snapshot.frame_id)
                    (depth, depth_path, depth_meta), elapsed_depth = timed_call(self.rgbd_service.capture_depth, self.snapshot.frame_id)
                    self.current_depth=depth; self.snapshot.depth_path=depth_path; self.snapshot.depth_meta=depth_meta; self._record_time('capture_depth_frame', elapsed_depth)
                else:
                    self.current_depth=None; self.snapshot.depth_path=None; self.snapshot.depth_meta=None
                self.transition_to(PerceptionState.INIT_RTABMAP_BRIDGE)
            elif self.state == PerceptionState.INIT_RTABMAP_BRIDGE:
                self._remember_inputs('rtabmap_bridge.get_status')
                self.snapshot.slam=self.rtabmap_bridge.get_status(); self._record_time('init_rtabmap_bridge', 0.0); self.transition_to(PerceptionState.ACTIVE_VISION)
            elif self.state == PerceptionState.ACTIVE_VISION:
                self._remember_inputs('active_vision_service.select_roi', mode=self.config.visual_attention_mode)
                av_result, elapsed = timed_call(self.active_vision_service.select_roi, self.current_frame, self.config.visual_attention_mode)
                self.snapshot.roi=av_result.roi; self._record_time('active_vision', elapsed); self.transition_to(PerceptionState.DETECT_LIGHT_TARGET)
            elif self.state == PerceptionState.DETECT_LIGHT_TARGET:
                self._remember_inputs('light_target_service.detect', roi=self.snapshot.roi.model_dump() if self.snapshot.roi else None, threshold=self.config.light_spot_threshold, min_area_px=self.config.light_spot_min_area_px)
                light_target, elapsed = timed_call(self.light_target_service.detect, self.current_frame, self.snapshot.roi)
                self.snapshot.light_target = light_target; self._record_time('detect_light_target', elapsed); self.transition_to(PerceptionState.DETECT_VISUAL_MARKERS)
            elif self.state == PerceptionState.DETECT_VISUAL_MARKERS:
                self._remember_inputs('visual_marker_service.detect', roi=self.snapshot.roi.model_dump() if self.snapshot.roi else None, apriltag_enabled=self.config.apriltag_enabled, cctag_enabled=self.config.cctag_enabled, qr_enabled=self.config.qr_enabled)
                markers, elapsed = timed_call(self.visual_marker_service.detect, self.current_frame, self.snapshot.calibration, self.snapshot.roi)
                self.snapshot.markers=markers; self._record_time('detect_visual_markers', elapsed); self.transition_to(PerceptionState.DETECT_HUMAN)
            elif self.state == PerceptionState.DETECT_HUMAN:
                self._remember_inputs('yolo_service.detect_humans')
                humans, elapsed = timed_call(self.yolo_service.detect_humans, self.current_frame); self.snapshot.humans=humans; self._record_time('detect_human', elapsed); self.transition_to(PerceptionState.DETECT_OBSTACLE)
            elif self.state == PerceptionState.DETECT_OBSTACLE:
                self._remember_inputs('yolo_service.detect_obstacles')
                obstacles, elapsed = timed_call(self.yolo_service.detect_obstacles, self.current_frame); self.snapshot.obstacles=obstacles; self.current_detections=obstacles; self._record_time('detect_obstacle', elapsed); self.transition_to(PerceptionState.DETECT_NEW_OBJECTS)
            elif self.state == PerceptionState.DETECT_NEW_OBJECTS:
                self._remember_inputs('novelty_service.detect_new_objects', detections=len(self.current_detections), tracked=len(self.snapshot.tracked_objects))
                new_objects, elapsed = timed_call(self.novelty_service.detect_new_objects, self.current_detections, self.snapshot.tracked_objects); self.snapshot.new_objects=new_objects; self._record_time('detect_new_objects', elapsed); self.transition_to(PerceptionState.TRACK_OBJECTS_KALMAN)
            elif self.state == PerceptionState.TRACK_OBJECTS_KALMAN:
                self._remember_inputs('kalman_service.update_tracks', detections=len(self.current_detections), previous_tracks=len(self.snapshot.tracked_objects))
                tracked, elapsed = timed_call(self.kalman_service.update_tracks, self.current_detections, self.snapshot.tracked_objects); self.snapshot.tracked_objects=tracked; self._record_time('track_objects_kalman', elapsed); self.transition_to(PerceptionState.UPDATE_SLAM_FROM_RTABMAP)
            elif self.state == PerceptionState.UPDATE_SLAM_FROM_RTABMAP:
                self._remember_inputs('rtabmap_bridge.get_status')
                slam_status, elapsed = timed_call(self.rtabmap_bridge.get_status); self.snapshot.slam=slam_status; self._record_time('update_slam_from_rtabmap', elapsed); self.transition_to(PerceptionState.CHECK_PATH_DEVIATION)
            elif self.state == PerceptionState.CHECK_PATH_DEVIATION:
                self._remember_inputs('path_deviation_service.check', pose=self.snapshot.slam.pose.model_dump() if self.snapshot.slam.pose else None)
                (flag, value), elapsed = timed_call(self.path_deviation_service.check, self.snapshot.slam.pose); self.snapshot.path_deviation_detected=flag; self.snapshot.path_deviation_value=value; self._record_time('check_path_deviation', elapsed); self.transition_to(PerceptionState.BUILD_POINT_CLOUD)
            elif self.state == PerceptionState.BUILD_POINT_CLOUD:
                if self.current_depth is not None:
                    self._remember_inputs('point_cloud_service.build_from_rgbd', depth_scale=self.snapshot.depth_meta.depth_scale if self.snapshot.depth_meta else 1000.0)
                    point_cloud, elapsed = timed_call(self.point_cloud_service.build_from_rgbd, self.current_frame, self.current_depth, self.snapshot.calibration, self.snapshot.depth_meta.depth_scale if self.snapshot.depth_meta else 1000.0)
                else:
                    self._remember_inputs('point_cloud_service.build_sparse_from_rgb_only')
                    point_cloud, elapsed = timed_call(self.point_cloud_service.build_sparse_from_rgb_only, self.current_frame, self.snapshot.calibration)
                if self.point_cloud_service.validate_transform(self.snapshot.slam.pose, self.config.transform_validation_translation_limit_m, self.config.transform_validation_rotation_limit_rad):
                    point_cloud = self.point_cloud_service.transform_to_map(point_cloud, self.snapshot.slam.pose)
                self.snapshot.point_cloud=point_cloud; self._record_time('build_point_cloud', elapsed); self.transition_to(PerceptionState.SAVE_POINT_CLOUD_IF_READY)
            elif self.state == PerceptionState.SAVE_POINT_CLOUD_IF_READY:
                if self.snapshot.point_cloud.point_count >= self.config.point_cloud_save_threshold:
                    self._remember_inputs('point_cloud_service.save_ply', frame_id=self.snapshot.frame_id)
                    save_path, elapsed = timed_call(self.point_cloud_service.save_ply, self.snapshot.point_cloud, self.snapshot.frame_id); self.snapshot.point_cloud_save_path=save_path; self._record_time('save_point_cloud', elapsed)
                self.transition_to(PerceptionState.PRINT_STATE)
            elif self.state == PerceptionState.PRINT_STATE:
                self.print_snapshot(); self.transition_to(PerceptionState.PUBLISH_ROS2_STATE)
            elif self.state == PerceptionState.PUBLISH_ROS2_STATE:
                self.ros_node.publish_snapshot(self.snapshot); self.ros_node.publish_point_cloud(self.snapshot); self.transition_to(PerceptionState.IDLE)
            elif self.state == PerceptionState.ERROR:
                self.print_snapshot()
            else:
                raise ValueError(f'Nieobsługiwany stan: {self.state}')
            return True
        except StopIteration as exc:
            info(f"Zatrzymanie pętli percepcji: {exc}")
            self.snapshot.system_ok = True
            self.snapshot.error_message = None
            self.transition_to(PerceptionState.IDLE)
            return False
        except Exception as exc:
            self.snapshot.system_ok=False; self.snapshot.error_message=f"{exc}\n{traceback.format_exc()}"; error(f"Błąd krytyczny: {exc}"); self.transition_to(PerceptionState.ERROR)
            return False
    def print_snapshot(self) -> None:
        print('\n=== AKTUALNY STAN PERCEPCJI ROBOTA ==='); print(self.snapshot.model_dump_json(indent=2)); print('=== KONIEC STANU PERCEPCJI ===\n')
    def shutdown(self) -> None:
        self.camera_service.close(); self.rgbd_service.close()
