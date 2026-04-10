# Robot Perception — instrukcja uruchomienia krok po kroku

Ten README jest napisany tak, aby można było przechodzić go linia po linii i wklejać kolejne komendy do terminala.

Projekt zawiera:
- warstwę `perception/` z maszyną stanów,
- warstwę `slam/` z mostkiem do RTAB-Map,
- GUI diagnostyczne w `gui/`,
- obsługę RGB-D z fallbackiem do RGB-only,
- detekcję markerów wizyjnych przez `VisualMarkerService`:
  - AprilTag,
  - QR-code,
  - CCTag jako szkielet integracyjny z `TODO`,
- publikację ROS2,
- zapis chmury punktów do PLY.

## 1. Założenia środowiskowe

### Conda-first policy (host)

Na hoście wspieramy wyłącznie uruchamianie w środowisku `conda` `robot_perception`.
Uruchomienia poza tym środowiskiem nie są wspierane i mogą zakończyć się błędem guardów środowiskowych.

Poniższe instrukcje zakładają system Linux z już zainstalowanym ROS2. Projekt był pisany pod użycie z ROS2 i RTAB-Map jako zewnętrznym komponentem.

Przed rozpoczęciem upewnij się, że masz:
- `conda` lub `miniconda`,
- działające ROS2,
- dostęp do topiców RTAB-Map, jeśli chcesz uruchamiać warstwę SLAM bridge,
- kamerę RGB, a opcjonalnie także depth source.

## 1.1. Profile Docker Compose

W projekcie są zdefiniowane dwa profile uruchomieniowe:

- `core` — tryb offline MP4, bez ROS2 i bez dostępu do urządzeń `/dev`,
- `ros-hw` — tryb ROS2 + mostki SLAM/RTAB-Map + dostęp do urządzeń `/dev`.

Przed uruchomieniem skopiuj plik przykładowy zmiennych:

```bash
cp .env.example .env
```

### Checklista dla profilu `ros-hw`

Przed startem `ros-hw` sprawdź:

- [ ] czy wskazana dystrybucja ROS jest dostępna (`ROS_DISTRO` w `.env`),
- [ ] czy są widoczne topici RTAB-Map (`RTABMAP_ODOM_TOPIC`, `RTABMAP_MAPDATA_TOPIC`, `RTABMAP_LOCALIZATION_TOPIC`),
- [ ] czy użytkownik ma uprawnienia do urządzeń kamery (`/dev/video*`).

Szybka weryfikacja na hoście:

```bash
source /opt/ros/${ROS_DISTRO}/setup.bash
ros2 topic list | grep rtabmap
ls -l /dev/video*
```

### Przykłady uruchomienia profili

Profil `core` (offline MP4, bez ROS2):

```bash
docker compose --profile core run --rm robot-perception-core
```

Profil `ros-hw` (ROS2 + RTAB-Map bridge + `/dev`):

```bash
docker compose --profile ros-hw run --rm robot-perception-ros-hw
```

## Wersjonowanie aplikacji

Wersja aplikacji jest wyliczana automatycznie na podstawie liczby commitów na gałęzi `main`:
- format: `0.1.<liczba_commitów_main>`,
- z każdym nowym commitem na `main` numer rośnie automatycznie,
- opcjonalnie można nadpisać wersję przez zmienną środowiskową `ROBOT_PERCEPTION_VERSION`.

Wersja jest widoczna:
- w CLI przez `--version` (np. `python main_perception.py --version`),
- w CLI przez szybki skrót `python run_module.py version`,
- w GUI w tytule okna oraz pasku statusu.

Autor aplikacji widoczny w metadanych CLI/GUI: `J2S`.

## 2. Przejście do katalogu projektu

Najpierw przejdź do katalogu projektu:

```bash
cd /ścieżka/do/robot_perception
```

Jeżeli rozpakowałeś archiwum do bieżącego katalogu i katalog nazywa się dokładnie `robot_perception`, użyj:

```bash
cd robot_perception
```

## 3. Utworzenie środowiska Conda

Uruchom bootstrap środowiska:

```bash
python bootstrap_conda.py
```

Aktywuj środowisko (krok wymagany, bez alternatyw hostowych):

```bash
conda activate robot_perception
```

