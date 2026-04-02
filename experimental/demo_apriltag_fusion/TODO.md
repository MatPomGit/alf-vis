# TODO – demo_apriltag_fusion

## Brakujące funkcjonalności

- [ ] Parametry kamery (`fx, fy, cx, cy`) są hardcodowane — brak wczytywania z pliku kalibracji
- [ ] Brak obsługi różnych rodzin markerów AprilTag (tylko `tag36h11`)
- [ ] Fuzja markerów zakłada statyczną kamerę — brak kompensacji ruchu
- [ ] `compute_R` zakłada stałą macierz szumu — brak adaptacyjnego filtru Kalmana
- [ ] Trajektoria zapisywana jest do `trajectory.csv` w bieżącym katalogu (brak `--output`)
- [ ] Brak wizualizacji pozycji 3-D markerów na obrazie
- [ ] Brak obsługi trybu bez markerów (fallback do tracking 2-D)
- [ ] Otworzenie pliku CSV bez context managera (`with`) — ryzyko niezamkniętego pliku
- [ ] Brak ograniczenia liczby klatek (`--max-frames`)
- [ ] Brak testów jednostkowych dla `fuse_tags` i filtru Kalmana
