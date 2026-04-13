"""PyWebIO web interface for quick image-analysis demos."""

from __future__ import annotations

import base64
import io
from typing import Any

import cv2
import numpy as np
from PIL import Image

from image_analysis.acquisition_metrics import assess_frame
from image_analysis.preprocessing import normalize_image, resize_image

MAX_DISPLAY_EDGE = 720


def decode_uploaded_image(payload: dict[str, Any]) -> np.ndarray:
    """Decode uploaded file payload into a BGR image.

    Args:
        payload: Dictionary returned by ``pywebio.input.file_upload``.

    Returns:
        BGR ``uint8`` image with shape ``(H, W, 3)``.

    Raises:
        ValueError: If payload is invalid or image cannot be decoded.
    """
    content = payload.get("content")
    if not isinstance(content, (bytes, bytearray)):
        raise ValueError("Uploaded payload does not contain binary content.")

    try:
        with Image.open(io.BytesIO(content)) as pil_image:
            rgb = pil_image.convert("RGB")
            image_rgb = np.array(rgb, dtype=np.uint8)
    except OSError as exc:
        raise ValueError("Unable to decode uploaded image file.") from exc

    if image_rgb.ndim != 3 or image_rgb.shape[2] != 3:
        raise ValueError("Unable to decode uploaded image file.")
    return image_rgb[:, :, ::-1].copy()


def encode_png_bytes(image: np.ndarray) -> bytes:
    """Encode BGR image to PNG bytes for browser display."""
    ok, encoded = cv2.imencode(".png", image)
    if not ok:
        raise ValueError("Failed to encode preview image to PNG.")
    return encoded.tobytes()


def prepare_preview_image(image: np.ndarray) -> np.ndarray:
    """Prepare resized preview image preserving aspect ratio."""
    height, width = image.shape[:2]
    longest_edge = max(height, width)
    if longest_edge <= MAX_DISPLAY_EDGE:
        return image

    scale = MAX_DISPLAY_EDGE / float(longest_edge)
    target_width = int(width * scale)
    target_height = int(height * scale)
    return resize_image(image, target_width, target_height)


def build_quality_rows(image: np.ndarray) -> list[list[str]]:
    """Build table rows with quality metrics for UI rendering."""
    metrics = assess_frame(image)
    normalised = normalize_image(image)

    return [
        ["Resolution", f"{image.shape[1]}x{image.shape[0]}"],
        ["Brightness", f"{metrics.brightness:.3f}"],
        ["Contrast", f"{metrics.contrast:.3f}"],
        ["Sharpness", f"{metrics.blur_score:.3f}"],
        ["Noise", f"{metrics.noise_std:.3f}"],
        ["Normalized range", f"{normalised.min():.2f} - {normalised.max():.2f}"],
    ]


def _render_single_analysis() -> None:
    """Render one image-analysis cycle in the PyWebIO session."""
    from pywebio.input import file_upload
    from pywebio.output import put_error, put_html, put_markdown, put_table

    put_markdown("## Analiza obrazu (PyWebIO)")
    # Interfejs jest celowo prosty, aby łatwo działał lokalnie oraz w kontenerze.
    upload = file_upload("Wgraj obraz (PNG/JPG)", accept=".png,.jpg,.jpeg", required=True)

    try:
        image = decode_uploaded_image(upload)
        preview = prepare_preview_image(image)
        table_rows = build_quality_rows(image)
        png_bytes = encode_png_bytes(preview)
    except ValueError as exc:
        put_error(f"Błąd danych wejściowych: {exc}")
        return

    img_b64 = base64.b64encode(png_bytes).decode("ascii")
    put_html(
        f'<img alt="preview" style="max-width: 100%; border: 1px solid #ccc;" '
        f'src="data:image/png;base64,{img_b64}">'
    )
    put_table([["Metric", "Value"], *table_rows])


def run_pywebio_app() -> None:
    """Start PyWebIO web application for image upload and quality inspection."""
    try:
        from pywebio import start_server
    except ImportError as exc:
        raise ImportError(
            "PyWebIO interface requires 'pywebio'. Install with: pip install -e '.[web]'"
        ) from exc

    # Celowo wybieramy tryb debug=False, aby ograniczyć ryzyko ujawniania szczegółów środowiska.
    start_server(_render_single_analysis, port=8080, debug=False)
