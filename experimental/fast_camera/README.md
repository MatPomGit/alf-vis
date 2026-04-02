# fast_camera – Wydajne przetwarzanie obrazów w czasie rzeczywistym

## Czym jest ten projekt?

Program demonstracyjny skupiony wyłącznie na **minimalnym opóźnieniu i maksymalnej
przepustowości** przetwarzania obrazu z kamery w czasie rzeczywistym.

Jest to niezależny, samodzielny program stworzony z inspiracji koncepcją „miniCamera" —
minimalnego, szybkiego oka kamery dostarczającego wyniki jak najszybciej.

## Kluczowe optymalizacje

| Optymalizacja | Opis |
|---|---|
| **Wątki producent/konsument** | Kamera i YOLO działają w oddzielnych wątkach — bez blokowania |
| **Kolejka o głębokości 1** | Stare klatki są automatycznie odrzucane, nigdy nie czekamy na stare dane |
| **Mały rozmiar wejścia YOLO** | Domyślnie `imgsz=320` zamiast 640 — 4× mniejszy tensor |
| **`verbose=False`** | Brak wydruków Ultralytics na konsolę |
| **Licznik FPS** | Wyświetla bieżący FPS w oknie podglądu |

Etykiety z opisami wykrytych obiektów wyświetlane są **czerwonym** tekstem ponad ramkami.

## Czym różni się od pozostałych projektów?

| Projekt | Główne zagadnienie |
|---|---|
| `demo_basic_tracking` | Podstawowy tracking 2-D z identyfikatorami |
| `demo_realsense_pipeline` | Kompletny potok: RealSense + SORT + eksport CSV |
| `demo_3d_world_map` | Projekcja 3-D głębi + stub SLAM |
| `demo_apriltag_fusion` | Fuzja pozycji: AprilTag + YOLO + filtr Kalmana 3-D |
| `demo_yolo_utils` | Preprocessing NCHW bez kamery — tylko NumPy |
| **fast_camera** (ten) | Minimalny czas odpowiedzi: wątki + mała sieć + odrzucanie klatek |

## Uruchamianie

```bash
# Domyślnie: kamera 0, YOLOv8n, imgsz=320, CPU
python experimental/fast_camera/main.py

# GPU z większym modelem
python experimental/fast_camera/main.py --device cuda:0 --model yolov8s.pt --imgsz 416

# Plik wideo bez okna (benchmark)
python experimental/fast_camera/main.py --source video.mp4 --no-display
```

## Parametry

- `--source` – indeks kamery (int) lub ścieżka do pliku wideo (domyślnie: `0`)
- `--model` – plik wag YOLO (domyślnie: `yolov8n.pt`)
- `--device` – urządzenie: `cpu` / `cuda:0` / `mps` (domyślnie: `cpu`)
- `--imgsz` – rozmiar wejściowy YOLO w pikselach (domyślnie: `320`)
- `--no-display` – wyłącza okno podglądu (tryb benchmark)

## Wymagane zależności

```bash
pip install ultralytics opencv-python
```
