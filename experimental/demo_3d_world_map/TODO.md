# TODO – demo_3d_world_map

## Brakujące funkcjonalności

- [ ] `slam_stub.py` to tylko szkielet — brak prawdziwej integracji ORB-SLAM3 / OpenVSLAM
- [ ] Brak ekstrapolacji pozycji kamery między klatkami (odometr wizyjny)
- [ ] Mapa świata nie jest zapisywana do pliku PLY / PCD ani ROS bag
- [ ] Wizualizacja `slam_view.py` nie jest zsynchronizowana z główną pętlą w czasie rzeczywistym
- [ ] Brak filtrowania outlierów w chmurze punktów (np. statystyczny filtr Open3D)
- [ ] Brak kalibracji zewnętrznej między kamerą RGB a głębią (zakładana tożsamość)
- [ ] `visualize_map.py` wymaga ręcznego podania ścieżki do pliku mapy
- [ ] Brak obsługi trybu monocularnego (bez RealSense)
- [ ] Brak śledzenia ID obiektów między klatkami w mapie 3-D
