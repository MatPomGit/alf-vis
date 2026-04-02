"""Utilities for YOLO camera preprocessing.

This module previously contained a pasted C++ OpenCV layer implementation, which made the
Python file invalid and caused syntax errors during static checks/import.
"""

from __future__ import annotations

import numpy as np


def resize_bilinear_nchw(
    tensor: np.ndarray,
    out_height: int,
    out_width: int,
) -> np.ndarray:
    """Resize an NCHW float tensor with bilinear interpolation.

    Args:
        tensor: Input array with shape ``(N, C, H, W)``.
        out_height: Target output height.
        out_width: Target output width.

    Returns:
        Resized tensor with shape ``(N, C, out_height, out_width)``.

    Raises:
        ValueError: If input shape is invalid or requested size is non-positive.
    """
    if tensor.ndim != 4:
        raise ValueError(f"Expected tensor with 4 dimensions (N,C,H,W), got {tensor.shape}.")
    if out_height <= 0 or out_width <= 0:
        raise ValueError("Output height and width must be positive integers.")

    batch, channels, in_height, in_width = tensor.shape
    if in_height == out_height and in_width == out_width:
        return tensor.copy()

    y_coords = np.linspace(0, in_height - 1, out_height, dtype=np.float32)
    x_coords = np.linspace(0, in_width - 1, out_width, dtype=np.float32)

    y0 = np.floor(y_coords).astype(np.int32)
    x0 = np.floor(x_coords).astype(np.int32)
    y1 = np.clip(y0 + 1, 0, in_height - 1)
    x1 = np.clip(x0 + 1, 0, in_width - 1)

    wy = (y_coords - y0).astype(np.float32)
    wx = (x_coords - x0).astype(np.float32)

    output = np.empty((batch, channels, out_height, out_width), dtype=tensor.dtype)

    for yi in range(out_height):
        top = tensor[:, :, y0[yi], :]
        bottom = tensor[:, :, y1[yi], :]

        top_interp = top[:, :, x0] * (1.0 - wx) + top[:, :, x1] * wx
        bottom_interp = bottom[:, :, x0] * (1.0 - wx) + bottom[:, :, x1] * wx
        output[:, :, yi, :] = top_interp * (1.0 - wy[yi]) + bottom_interp * wy[yi]

    return output


__all__ = ["resize_bilinear_nchw"]
