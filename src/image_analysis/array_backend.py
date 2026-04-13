"""Helpers for selecting NumPy/CuPy backends and PyScript runtime detection."""

from __future__ import annotations

import os
import sys
from types import ModuleType

import numpy as np


def is_pyscript_runtime() -> bool:
    """Return True when the code is running inside a PyScript/Pyodide environment."""
    # W PyScript interpreter działa na WebAssembly i zwykle raportuje platformę ``emscripten``.
    if sys.platform == "emscripten":
        return True

    # Część środowisk ustawia znaczniki środowiskowe pomocne przy integracji front-end.
    return os.getenv("PY_SCRIPT") == "1" or os.getenv("PYODIDE") == "1"


def get_array_backend(prefer_gpu: bool = False) -> ModuleType:
    """Return an array module compatible with NumPy API.

    The function always returns ``numpy`` unless ``prefer_gpu=True`` and ``cupy``
    can be imported successfully.

    Args:
        prefer_gpu: If True, try to return the ``cupy`` module.

    Returns:
        Module object implementing NumPy-like API (`numpy` or `cupy`).
    """
    if not prefer_gpu:
        return np

    try:
        import cupy as cp
    except ImportError:
        return np

    return cp


def to_numpy(array: object) -> np.ndarray:
    """Convert NumPy/CuPy arrays to a NumPy ``ndarray``.

    Args:
        array: Object exposing array protocol, a NumPy array, or a CuPy array.

    Returns:
        NumPy representation of input data.
    """
    # Najpierw szybka ścieżka dla natywnego ``ndarray``.
    if isinstance(array, np.ndarray):
        return array

    get_fn = getattr(array, "get", None)
    if callable(get_fn):
        converted = get_fn()
        if isinstance(converted, np.ndarray):
            return converted

    return np.asarray(array)
