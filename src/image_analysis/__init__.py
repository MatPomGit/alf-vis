"""Image analysis package for the Unitree G1 EDU robot.

Public API for the image_analysis module.  The package covers the full
perception pipeline: camera capture, calibration, marker detection, YOLO
object detection, 3-D pose estimation, SLAM, plane detection, RGB-D
visualisation, and acquisition quality assessment.
"""

from image_analysis.acquisition_metrics import (
    AcquisitionMonitor,
    AcquisitionReport,
    FrameMetrics,
    assess_frame,
)
from image_analysis.calibration import (
    CalibrationResult,
    calibrate_camera,
    load_calibration,
    save_calibration,
    undistort_image,
)
from image_analysis.camera import CameraConfig, RgbdFrame, UnitreeCamera
from image_analysis.classification import classify_image
from image_analysis.detection import Detection, detect_objects
from image_analysis.markers import MarkerDetection, MarkerType, detect_all_markers
from image_analysis.object_classes import ObjectClass, classify_detection
from image_analysis.plane_detection import Plane3D, detect_multiple_planes, fit_plane_ransac
from image_analysis.point_cloud import PointCloud, create_point_cloud
from image_analysis.pose_estimation import Pose3D, estimate_pose_from_marker
from image_analysis.preprocessing import load_image, normalize_image, resize_image
from image_analysis.slam import SlamConfig, SlamMap, SlamSession
from image_analysis.targeting import TargetOffset, compute_center_offset, draw_crosshair
from image_analysis.viewer import render_depth, render_rgb
from image_analysis.yolo_detector import YoloConfig, YoloDetector

__all__ = [
    "AcquisitionMonitor",
    "AcquisitionReport",
    "CalibrationResult",
    "CameraConfig",
    "Detection",
    "FrameMetrics",
    "MarkerDetection",
    "MarkerType",
    "ObjectClass",
    "Plane3D",
    "PointCloud",
    "Pose3D",
    "RgbdFrame",
    "SlamConfig",
    "SlamMap",
    "SlamSession",
    "TargetOffset",
    "UnitreeCamera",
    "YoloConfig",
    "YoloDetector",
    "assess_frame",
    "calibrate_camera",
    "classify_detection",
    "classify_image",
    "compute_center_offset",
    "create_point_cloud",
    "detect_all_markers",
    "detect_multiple_planes",
    "detect_objects",
    "draw_crosshair",
    "estimate_pose_from_marker",
    "fit_plane_ransac",
    "load_calibration",
    "load_image",
    "normalize_image",
    "render_depth",
    "render_rgb",
    "resize_image",
    "save_calibration",
    "undistort_image",
]
