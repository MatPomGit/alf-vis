from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ImageMeta(BaseModel):
    width: int
    height: int
    encoding: str = "bgr8"
    fps: float | None = None
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
    camera_matrix: list[list[float]]
    distortion_coefficients: list[float]
    calibration_rms: float | None = None


class VisualMarker(BaseModel):
    tag_id: int
    family: str
    center: tuple[float, float]
    corners: list[tuple[float, float]]
    decision_margin: float | None = None
    hamming: int | None = None
    pose: Pose3D | None = None
    translation_vector: list[float] | None = None
    rotation_vector: list[float] | None = None
    reprojection_error_px: float | None = None
    pose_quality: str | None = None


class LightTarget(BaseModel):
    center_xy: tuple[float, float]
    axes_xy: tuple[float, float]
    angle_deg: float
    area_px: float
    contour_points: int


class DetectedObject(BaseModel):
    label: str
    class_id: int
    confidence: float
    bbox_xyxy: tuple[float, float, float, float]
    centroid_xy: tuple[float, float]
    is_new: bool = False


class TrackedObject(BaseModel):
    object_id: int
    label: str
    class_id: int
    confidence: float
    bbox_xyxy: tuple[float, float, float, float]
    centroid_xy: tuple[float, float]
    velocity_xy: tuple[float, float] = (0.0, 0.0)
    kalman_state: list[float] = Field(default_factory=list)


class PointCloudData(BaseModel):
    coordinate_frame: str = "map"
    points: list[tuple[float, float, float]] = Field(default_factory=list)
    colors: list[tuple[float, float, float]] = Field(default_factory=list)

    @property
    def point_count(self) -> int:
        return len(self.points)


class SlamStatus(BaseModel):
    initialized: bool = False
    status: str = "NOT_INITIALIZED"
    pose: Pose3D | None = None
    map_point_count: int = 0
    odom_lost: bool = False
    inliers: int = 0
    matches: int = 0
    localization_id: int = 0
    loop_closure_id: int = 0
    map_to_odom_available: bool = False
    camera_to_map_available: bool = False
    database_path: str | None = None


class PerceptionSnapshot(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    frame_id: int = 0
    timestamp_sec: float = 0.0
    camera_id: int = 0
    image_path: str | None = None
    depth_path: str | None = None
    image_meta: ImageMeta | None = None
    depth_meta: DepthMeta | None = None
    calibration: CameraCalibration | None = None
    roi: ROI | None = None
    light_target: LightTarget | None = None
    markers: list[VisualMarker] = Field(default_factory=list)
    humans: list[DetectedObject] = Field(default_factory=list)
    obstacles: list[DetectedObject] = Field(default_factory=list)
    new_objects: list[DetectedObject] = Field(default_factory=list)
    tracked_objects: list[TrackedObject] = Field(default_factory=list)
    slam: SlamStatus = Field(default_factory=SlamStatus)
    path_deviation_detected: bool = False
    path_deviation_value: float = 0.0
    point_cloud: PointCloudData = Field(default_factory=PointCloudData)
    point_cloud_save_path: str | None = None
    processing_times_ms: dict[str, float] = Field(default_factory=dict)
    system_ok: bool = True
    error_message: str | None = None


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
    light_spot_hsv_lower: list[int] | None = None
    light_spot_hsv_upper: list[int] | None = None
