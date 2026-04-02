# demo_basic_tracking – Podstawowy tracking obiektów YOLO + ByteTrack

## Czym jest ten projekt?

Minimalny, kompletny przykład **wieloobiektowego śledzenia** (multi-object tracking, MOT)
opartego na detektorze YOLOv8 i prostym trackerze ByteTrack.

Każdy wykryty obiekt otrzymuje unikalny identyfikator (`ID`) zachowywany między klatkami.
Ramki i etykiety z czerwonymi opisami są rysowane bezpośrednio na podglądzie kamery.

## Czym różni się od pozostałych projektów?

| Projekt | Główne zagadnienie |
|---|---|
| **demo_basic_tracking** (ten) | Podstawowy tracking 2-D z identyfikatorami |
| `demo_realsense_pipeline` | Kompletny potok z RealSense, eksport CSV, mapa świata |
| `demo_3d_world_map` | Projekcja 3-D głębi + stub SLAM |
| `demo_apriltag_fusion` | Fuzja pozycji z AprilTag + filtr Kalmana 3-D |
| `demo_yolo_utils` | Narzędzia preprocesingu NCHW bez kamery |
| `fast_camera` | Najwydajniejsze przetwarzanie w czasie rzeczywistym (wątki) |

## Uruchamianie

```bash
python experimental/demo_basic_tracking/main.py
```

## Wymagane zależności

```bash
pip install ultralytics opencv-python
```
