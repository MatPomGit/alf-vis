# Szablon Projektu – Analiza Obrazu w Pythonie

## Wymagania systemowe

| Wymaganie     | Wersja minimalna |
|---------------|-----------------|
| Python        | 3.11             |
| pip           | 23.x             |
| Git           | 2.x              |

Zalecane środowisko: **virtualenv** lub **conda**.

---

## Instalacja

```bash
# Sklonuj repozytorium (lub użyj jako szablonu w GitHub)
git clone https://github.com/<uzytkownik>/<projekt>.git
cd <projekt>

# Utwórz i aktywuj wirtualne środowisko
python -m venv .venv
source .venv/bin/activate   # Linux / macOS
# .venv\Scripts\activate    # Windows

# Zainstaluj zależności
pip install -e ".[dev]"
```

---

## Użycie

```python
from image_analysis.preprocessing import load_image, resize_image
from image_analysis.detection import detect_objects
from image_analysis.classification import classify_image

# Wczytaj i przygotuj obraz
image = load_image("data/raw/sample.jpg")
resized = resize_image(image, width=640, height=480)

# Wykryj obiekty
detections = detect_objects(resized)

# Sklasyfikuj obraz
label, confidence = classify_image(resized)
print(f"Etykieta: {label}, pewność: {confidence:.2%}")
```

Więcej przykładów: [`notebooks/example_analysis.ipynb`](notebooks/example_analysis.ipynb).

---

## Testowanie

```bash
# Uruchom wszystkie testy
pytest

# Testy z pokryciem kodu
pytest --cov=src/image_analysis --cov-report=term-missing

# Testy jednego modułu
pytest tests/test_preprocessing.py -v
```

---

## Styl kodu i narzędzia jakości

Projekt używa następujących narzędzi (skonfigurowanych w `pyproject.toml`):

| Narzędzie  | Zastosowanie                     |
|------------|----------------------------------|
| `ruff`     | Lintowanie i formatowanie kodu   |
| `mypy`     | Statyczna analiza typów          |
| `pytest`   | Testy jednostkowe                |
| `pre-commit` | Weryfikacja przed commitem     |

```bash
# Lintowanie
ruff check src/ tests/

# Formatowanie
ruff format src/ tests/

# Sprawdzanie typów
mypy src/

# Instalacja hooków pre-commit
pre-commit install
pre-commit run --all-files
```

---

## Współpraca z agentami AI

Repozytorium zawiera dedykowane instrukcje dla agentów AI:

| Plik                                  | Agent              |
|---------------------------------------|--------------------|
| `.github/copilot-instructions.md`     | GitHub Copilot     |
| `AGENTS.md`                           | Codex / OpenAI     |
| `CLAUDE.md`                           | Claude (Anthropic) |

Instrukcje obejmują:
- zasady stylu kodu (PEP 8, type hints, docstringi Google-style),
- wymagania testowe (pytest, pokrycie > 80 %),
- wzorce specyficzne dla analizy obrazu,
- reguły bezpieczeństwa i wydajności.

---

## Wkład w projekt

1. Utwórz branch z opisową nazwą: `feature/<nazwa>` lub `fix/<nazwa>`.
2. Wprowadź zmiany przestrzegając zasad zawartych w `AGENTS.md` / `CLAUDE.md`.
3. Uruchom testy i linter przed wystawieniem PR.
4. Wypełnij szablon Pull Request.

## ToDo
Create src/image_analysis/camera.py – capture from Unitree G1 EDU camera (req. 1)
Create src/image_analysis/calibration.py – chessboard calibration (req. 2)
Create src/image_analysis/markers.py – AprilTag / ArUco / CCTag / QR detection (req. 3)
Create src/image_analysis/yolo_detector.py – YOLO-based object detection (req. 4)
Create src/image_analysis/object_classes.py – classification into 5 categories (req. 5)
Create src/image_analysis/targeting.py – deviation from image center (req. 6)
Create src/image_analysis/pose_estimation.py – 3D pose of objects (req. 7)
Create src/image_analysis/slam.py – real-time SLAM (req. 8)
Create src/image_analysis/plane_detection.py – flat surface detection in 3D (req. 9)
Create src/image_analysis/viewer.py – 2D RGB and depth image viewer (req. 10)
Create src/image_analysis/point_cloud.py – RGB+depth 3D synthesis (req. 11)
Create src/image_analysis/map_visualizer.py – real-time 3D map view (req. 12)
Create src/image_analysis/acquisition_metrics.py – acquisition error assessment (req. 13)
Add corresponding tests for each new module
Update src/image_analysis/__init__.py with new exports
Update pyproject.toml with optional dependencies
Update requirements.txt
Update README.md and docs/index.md

---

## Licencja

Projekt objęty licencją **Apache 2.0** – szczegóły w pliku [LICENSE](LICENSE).
