from __future__ import annotations

import time
from pathlib import Path
from typing import Callable, Tuple, TypeVar

import yaml

from common.models import AppConfig, CameraCalibration


T = TypeVar("T")


def timed_call(fn: Callable[..., T], *args, **kwargs) -> Tuple[T, float]:
    """Mierzy czas wykonania funkcji w milisekundach."""
    start = time.perf_counter()
    result = fn(*args, **kwargs)
    elapsed_ms = (time.perf_counter() - start) * 1000.0
    return result, round(elapsed_ms, 3)


def ensure_dir(path: str | Path) -> Path:
    """Tworzy katalog, jeśli nie istnieje."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def load_config(path: str | Path) -> AppConfig:
    """Wczytuje konfigurację YAML."""
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return AppConfig.model_validate(data)


def load_camera_calibration(path: str | Path) -> CameraCalibration:
    """Wczytuje parametry kalibracji kamery."""
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return CameraCalibration.model_validate(data)

common/calibration.py
from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Tuple

import cv2
import numpy as np
import yaml

from common.models import CameraCalibration


def calibrate_camera_from_chessboard(
    image_paths: list[str],
    board_size: tuple[int, int],
    square_size_m: float,
) -> CameraCalibration:
    """Kalibruje kamerę na podstawie zdjęć szachownicy."""
    objp = np.zeros((board_size[0] * board_size[1], 3), np.float32)
    objp[:, :2] = np.mgrid[0:board_size[0], 0:board_size[1]].T.reshape(-1, 2)
    objp *= square_size_m

    objpoints = []
    imgpoints = []
    image_shape = None

    for image_path in image_paths:
        img = cv2.imread(image_path)
        if img is None:
            continue

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        ok, corners = cv2.findChessboardCorners(gray, board_size, None)
        if not ok:
            continue

        corners2 = cv2.cornerSubPix(
            gray,
            corners,
            (11, 11),
            (-1, -1),
            (
                cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER,
                30,
                0.001,
            ),
        )

        objpoints.append(objp)
        imgpoints.append(corners2)
        image_shape = gray.shape[::-1]

    if not objpoints or image_shape is None:
        raise RuntimeError("Nie udało się zebrać poprawnych punktów do kalibracji kamery.")

    rms, camera_matrix, dist_coeffs, _, _ = cv2.calibrateCamera(
        objpoints,
        imgpoints,
        image_shape,
        None,
        None,
    )

    return CameraCalibration(
        image_width=int(image_shape[0]),
        image_height=int(image_shape[1]),
        camera_matrix=camera_matrix.tolist(),
        distortion_coefficients=dist_coeffs.flatten().tolist(),
        calibration_rms=float(rms),
    )


def save_camera_calibration(calibration: CameraCalibration, output_path: str | Path) -> None:
    """Zapisuje kalibrację kamery do YAML."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(calibration.model_dump(), f, sort_keys=False)



""" 
from __future__ import annotations
import time
from pathlib import Path
from typing import Callable, TypeVar, Tuple
import yaml
from common.models import AppConfig

# ...
T = TypeVar("T")
# Mierzy czas wykonania funkcji w milisekundach
def timed_call(fn: Callable[..., T], *args, **kwargs) -> Tuple[T, float]:
    start = time.perf_counter()
    result = fn(*args, **kwargs)
    elapsed_ms = (time.perf_counter() - start) * 1000.0
    return result, round(elapsed_ms, 3)

# Tworzy katalog, jeśli nie istnieje
def ensure_dir(path: str | Path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p

# Wczytuje konfigurację YAML i waliduje ją przez Pydantic
def load_config(path: str | Path) -> AppConfig:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return AppConfig.model_validate(data)
 """

""" old
from __future__ import annotations
from pathlib import Path
def ensure_dir(path: str | Path) -> Path:
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path 
"""