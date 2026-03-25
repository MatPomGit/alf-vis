# YOLO + RealSense + tracking

Projekt wykonuje detekcję YOLOv8 i prosty tracking wieloobiektowy.

## Nowy tracker

Tracker działa w stylu SORT:
- filtr Kalmana z modelem stałej prędkości dla centroidu bbox,
- globalne dopasowanie detekcji do ścieżek przez Hungarian matching,
- usuwanie torów po zadanej liczbie brakujących klatek.

## Uruchomienie

```bash
python main.py
python main.py --save-tracking outputs/tracking.csv
python main.py --save-tracking outputs/tracking.csv --max-distance 80 --max-missing 5
python main.py --no-display --max-frames 100
```

## Parametry

- `--save-tracking` - zapis CSV ze śledzonymi ID
- `--max-distance` - maksymalna odległość centroidu przy dopasowaniu
- `--max-missing` - ile klatek tor może zniknąć
- `--no-display` - wyłącza okno podglądu
- `--max-frames` - limit liczby przetwarzanych klatek

## Test bez kamery

```bash
python test_tracker.py
```

Wygenerowany plik testowy:
- `test_outputs/tracking_kalman_hungarian.csv`
