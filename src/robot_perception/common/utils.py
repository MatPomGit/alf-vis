from __future__ import annotations
import time
from pathlib import Path
from typing import Callable, Tuple, TypeVar
import yaml
from common.models import AppConfig, CameraCalibration
T = TypeVar("T")

def timed_call(fn: Callable[..., T], *args, **kwargs) -> Tuple[T, float]:
    start = time.perf_counter()
    result = fn(*args, **kwargs)
    elapsed_ms = (time.perf_counter() - start) * 1000.0
    return result, round(elapsed_ms, 3)

def ensure_dir(path: str | Path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p

def load_config(path: str | Path) -> AppConfig:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return AppConfig.model_validate(data)

def load_camera_calibration(path: str | Path) -> CameraCalibration:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return CameraCalibration.model_validate(data)
