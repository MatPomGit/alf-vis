# YOLO + ByteTrack + 3D + SLAM (v4)

## Opis
System do:
- detekcji obiektów (YOLO)
- rekonstrukcji 3D (RealSense)
- stabilizacji trajektorii
- budowy mapy świata (AprilTag / SLAM-ready)

---

## Instalacja
pip install -r requirements.txt

## Uruchomienie
python main.py

Dodatkowe opcje:
- zapis mapy do PLY: `python main.py --save-map outputs/map.ply`
- uruchomienie headless: `python main.py --no-display`
- ograniczenie liczby klatek: `python main.py --max-frames 100`

---

## Test bez RealSense
Prosty smoke test, który nie wymaga kamery głębi:

`python test_no_realsense.py`

Test tworzy syntetyczną chmurę punktów i zapisuje ją do:
`test_outputs/world_map_test.ply`

---

## Struktura plików

### realsense.py
Obsługa kamery głębi. Jeżeli `pyrealsense2` nie jest zainstalowane albo brak urządzenia,
moduł przechodzi w tryb niedostępny zamiast wywalać import całej aplikacji.

### depth_projection.py
Konwersja bounding box → punkt 3D.

### world_map.py
Tworzy globalny układ odniesienia:
- transformacja kamera → świat
- akumulacja chmury punktów
- zapis mapy do PLY

### main.py
Główna pętla:
- YOLO detection
- projekcja 3D
- aktualizacja mapy
- opcjonalny zapis mapy do pliku PLY

### slam_stub.py
Miejsce na integrację SLAM (np. ORB-SLAM3).

### visualize_map.py
Wizualizacja mapy.

---

## Co robi system
1. Wykrywa obiekty
2. Pobiera głębię (RealSense)
3. Przekształca do 3D
4. Buduje mapę świata
5. Może zapisać chmurę punktów do PLY

---

## Następne kroki
- integracja ORB-SLAM3
- RViz2
- filtrowanie / kolorowanie chmury punktów
