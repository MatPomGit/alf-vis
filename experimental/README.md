# Experimental Sub-projects

This directory contains prototype and research implementations that were
developed during the evolution of the `image_analysis` package. They are
**not part of the main package** and are not installed by `pip install`.

Each sub-project focuses on a **different topic** so that they can be used
as standalone learning examples. See the `README.md` inside each folder for
details, and `TODO.md` for known missing features.

## Contents

| Directory | Focus |
|-----------|-------|
| `demo_basic_tracking/` | Podstawowy tracking 2-D: ByteTrack + YOLO, unikalny ID per obiekt |
| `demo_realsense_pipeline/` | Kompletny potok RealSense: SORT tracker, projekcja 3-D, eksport CSV |
| `demo_3d_world_map/` | Budowa mapy 3-D z głębią RealSense + stub SLAM |
| `demo_apriltag_fusion/` | Fuzja pozycji kamery z AprilTag + YOLO + filtr Kalmana 3-D |
| `demo_yolo_utils/` | Narzędzia preprocesingu NCHW bez kamery (bilinear resize NumPy) |
| `fast_camera/` | Minimalne opóźnienie w czasie rzeczywistym: wątki, mały model, drop klatek |

## Dependencies

These prototypes may require extra packages not listed in the main
`pyproject.toml`. Install the `experimental` group for all of them:

```bash
pip install -e ".[experimental]"
```

Or install manually:

```bash
pip install ultralytics opencv-python pyrealsense2 open3d pupil-apriltags matplotlib pandas
```

## Status

These sub-projects are archived for reference. Active development has moved
to the `src/image_analysis/` package. Do **not** import from these modules
in production code.

