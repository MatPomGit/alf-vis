
# demo_3d_world_map – Projekcja 3-D głębi + stub SLAM

## Czym jest ten projekt?

Demonstracja **budowy mapy przestrzeni 3-D** na podstawie informacji o głębi z kamery
Intel RealSense i detekcji YOLO. Projekt zawiera stub integracji SLAM (Simultaneous
Localisation and Mapping), który pokazuje architekturę rozwiązania bez pełnej implementacji.

Projekt skupia się na:
- Projekcji centrów bounding boxów z przestrzeni 2-D do 3-D przy użyciu mapy głębi.
- Tworzeniu i wizualizacji uproszczonej mapy świata (`WorldMap`).
- Demonstracji podstawowej architektury SLAM z modularnym stubem (`slam_stub.py`).
- Wizualizacji live widoku SLAM w osobnym oknie (`slam_view.py`).

## Czym różni się od pozostałych projektów?

| Projekt | Główne zagadnienie |
|---|---|
| `demo_basic_tracking` | Podstawowy tracking 2-D z identyfikatorami |
| `demo_realsense_pipeline` | Kompletny potok: RealSense + SORT + eksport CSV |
| **demo_3d_world_map** (ten) | Projekcja 3-D głębi + stub SLAM + wizualizacja mapy |
| `demo_apriltag_fusion` | Fuzja pozycji z AprilTag + filtr Kalmana 3-D |
| `demo_yolo_utils` | Narzędzia preprocesingu NCHW bez kamery |
| `fast_camera` | Najwydajniejsze przetwarzanie w czasie rzeczywistym (wątki) |

## Struktura plików

| Plik | Opis |
|---|---|
| `main.py` | Główna pętla: YOLO + RealSense + projekcja 3-D + mapa |
| `realsense.py` | Abstrakcja kamery głębi RealSense |
| `depth_projection.py` | Konwersja bounding box → punkt 3-D |
| `world_map.py` | Globalny układ odniesienia i chmura punktów |
| `slam_stub.py` | Stub miejsca na integrację ORB-SLAM3 / innych |
| `slam_view.py` | Wizualizacja live widoku SLAM |
| `visualize_map.py` | Offline wizualizacja zapisanej mapy |

## Uruchamianie

```bash
python experimental/demo_3d_world_map/main.py
```

## Wymagane zależności

```bash
pip install ultralytics opencv-python pyrealsense2 open3d
```

