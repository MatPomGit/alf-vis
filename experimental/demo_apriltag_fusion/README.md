Uwagi techniczne:

- Gating: próg ustawiony na ~9 (3D, kompromis między odrzucaniem outlierów a utrzymaniem tracków)
- Adaptive R: obecnie uproszczone (stałe 0.9 dla stabilności — możesz podać realne box.conf)
- Fuzja markerów: ważona decision_margin
- CSV: frame, id, x, y, z
