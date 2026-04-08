from __future__ import annotations
from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel, ConfigDict, Field

class ImageMeta(BaseModel):
    width: int
    height: int
    encoding: str = "bgr8"
    fps: Optional[float] = None
    camera_id: int = 0

class DepthMeta(BaseModel):
    width: int
    height: int
    encoding: str = "16UC1"
    depth_scale: float = 1000.0
    depth_unit_m: float = 0.001

class ROI(BaseModel):
    x: int
    y: int
    width: int
    height: int

class Pose3D(BaseModel):
    x: float
    y: float
    z: float
    roll: float = 0.0
    pitch: float = 0.0
    yaw: float = 0.0

class CameraCalibration(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    image_width: int
    image_height: int
    camera_matrix: List[List[float]]
    distortion_coefficients: List[float]
    calibration_rms: Optional[float] = None

class VisualMarker(BaseModel):
    tag_id: int
    family: str
    center: Tuple[float, float]
    corners: List[Tuple[float, float]]
    decision_margin: Optional[float] = None
    hamming: Optional[int] = None
    pose: Optional[Pose3D] = None
    translation_vector: Optional[List[float]] = None
    rotation_vector: Optional[List[float]] = None
    reprojection_error_px: Optional[float] = None
    pose_quality: Optional[str] = None

class LightTarget(BaseModel):
    center_xy: Tuple[float, float]
    axes_xy: Tuple[float, float]
    angle_deg: float
    area_px: float
    contour_points: int

class DetectedObject(BaseModel):
    label: str
    class_id: int
    confidence: float
    bbox_xyxy: Tuple[float, float, float, float]
    centroid_xy: Tuple[float, float]
    is_new: bool = False

class TrackedObject(BaseModel):
    object_id: int
    label: str
    class_id: int
    confidence: float
    bbox_xyxy: Tuple[float, float, float, float]
    centroid_xy: Tuple[float, float]
    velocity_xy: Tuple[float, float] = (0.0, 0.0)
    kalman_state: List[float] = Field(default_factory=list)

class PointCloudData(BaseModel):
    coordinate_frame: str = "map"
    points: List[Tuple[float, float, float]] = Field(default_factory=list)
    colors: List[Tuple[float, float, float]] = Field(default_factory=list)
    @property
    def point_count(self) -> int:
        return len(self.points)

class SlamStatus(BaseModel):
    initialized: bool = False
    status: str = "NOT_INITIALIZED"
    pose: Optional[Pose3D] = None
    map_point_count: int = 0
    odom_lost: bool = False
    inliers: int = 0
    matches: int = 0
    localization_id: int = 0
    loop_closure_id: int = 0
    map_to_odom_available: bool = False
    camera_to_map_available: bool = False
    database_path: Optional[str] = None

class PerceptionSnapshot(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    frame_id: int = 0
    timestamp_sec: float = 0.0
    camera_id: int = 0
    image_path: Optional[str] = None
    depth_path: Optional[str] = None
    image_meta: Optional[ImageMeta] = None
    depth_meta: Optional[DepthMeta] = None
    calibration: Optional[CameraCalibration] = None
    roi: Optional[ROI] = None
    light_target: Optional[LightTarget] = None
    markers: List[VisualMarker] = Field(default_factory=list)
    humans: List[DetectedObject] = Field(default_factory=list)
    obstacles: List[DetectedObject] = Field(default_factory=list)
    new_objects: List[DetectedObject] = Field(default_factory=list)
    tracked_objects: List[TrackedObject] = Field(default_factory=list)
    slam: SlamStatus = Field(default_factory=SlamStatus)
    path_deviation_detected: bool = False
    path_deviation_value: float = 0.0
    point_cloud: PointCloudData = Field(default_factory=PointCloudData)
    point_cloud_save_path: Optional[str] = None
    processing_times_ms: Dict[str, float] = Field(default_factory=dict)
    system_ok: bool = True
    error_message: Optional[str] = None

class AppConfig(BaseModel):
    camera_id: int = 0
    depth_camera_id: int = 0
    camera_width: int = 640
    camera_height: int = 480
    output_dir: str = "output"
    point_cloud_save_threshold: int = 500
    perception_state_topic: str = "/perception/state"
    point_cloud_topic: str = "/perception/point_cloud"
    yolo_model_path: str = "yolov8s.pt"
    visual_attention_mode: int = 1
    apriltag_enabled: bool = True
    cctag_enabled: bool = True
    qr_enabled: bool = True
    april_tag_family: str = "tag36h11"
    april_tag_size_m: float = 0.162
    calibration_file: str = "config/camera_calibration.yaml"
    rtabmap_odom_topic: str = "/rtabmap/odom_info"
    rtabmap_mapdata_topic: str = "/rtabmap/mapData"
    rtabmap_localization_topic: str = "/rtabmap/info"
    planned_path_y_tolerance: float = 0.5
    default_camera_source: str = "rgbd"
    allow_rgb_fallback: bool = True
    transform_validation_translation_limit_m: float = 50.0
    transform_validation_rotation_limit_rad: float = 3.2
    apriltag_reprojection_good_px: float = 1.5
    apriltag_reprojection_warn_px: float = 4.0
    light_spot_threshold: int = 230
    light_spot_min_area_px: float = 40.0
