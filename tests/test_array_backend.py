"""Tests for NumPy/CuPy backend helpers."""

from __future__ import annotations

import sys
from types import SimpleNamespace

import numpy as np

from image_analysis.array_backend import get_array_backend, is_pyscript_runtime, to_numpy


class _FakeCuPyArray:
    """Simple stand-in for a CuPy-like object exposing ``get``."""

    def __init__(self, payload: np.ndarray) -> None:
        self._payload = payload

    def get(self) -> np.ndarray:
        """Return materialized NumPy payload."""
        return self._payload


def test_get_array_backend_returns_numpy_by_default() -> None:
    """Default backend should be NumPy."""
    backend = get_array_backend()
    assert backend is np


def test_get_array_backend_returns_numpy_when_cupy_missing() -> None:
    """GPU preference should gracefully fallback when CuPy is unavailable."""
    backend = get_array_backend(prefer_gpu=True)
    assert backend is np


def test_get_array_backend_returns_fake_cupy_when_present(monkeypatch) -> None:
    """When CuPy import succeeds the helper should return CuPy module."""
    fake_cupy = SimpleNamespace(name="fake-cupy")
    # Podmieniamy moduł w cache importów, aby nie wymagać prawdziwego CUDA/CuPy w CI.
    monkeypatch.setitem(sys.modules, "cupy", fake_cupy)

    backend = get_array_backend(prefer_gpu=True)
    assert backend is fake_cupy


def test_is_pyscript_runtime_detects_env_flags(monkeypatch) -> None:
    """Env flags should be treated as PyScript/Pyodide runtime markers."""
    monkeypatch.setenv("PY_SCRIPT", "1")
    assert is_pyscript_runtime() is True

    monkeypatch.delenv("PY_SCRIPT", raising=False)
    monkeypatch.setenv("PYODIDE", "1")
    assert is_pyscript_runtime() is True

    monkeypatch.delenv("PYODIDE", raising=False)
    assert is_pyscript_runtime() is (sys.platform == "emscripten")


def test_to_numpy_returns_same_array_for_numpy_input() -> None:
    """NumPy arrays should pass through without extra copies."""
    source = np.array([1, 2, 3])
    result = to_numpy(source)
    assert result is source


def test_to_numpy_uses_get_method_for_cupy_like_objects() -> None:
    """CuPy-like objects should be converted via ``get`` method."""
    source = _FakeCuPyArray(np.array([4, 5, 6]))
    result = to_numpy(source)
    np.testing.assert_array_equal(result, np.array([4, 5, 6]))


def test_to_numpy_uses_array_protocol_fallback() -> None:
    """Objects implementing array protocol should be converted with ``np.asarray``."""
    result = to_numpy([7, 8, 9])
    np.testing.assert_array_equal(result, np.array([7, 8, 9]))
