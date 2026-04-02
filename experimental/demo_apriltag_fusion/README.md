# demo_apriltag_fusion – Fuzja AprilTag + YOLO + filtr Kalmana 3-D

## Czym jest ten projekt?

Demonstracja **fuzji pozycji kamery** (wyznaczanej przez markery AprilTag) z
śledzeniem obiektów YOLO i predykcją trajektorii 3-D przez filtr Kalmana.

Projekt skupia się na:
- Detekcji i estymacji pozy markerów AprilTag (rodzina `tag36h11`).
- Fuzji informacji z wielu widzialnych markerów (ważone uśrednianie po `decision_margin`).
- Przekazywaniu wyznaczonej pozycji kamery do stanu filtru Kalmana każdego toru.
- Zapisie trajektorii 3-D do pliku CSV (`trajectory.csv`).

Etykiety z opisami wykrytych obiektów wyświetlane są **czerwonym** tekstem ponad ramkami.

## Czym różni się od pozostałych projektów?

| Projekt | Główne zagadnienie |
|---|---|
| `demo_basic_tracking` | Podstawowy tracking 2-D z identyfikatorami |
| `demo_realsense_pipeline` | Kompletny potok: RealSense + SORT + eksport CSV |
| `demo_3d_world_map` | Projekcja 3-D głębi + stub SLAM |
| **demo_apriltag_fusion** (ten) | Fuzja pozycji: AprilTag + YOLO + filtr Kalmana 3-D |
| `demo_yolo_utils` | Narzędzia preprocesingu NCHW bez kamery |
| `fast_camera` | Najwydajniejsze przetwarzanie w czasie rzeczywistym (wątki) |

## Uruchamianie

```bash
python experimental/demo_apriltag_fusion/main.py
```

Wynik: plik `trajectory.csv` z kolumnami `frame,id,x,y,z`.

## Wymagane zależności

```bash
pip install ultralytics opencv-python pupil-apriltags
```
