# demo_yolo_utils – Narzędzia preprocesingu dla YOLO (NCHW bilinear resize)

## Czym jest ten projekt?

Zestaw **funkcji narzędziowych do preprocesingu obrazów** w formacie NCHW
(batch × kanały × wysokość × szerokość), stosowanym przez frameworki głębokiego uczenia
(PyTorch, ONNX Runtime, TensorRT).

Projekt skupia się na:
- Efektywnej bilinearnej interpolacji dla tensorów NCHW bez zależności od `cv2`.
- Czystej implementacji NumPy gotowej do przeniesienia na GPU / ONNX.
- Demonstracji jak przygotować wejście do YOLO bez korzystania z Ultralytics pipeline.

## Czym różni się od pozostałych projektów?

| Projekt | Główne zagadnienie |
|---|---|
| `demo_basic_tracking` | Podstawowy tracking 2-D z identyfikatorami |
| `demo_realsense_pipeline` | Kompletny potok: RealSense + SORT + eksport CSV |
| `demo_3d_world_map` | Projekcja 3-D głębi + stub SLAM |
| `demo_apriltag_fusion` | Fuzja pozycji: AprilTag + YOLO + filtr Kalmana 3-D |
| **demo_yolo_utils** (ten) | Preprocessing NCHW bez kamery — tylko NumPy |
| `fast_camera` | Najwydajniejsze przetwarzanie w czasie rzeczywistym (wątki) |

## Zawartość

| Plik | Opis |
|---|---|
| `camera_yolo.py` | Bilinear resize dla tensorów NCHW (`resize_bilinear_nchw`) |

## Użycie w kodzie

```python
from demo_yolo_utils.camera_yolo import resize_bilinear_nchw
import numpy as np

tensor = np.random.rand(1, 3, 480, 640).astype(np.float32)
resized = resize_bilinear_nchw(tensor, out_height=320, out_width=320)
# resized.shape == (1, 3, 320, 320)
```

## Wymagane zależności

```bash
pip install numpy
```
