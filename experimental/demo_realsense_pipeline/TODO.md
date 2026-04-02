# TODO – demo_realsense_pipeline

## Brakujące funkcjonalności

- [ ] Brak wizualizacji mapy świata w czasie rzeczywistym (jest tylko `visualize_map.py` offline)
- [ ] Brak obsługi wielu kamer RealSense jednocześnie
- [ ] Tracker wymaga ręcznego ustawienia `--max-distance` (brak auto-kalibracji)
- [ ] Brak re-ID — zmiana pozycji kamery powoduje duplikaty torów
- [ ] Brak eksportu ścieżek 3-D do formatu ROS bag / PLY
- [ ] Wizualizacja mapy 2-D nie pokazuje niepewności punktów 3-D
- [ ] Brak testów integracyjnych dla całego potoku (tylko `test_tracker.py`)
- [ ] Obsługa głębi RealSense wymaga ręcznej kalibracji kamery kolorowej
