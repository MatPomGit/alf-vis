# demo_realsense_pipeline – Kompletny potok RealSense + YOLO + eksport CSV

## Czym jest ten projekt?

Demonstracja **kompletnego potoku akwizycji i śledzenia** z użyciem kamery Intel RealSense
(lub zwykłej kamery USB jako fallback).

Projekt skupia się na:
- Synchronizowanym poborze obrazu RGB i mapy głębi z RealSense.
- Śledzeniu obiektów z SORT-like trackerem (filtr Kalmana + Hungarian matching).
- Przypisaniu 3-D punktów świata do każdego toru.
- Eksporcie wyników śledzenia do pliku CSV (opcja `--save-tracking`).
- Budowie uproszczonej mapy świata (`WorldMap`).

Etykiety z opisami wykrytych obiektów wyświetlane są **czerwonym** tekstem ponad ramkami.

## Czym różni się od pozostałych projektów?

| Projekt | Główne zagadnienie |
|---|---|
| `demo_basic_tracking` | Podstawowy tracking 2-D z identyfikatorami |
| **demo_realsense_pipeline** (ten) | Kompletny potok: RealSense + SORT + eksport CSV |
| `demo_3d_world_map` | Projekcja 3-D głębi + stub SLAM |
| `demo_apriltag_fusion` | Fuzja pozycji z AprilTag + filtr Kalmana 3-D |
| `demo_yolo_utils` | Narzędzia preprocesingu NCHW bez kamery |
| `fast_camera` | Najwydajniejsze przetwarzanie w czasie rzeczywistym (wątki) |

## Uruchamianie

```bash
python experimental/demo_realsense_pipeline/main.py
python experimental/demo_realsense_pipeline/main.py --save-tracking outputs/tracking.csv
python experimental/demo_realsense_pipeline/main.py --no-display --max-frames 100
```

## Parametry

- `--save-tracking` – zapis CSV ze śledzonymi ID
- `--max-distance` – maksymalna odległość centroidu przy dopasowaniu
- `--max-missing` – ile klatek tor może zniknąć
- `--no-display` – wyłącza okno podglądu
- `--max-frames` – limit liczby przetwarzanych klatek

## Test bez kamery

```bash
python experimental/demo_realsense_pipeline/test_tracker.py
```

## Wymagane zależności

```bash
pip install ultralytics opencv-python pyrealsense2
```