## 4. Canonical manifest runtime i polityka wersjonowania

W tym projekcie obowiązuje jedna kanoniczna definicja środowiska runtime:
- `environment.yml` — **źródło prawdy** dla zależności uruchomieniowych,
- `requirements.txt` — plik pomocniczy, **generowany automatycznie** z `environment.yml`.

Polityka wersjonowania:
- pakiety niekrytyczne: minimalne wersje (`>=`),
- pakiety krytyczne runtime: piny deterministyczne:
  - `numpy=1.26.4`,
  - `opencv=4.9.0`,
  - `open3d==0.19.0`,
  - `ultralytics==8.3.0`.

Po każdej zmianie `environment.yml` odśwież plik `requirements.txt`:

```bash
python scripts/sync_requirements.py
```

Jeżeli w Twoim środowisku Conda nie ma `tkinter`, doinstaluj go systemowo albo przez Condę:

```bash
conda install -c conda-forge tk
```

## 5. Załadowanie środowiska ROS2

Załaduj ROS2 do bieżącej sesji terminala.

Przykład dla ROS2 Humble:

```bash
source /opt/ros/humble/setup.bash
```

Jeżeli używasz innej dystrybucji ROS2, podmień ścieżkę odpowiednio.

Jeżeli masz własny workspace ROS2 z pakietami `rtabmap_msgs` albo dodatkowymi zależnościami, doładuj też overlay workspace:

```bash
source ~/twoj_ros2_ws/install/setup.bash
```

## 6. Weryfikacja importów Pythona

Uruchom szybki test importów. To pozwoli od razu wychwycić brakujące biblioteki:

```bash
python - <<'PY'
import cv2
import numpy
import open3d
import pydantic
import pupil_apriltags
import ultralytics
import tkinter
import transforms3d
print('OK: importy użytkowe działają')
PY
```

Jeżeli chcesz też sprawdzić importy ROS2:

```bash
python - <<'PY'
import rclpy
import tf2_ros
from std_msgs.msg import String
from sensor_msgs.msg import PointCloud2
print('OK: importy ROS2 działają')
PY
```

## 7. Konfiguracja projektu

Sprawdź główny plik konfiguracyjny:

```bash
cat config/settings.yaml
```

Sprawdź plik kalibracji kamery:

```bash
cat config/camera_calibration.yaml
```

Najważniejsze pola w `config/settings.yaml`, które zwykle trzeba dopasować:
- `camera_id`
- `depth_camera_id`
- `default_camera_source`
- `rtabmap_odom_topic`
- `rtabmap_mapdata_topic`
- `rtabmap_localization_topic`
- `apriltag_enabled`
- `cctag_enabled`
- `qr_enabled`
- `visual_attention_mode`

## 8. Znaczenie `visual_attention_mode`

W pliku `config/settings.yaml` możesz ustawić tryb active vision:
- `0` — brak modułu uwagi, używany cały obraz,
- `1` — bazowy active vision,
- `2` — Foveated Diffusion, obecnie fallback do bazowego ROI,
- `3` — FoveaTer, obecnie fallback do bazowego ROI,
- `4` — RetinaViT, obecnie fallback do bazowego ROI.

Jeżeli chcesz na szybko wyłączyć active vision i używać całego obrazu, ustaw:

```bash
sed -i 's/^visual_attention_mode:.*/visual_attention_mode: 0/' config/settings.yaml
```

Jeżeli chcesz wrócić do trybu bazowego:

```bash
sed -i 's/^visual_attention_mode:.*/visual_attention_mode: 1/' config/settings.yaml
```

## 9. Kalibracja kamery

Jeżeli chcesz wygenerować własny plik kalibracji kamery na podstawie zdjęć szachownicy, umieść zdjęcia PNG w katalogu, na przykład:

```bash
mkdir -p calibration_images
```

Następnie uruchom:

```bash
python tools/calibrate_camera.py calibration_images --cols 9 --rows 6 --square-size 0.024 --output config/camera_calibration.yaml
```

Po tym sprawdź wynik:

```bash
cat config/camera_calibration.yaml
```

## 10. Uruchomienie pojedynczych modułów diagnostycznych

### 10.1. Detekcja markerów wizyjnych

Uruchom test detekcji markerów:

