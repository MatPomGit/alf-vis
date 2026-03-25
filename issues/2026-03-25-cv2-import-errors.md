# Additional issues discovered (not fixed in this patch)

## 1) acquisition_metrics imports cv2 at module import time
- **File:** `src/image_analysis/acquisition_metrics.py`
- **Problem:** Importing the module fails in headless/container environments where `libGL.so.1` is unavailable.
- **Impact:** Test collection stops for `tests/test_acquisition_metrics.py`.

## 2) calibration imports cv2 at module import time
- **File:** `src/image_analysis/calibration.py`
- **Problem:** Same headless import failure (`ImportError: libGL.so.1`).
- **Impact:** Breaks `tests/test_calibration.py` and transitive imports used by point-cloud and pose-estimation tests.

## 3) camera imports cv2 at module import time
- **File:** `src/image_analysis/camera.py`
- **Problem:** Same headless import failure (`ImportError: libGL.so.1`).
- **Impact:** Breaks `tests/test_camera.py` collection.

## 4) markers imports cv2 at module import time
- **File:** `src/image_analysis/markers.py`
- **Problem:** Same headless import failure (`ImportError: libGL.so.1`).
- **Impact:** Breaks `tests/test_markers.py` collection.

## 5) viewer imports cv2 at module import time
- **File:** `src/image_analysis/viewer.py`
- **Problem:** Same headless import failure (`ImportError: libGL.so.1`).
- **Impact:** Breaks `tests/test_viewer.py` collection.
