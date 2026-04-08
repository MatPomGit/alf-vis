from enum import Enum, auto

# Enum stanów głównej maszyny percepcji

class PerceptionState(Enum):
    IDLE = auto()
    CAPTURE_CAMERA_FRAME = auto()
    INIT_VISUAL_SLAM = auto()
    ACTIVE_VISION = auto()
    DETECT_VISUAL_MARKERS = auto()
    DETECT_HUMAN = auto()
    DETECT_OBSTACLE = auto()
    DETECT_NEW_OBJECTS = auto()
    TRACK_OBJECTS_KALMAN = auto()
    CHECK_PATH_DEVIATION = auto()
    UPDATE_VISUAL_SLAM = auto()
    BUILD_POINT_CLOUD = auto()
    SAVE_POINT_CLOUD_IF_READY = auto()
    PRINT_STATE = auto()
    PUBLISH_ROS2_STATE = auto()
    ERROR = auto()