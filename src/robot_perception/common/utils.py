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
    """Mierzy czas wykonania funkcji w milisekundach."""
    start = time.perf_counter()
    result = fn(*args, **kwargs)
    elapsed_ms = (time.perf_counter() - start) * 1000.0
    return result, round(elapsed_ms, 3)

# Tworzy katalog, jeśli nie istnieje
def ensure_dir(path: str | Path) -> Path:
    """Tworzy katalog, jeśli nie istnieje."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p

# Wczytuje konfigurację YAML i waliduje ją przez Pydantic
def load_config(path: str | Path) -> AppConfig:
    """Wczytuje konfigurację YAML i waliduje ją przez Pydantic."""
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return AppConfig.model_validate(data)






""" old
from __future__ import annotations
from pathlib import Path
def ensure_dir(path: str | Path) -> Path:
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path 
"""