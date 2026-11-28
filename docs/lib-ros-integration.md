# Opcjonalna diagnostyka TF2 dla SLAM

Opcjonalny pilotaż lib-ros 0.2.0 przypięty do SHA d4813d48ef60a9649df122d6df3cc056312608b5. Python 3.11+ i zgodne środowisko ROS 2 dla trybu natywnego. Nie zmienia dotychczasowego backendu, wymagań podstawowych ani sterowania.

```bash
python -m pip install -r requirements-lib-ros.txt
python tools/lib_ros_probe.py --self-test
python tools/lib_ros_probe.py
```

Test offline weryfikuje kontrakt aplikacji i publiczne API biblioteki. Uruchomienie natywne tylko w autoryzowanym środowisku ROS 2. Brak deklaracji walidacji sprzętowej; wersja eksperymentalna, bez publicznego wydania.
