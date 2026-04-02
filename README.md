# alf-vis — Image Analysis for Unitree G1 EDU

[![CI](https://github.com/MatPomGit/alf-vis/actions/workflows/ci.yml/badge.svg)](https://github.com/MatPomGit/alf-vis/actions/workflows/ci.yml)

Python library for robot vision on the **Unitree G1 EDU** platform.
Covers RGB-D capture, object detection and tracking (Kalman + YOLO), visual
marker detection (ArUco / AprilTag / QR), camera calibration, 3-D point cloud
processing, SLAM, and image quality metrics.

---

## Package structure

```
src/image_analysis/
├── acquisition_metrics.py  # Frame quality assessment
├── active_vision.py        # Adaptive ROI optimisation
├── calibration.py          # Chessboard camera calibration
├── camera.py               # Unitree G1 EDU RGB-D capture
├── classification.py       # Image classification wrapper (stub)
├── detection.py            # YOLO object detection wrapper
├── kalman_tracking.py      # Multi-object Kalman tracker ★
├── map_visualizer.py       # 3-D map visualisation
├── markers.py              # ArUco / AprilTag / QR detection
├── object_classes.py       # YOLO class label mapping
├── plane_detection.py      # Plane fitting in point clouds
├── point_cloud.py          # RGB-D point cloud generation
├── pose_estimation.py      # 6-DOF pose from markers / depth
├── preprocessing.py        # Load, resize, normalise images
├── slam.py                 # SLAM interface (backends: ORB-SLAM3, RTAB-Map, Open3D)
├── targeting.py            # Target acquisition for active vision
├── utils.py                # Logging, path helpers, image validation
├── viewer.py               # 2-D RGB/depth viewer
└── yolo_detector.py        # YOLO detector wrapper
```

The `★` module is the primary public export:

```python
from image_analysis import KalmanMultiObjectTracker, TrackedObject
```

---

## Installation

### Base (OpenCV + NumPy + Pillow)

```bash
pip install -e .
```

### With optional features

| Extra | Packages | Use case |
|-------|----------|----------|
| `markers` | `pupil-apriltags`, `pyzbar` | AprilTag + QR detection |
| `yolo` | `ultralytics` | YOLO object detection |
| `3d` | `open3d` | Point clouds, SLAM, plane detection |
| `all` | all of the above | Full installation |

```bash
pip install -e ".[markers]"
pip install -e ".[yolo]"
pip install -e ".[3d]"
pip install -e ".[all]"
```

### Development

```bash
pip install -e ".[dev]"
```

---

## Running tests

```bash
# All tests with coverage report
pytest --cov=src/image_analysis --cov-report=term-missing

# Or via Make
make test
```

Coverage must be ≥ 80 % per module.

---

## Linting and type checking

```bash
make lint        # ruff check + format check
make typecheck   # mypy strict
```

---

## Pre-commit hooks

```bash
pip install pre-commit
pre-commit install
```

---

## Experimental sub-projects

Earlier prototype implementations (ByteTrack v3/v4, OpenCV pipeline,
RealSense acquisition) live in [`experimental/`](experimental/README.md).
They are archived for reference and are **not** installed as part of this
package.

---

## Model files

Large `.pt` / `.onnx` / `.tflite` model files are **not** stored in this
repository (see `.gitignore`). Download the YOLO nano model at runtime:

```python
from ultralytics import YOLO
model = YOLO("yolov8n.pt")  # downloads automatically on first use
```

---

## License

See [`docs/LICENSE`](docs/LICENSE).
