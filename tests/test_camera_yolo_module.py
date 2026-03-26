"""Tests for src/yolo/camera_yolo.py utility module."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np


MODULE_PATH = Path(__file__).resolve().parents[1] / "src" / "yolo" / "camera_yolo.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("camera_yolo", MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_module_can_be_imported() -> None:
    module = _load_module()
    assert hasattr(module, "resize_bilinear_nchw")


def test_resize_bilinear_nchw_returns_expected_shape() -> None:
    module = _load_module()
    data = np.arange(2 * 3 * 4 * 5, dtype=np.float32).reshape(2, 3, 4, 5)

    resized = module.resize_bilinear_nchw(data, out_height=2, out_width=3)

    assert resized.shape == (2, 3, 2, 3)
    assert resized.dtype == np.float32
