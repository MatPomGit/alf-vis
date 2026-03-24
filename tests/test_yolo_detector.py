"""Tests for image_analysis.yolo_detector module."""

from __future__ import annotations

import numpy as np
import pytest

from image_analysis.yolo_detector import YoloConfig, YoloDetector, _parse_ultralytics_results


class TestYoloConfig:
    def test_default_values(self) -> None:
        cfg = YoloConfig()
        assert cfg.confidence == pytest.approx(0.45)
        assert cfg.device == "cpu"
        assert cfg.image_size == 640

    def test_custom_weights(self) -> None:
        cfg = YoloConfig(weights="yolov8s.pt")
        assert str(cfg.weights) == "yolov8s.pt"


class TestYoloDetector:
    def test_is_not_loaded_by_default(self) -> None:
        detector = YoloDetector()
        assert detector.is_loaded is False

    def test_raises_import_error_when_ultralytics_missing(self) -> None:
        """load() should raise ImportError when ultralytics is not installed."""
        detector = YoloDetector(YoloConfig(weights="yolov8n.pt"))
        # If ultralytics IS installed in the test env, skip the check.
        try:
            import ultralytics  # type: ignore[import-untyped]  # noqa: F401

            pytest.skip("ultralytics is installed; skipping ImportError test.")
        except ImportError:
            with pytest.raises(ImportError, match="ultralytics"):
                detector.load()

    def test_detect_raises_type_error_for_non_ndarray(self) -> None:
        detector = YoloDetector()
        with pytest.raises(TypeError):
            detector.detect("not an image")  # type: ignore[arg-type]

    def test_detect_raises_runtime_error_when_not_loaded(self) -> None:
        detector = YoloDetector()
        image = np.zeros((100, 100, 3), dtype=np.uint8)
        with pytest.raises(RuntimeError, match="not loaded"):
            detector.detect(image)


class TestParseUltralyticsResults:
    def test_empty_results_returns_empty_list(self) -> None:
        result = _parse_ultralytics_results([])
        assert result == []

    def test_result_without_boxes_returns_empty_list(self) -> None:
        class FakeResult:
            boxes = None
            names: dict = {}

        result = _parse_ultralytics_results([FakeResult()])
        assert result == []
