"""Tests for PyWebIO interface helpers."""

from __future__ import annotations

import builtins

import numpy as np
import pytest

from image_analysis.pywebio_app import (
    MAX_DISPLAY_EDGE,
    build_quality_rows,
    decode_uploaded_image,
    encode_png_bytes,
    prepare_preview_image,
    run_pywebio_app,
)


def _make_image(height: int = 120, width: int = 160) -> np.ndarray:
    """Create synthetic BGR uint8 image for tests."""
    rng = np.random.default_rng(seed=123)
    return rng.integers(0, 255, size=(height, width, 3), dtype=np.uint8)


def test_decode_uploaded_image_raises_for_missing_content() -> None:
    """Decode should fail when payload has no binary buffer."""
    with pytest.raises(ValueError, match="binary content"):
        decode_uploaded_image({})


def test_decode_uploaded_image_decodes_valid_png() -> None:
    """Decode should return BGR uint8 image for valid encoded content."""
    source = _make_image()
    payload = {"content": encode_png_bytes(source)}

    decoded = decode_uploaded_image(payload)

    assert decoded.dtype == np.uint8
    assert decoded.shape == source.shape


def test_prepare_preview_image_keeps_small_images_unchanged() -> None:
    """Small images should not be resized."""
    image = _make_image(height=100, width=120)
    preview = prepare_preview_image(image)
    assert preview.shape == image.shape


def test_prepare_preview_image_resizes_large_images() -> None:
    """Large images should be downscaled to configured max edge."""
    image = _make_image(height=2000, width=1200)
    preview = prepare_preview_image(image)

    assert max(preview.shape[:2]) == MAX_DISPLAY_EDGE


def test_build_quality_rows_returns_expected_labels() -> None:
    """Quality table should expose all expected metrics."""
    image = _make_image()
    rows = build_quality_rows(image)
    labels = [row[0] for row in rows]

    assert labels == [
        "Resolution",
        "Brightness",
        "Contrast",
        "Sharpness",
        "Noise",
        "Normalized range",
    ]


def test_run_pywebio_app_raises_without_dependency(monkeypatch) -> None:
    """Missing PyWebIO dependency should raise clear installation hint."""
    real_import = builtins.__import__

    def _fake_import(name: str, *args: object, **kwargs: object) -> object:
        if name == "pywebio":
            raise ImportError("missing pywebio")
        return real_import(name, *args, **kwargs)

    # Symulujemy brak modułu pywebio bez modyfikacji środowiska systemowego.
    monkeypatch.setattr(builtins, "__import__", _fake_import)
    with pytest.raises(ImportError, match="requires 'pywebio'"):
        run_pywebio_app()
