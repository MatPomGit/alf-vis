# Experimental Sub-projects

This directory contains prototype and research implementations that were
developed during the evolution of the `image_analysis` package. They are
**not part of the main package** and are not installed by `pip install`.

## Contents

| Directory | Description |
|-----------|-------------|
| `bytetrack3/` | ByteTrack v3 — early multi-object tracker prototype |
| `bytetrack4/` | ByteTrack v4 — tracker with SLAM integration stub |
| `cv2/` | OpenCV-based tracking pipeline with RealSense acquisition |
| `image_acquisition/` | Alternative acquisition pipeline with ByteTracker and world map |
| `yolo/` | Standalone YOLO camera integration script |

## Dependencies

These prototypes may require extra packages not listed in the main
`pyproject.toml`. Install them manually as needed:

```bash
pip install ultralytics opencv-python pyrealsense2 open3d pupil-apriltags matplotlib pandas
```

## Status

These sub-projects are archived for reference. Active development has moved
to the `src/image_analysis/` package. Do **not** import from these modules
in production code.
