
# YOLO + ByteTrack + 3D + SLAM (v4)

## Opis
System do:
- detekcji obiektów (YOLO)
- rekonstrukcji 3D (RealSense)
- stabilizacji trajektorii
- budowy mapy świata (AprilTag / SLAM-ready)

---

## Krok po kroku

### 1. Instalacja
pip install -r requirements.txt

---

### 2. Uruchomienie
python main.py

---

## Struktura plików

### realsense.py
Obsługa kamery głębi. Dostarcza:
- obraz RGB
- mapę głębi
- funkcję deproject()

---

### depth_projection.py
Konwersja bounding box → punkt 3D.

---

### world_map.py
Tworzy globalny układ odniesienia:
- transformacja kamera → świat
- akumulacja chmury punktów

---

### main.py
Główna pętla:
- YOLO detection
- projekcja 3D
- aktualizacja mapy

---

### slam_stub.py
Miejsce na integrację SLAM (np. ORB-SLAM3).

---

### visualize_map.py
Wizualizacja mapy (do rozbudowy).

---

## Co robi system

1. Wykrywa obiekty
2. Pobiera głębię (RealSense)
3. Przekształca do 3D
4. Buduje mapę świata

---

## Następne kroki

- integracja ORB-SLAM3
- RViz2
- zapis mapy do PLY