```bash
python run_module.py markers
```

To uruchomi:
- kamerę RGB,
- `VisualMarkerService`,
- detekcję AprilTag,
- detekcję QR-code,
- próbę detekcji CCTag, która obecnie jest szkieletem z `TODO`.

### 10.2. Budowa chmury punktów

Uruchom test RGB-D / RGB-only:

```bash
python run_module.py rgbd
```

Jeżeli źródło depth będzie dostępne, zostanie użyta prawdziwa ścieżka RGB-D.
Jeżeli nie będzie dostępne, pipeline przejdzie do uproszczonej pseudochmury z RGB.

### 10.3. Test mostka RTAB-Map

Uruchom test warstwy SLAM bridge:

```bash
python run_module.py rtabmap_bridge
```

To polecenie:
- utworzy node ROS2,
- podepnie `RTABMapRosBridge`,
- odczyta przez chwilę topici,
- wypisze zmapowany `SlamStatus`.

## 11. Uruchomienie warstwy percepcji

### 11.1. Tryb RGB-D

```bash
python main_perception.py --source rgbd
```

Jeżeli depth source nie będzie dostępne i `allow_rgb_fallback: true`, program sam przejdzie do trybu RGB-only.

### 11.2. Wymuszenie trybu RGB-only

```bash
python main_perception.py --source rgb
```

Ten tryb jest przydatny, gdy:
- nie masz kamery depth,
- chcesz testować pipeline tylko na obrazie RGB,
- chcesz odseparować błędy depth od reszty logiki.

## 12. Uruchomienie warstwy SLAM bridge

Uruchom niezależny proces odbierający stan RTAB-Map:

```bash
python main_slam.py
```

To uruchamia:
- `SlamRosNode`,
- `TfService`,
- `RTABMapRosBridge`,
- publikację uproszczonego statusu SLAM na dodatkowym topicu `/slam/status`.

## 13. Uruchomienie GUI

Uruchom panel diagnostyczny:

```bash
python run_module.py gui
```

GUI pozwala:
- wystartować percepcję,
- zatrzymać percepcję,
- wystartować SLAM bridge,
- zatrzymać SLAM bridge,
- wykonać jeden krok maszyny stanów,
- podejrzeć bieżący stan FSM,
- podejrzeć, z jakimi argumentami zostały odpalone ostatnie moduły.

## 14. Typowy scenariusz uruchomienia — kolejność do wklejenia

Jeżeli chcesz po prostu odpalić system od zera, wklej dokładnie te komendy po kolei.

### 14.1. Terminal 1 — percepcja

```bash
cd /ścieżka/do/robot_perception
conda activate robot_perception
source /opt/ros/humble/setup.bash
python main_perception.py --source rgbd
```

### 14.2. Terminal 2 — SLAM bridge

```bash
cd /ścieżka/do/robot_perception
conda activate robot_perception
source /opt/ros/humble/setup.bash
python main_slam.py
```

### 14.3. Terminal 3 — GUI

```bash
cd /ścieżka/do/robot_perception
conda activate robot_perception
source /opt/ros/humble/setup.bash
python run_module.py gui
```

## 15. Szybka diagnostyka ROS2

### 15.1. Lista topiców

```bash
ros2 topic list
```

### 15.2. Sprawdzenie topiców RTAB-Map

```bash
ros2 topic list | grep rtabmap
```

### 15.3. Podgląd uproszczonego statusu SLAM

```bash
ros2 topic echo /slam/status
```

### 15.4. Podgląd stanu percepcji

```bash
ros2 topic echo /perception/state
```

### 15.5. Podgląd publikowanej chmury punktów

```bash
ros2 topic echo /perception/point_cloud
```

## 16. Gdzie szukać zapisanych danych

### 16.1. Zapisane klatki RGB

```bash
ls -lah output/frames
```

### 16.2. Zapisane mapy depth

```bash
ls -lah output/depth
```

### 16.3. Zapisane chmury punktów PLY

```bash
ls -lah output/pointclouds
```

## 17. Najczęstsze problemy i gotowe komendy naprawcze

### Problem 1: `ModuleNotFoundError: No module named transforms3d`

```bash
conda activate robot_perception
pip install transforms3d
```

