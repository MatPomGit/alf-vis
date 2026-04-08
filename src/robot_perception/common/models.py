from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field, ConfigDict


class ImageMeta(BaseModel):
    """Metadane pojedynczej ramki obrazu."""

    width: int
    height: int
    encoding: str = "bgr8"
    fps: Optional[float] = None
    camera_id: int = 0


class ROI(BaseModel):
    """Region zainteresowania w obrazie."""

    x: int
    y: int
    width: int
    height: int


class Pose3D(BaseModel):
    """Prosta reprezentacja pozy 3D."""

    x: float
    y: float
    z: float
    roll: float = 0.0
    pitch: float = 0.0
    yaw: float = 0.0


class VisualMarker(BaseModel):
    """Opis wykrytego markera AprilTag."""

    tag_id: int
    family: str
    center: Tuple[float, float]
    corners: List[Tuple[float, float]]
    pose: Optional[Pose3D] = None
    decision_margin: Optional[float] = None
    hamming: Optional[int] = None


class DetectedObject(BaseModel):
    """Opis obiektu wykrytego przez detektor YOLO."""

    label: str
    class_id: int
    confidence: float
    bbox_xyxy: Tuple[float, float, float, float]
    centroid_xy: Tuple[float, float]
    is_new: bool = False


class TrackedObject(BaseModel):
    """Opis obiektu śledzonego filtrem Kalmana."""

    object_id: int
    label: str
    class_id: int
    confidence: float
    bbox_xyxy: Tuple[float, float, float, float]
    centroid_xy: Tuple[float, float]
    velocity_xy: Tuple[float, float] = (0.0, 0.0)
    kalman_state: List[float] = Field(default_factory=list)


class PointCloudData(BaseModel):
    """Reprezentacja chmury punktów używana przez warstwę aplikacyjną."""

    coordinate_frame: str = "map"
    points: List[Tuple[float, float, float]] = Field(default_factory=list)
    colors: List[Tuple[float, float, float]] = Field(default_factory=list)

    @property
    def point_count(self) -> int:
        return len(self.points)


class SlamStatus(BaseModel):
    """Stan pracy systemu SLAM."""

    initialized: bool = False
    status: str = "NOT_INITIALIZED"
    pose: Optional[Pose3D] = None
    map_point_count: int = 0
    database_path: Optional[str] = None


class PerceptionSnapshot(BaseModel):
    """Pełny bieżący stan percepcji robota."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    frame_id: int = 0
    timestamp_sec: float = 0.0
    camera_id: int = 0
    image_path: Optional[str] = None
    image_meta: Optional[ImageMeta] = None

    roi: Optional[ROI] = None
    markers: List[VisualMarker] = Field(default_factory=list)
    humans: List[DetectedObject] = Field(default_factory=list)
    obstacles: List[DetectedObject] = Field(default_factory=list)
    new_objects: List[DetectedObject] = Field(default_factory=list)
    tracked_objects: List[TrackedObject] = Field(default_factory=list)

    path_deviation_detected: bool = False
    path_deviation_value: float = 0.0

    slam: SlamStatus = Field(default_factory=SlamStatus)
    point_cloud: PointCloudData = Field(default_factory=PointCloudData)
    point_cloud_save_path: Optional[str] = None

    processing_times_ms: Dict[str, float] = Field(default_factory=dict)
    system_ok: bool = True
    error_message: Optional[str] = None


class AppConfig(BaseModel):
    """Konfiguracja całej aplikacji percepcji."""

    camera_id: int = 0
    camera_width: int = 640
    camera_height: int = 480
    output_dir: str = "output"
    point_cloud_save_threshold: int = 500
    perception_state_topic: str = "/perception/state"
    point_cloud_topic: str = "/perception/point_cloud"
    yolo_model_path: str = "yolov8s.pt"
    april_tag_family: str = "tag36h11"
    rtabmap_database_path: str = "output/rtabmap.db"
    rtabmap_launch_package: str = "rtabmap_launch"
    rtabmap_launch_file: str = "rtabmap.launch.py"
    planned_path_y_tolerance: float = 0.5