### Problem 2: `No module named rclpy`

To zwykle znaczy, że nie załadowano środowiska ROS2.

```bash
source /opt/ros/humble/setup.bash
```

Jeżeli używasz własnego workspace:

```bash
source ~/twoj_ros2_ws/install/setup.bash
```

### Problem 3: `Nie udało się otworzyć kamery RGB`

Sprawdź dostępne urządzenia wideo:

```bash
ls /dev/video*
```

Następnie zmień `camera_id` w `config/settings.yaml`.

### Problem 4: `Nie udało się otworzyć źródła depth`

Wymuś tryb RGB-only:

```bash
python main_perception.py --source rgb
```

albo ustaw domyślnie w konfiguracji:

```bash
sed -i 's/^default_camera_source:.*/default_camera_source: rgb/' config/settings.yaml
```

### Problem 5: brak topiców RTAB-Map

Sprawdź, czy RTAB-Map rzeczywiście publikuje topici:

```bash
ros2 topic list | grep rtabmap
```

Jeżeli nazwy topiców są inne niż w konfiguracji, popraw `config/settings.yaml`.

## 18. Minimalna procedura testowa po zmianach w kodzie

Po każdej większej zmianie możesz przejść ten zestaw poleceń:

```bash
cd /ścieżka/do/robot_perception
conda activate robot_perception
source /opt/ros/humble/setup.bash
python run_module.py markers
python run_module.py rgbd
python run_module.py rtabmap_bridge
python main_perception.py --source rgb
```

Jeżeli wszystko przejdzie bez wyjątku, masz dużą szansę, że podstawowe ścieżki działania są nadal poprawne.

## 19. Co w projekcie jest jeszcze otwarte

W kodzie celowo zostawiono `TODO` w miejscach, które zależą od dalszej integracji sprzętowej lub badawczej:
- rzeczywista biblioteka CCTag,
- prawdziwe backendy Foveated Diffusion / FoveaTer / RetinaViT,
- adapter dla RealSense / ZED / topiców ROS2 dla depth,
- własne wiadomości ROS2 `.msg` zamiast JSON w `std_msgs/String`,
- ewentualne dopracowanie semantyki map points w RTAB-Map.

## 20. Najkrótszy zestaw komend „od zera”

Jeżeli chcesz tylko minimalny zestaw komend do uruchomienia, użyj tego:

```bash
cd /ścieżka/do/robot_perception
python bootstrap_conda.py
conda activate robot_perception
pip install transforms3d
source /opt/ros/humble/setup.bash
python run_module.py gui
```

A jeżeli chcesz od razu uruchomić percepcję bez GUI:

```bash
cd /ścieżka/do/robot_perception
conda activate robot_perception
source /opt/ros/humble/setup.bash
python main_perception.py --source rgbd
```


## 13. Praca na nagraniu MP4 (zamiast kamery live)

### 13.1. Odtwarzanie pipeline percepcji na MP4

```bash
python scripts/run_perception_from_mp4.py /sciezka/do/nagrania.mp4 --source rgb --config config/settings.yaml
```

Opcjonalne flagi:
- `--max-frames 300` — zatrzymanie po określonej liczbie pełnych klatek pipeline,
- `--print-snapshot` — wypisywanie pełnego snapshotu JSON na każdej klatce.

### 13.2. Pomiar jakości i stabilności śledzenia do CSV

```bash
python scripts/measure_tracking_from_mp4.py /sciezka/do/nagrania.mp4 --source rgb --csv output/tracking_measurements.csv --config config/settings.yaml
```

Skrypt pomiarowy zapisuje w CSV dane dla **każdego kroku** maszyny stanów, w tym m.in.:
- `frame_id`, `frame_timestamp_sec`, `video_timestamp_sec`,
- stan przed i po kroku (`state_before`, `state_after`),
- liczby detekcji, markerów i tracków,
- metryki stabilności śledzenia (`tracks_mean_displacement_px`, `tracks_max_displacement_px`, liczba tracków nowych/utraconych),
- czasy etapów (`time_ms::...`) dla wszystkich kroków pipeline.

Dzięki temu możesz uruchamiać ten sam plik MP4 wielokrotnie z różnymi parametrami i porównywać jakość śledzenia między konfiguracjami.
