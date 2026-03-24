"""Tests for image_analysis.camera module."""

from __future__ import annotations

import pytest

from image_analysis.camera import (
    CameraConfig,
    RgbdFrame,
    UnitreeCamera,
)


class TestCameraConfig:
    def test_default_values(self) -> None:
        cfg = CameraConfig()
        assert cfg.source == 0
        assert cfg.frame_width == 1280
        assert cfg.frame_height == 720
        assert cfg.fps == 30
        assert cfg.enable_depth is False
        assert cfg.calibration_file is None

    def test_custom_values(self) -> None:
        cfg = CameraConfig(source="rtsp://192.168.1.1", frame_width=640, frame_height=480)
        assert cfg.source == "rtsp://192.168.1.1"
        assert cfg.frame_width == 640


class TestRgbdFrame:
    def test_can_be_created(self) -> None:
        import numpy as np

        rgb = np.zeros((100, 100, 3), dtype=np.uint8)
        depth = np.zeros((100, 100), dtype=np.float32)
        frame = RgbdFrame(rgb=rgb, depth=depth, timestamp_ns=12345)
        assert frame.timestamp_ns == 12345
        assert frame.rgb.shape == (100, 100, 3)
        assert frame.depth.shape == (100, 100)


class TestUnitreeCamera:
    def test_is_open_false_before_open(self) -> None:
        cam = UnitreeCamera(CameraConfig(source=0))
        assert cam.is_open is False

    def test_raises_runtime_error_on_invalid_source(self) -> None:
        # Use a non-existent device index that will not open.
        cam = UnitreeCamera(CameraConfig(source=99))
        with pytest.raises(RuntimeError, match="Failed to open camera"):
            cam.open()

    def test_close_when_not_open_does_not_raise(self) -> None:
        cam = UnitreeCamera(CameraConfig(source=0))
        cam.close()  # must not raise

    def test_read_rgb_raises_when_not_open(self) -> None:
        cam = UnitreeCamera(CameraConfig(source=0))
        with pytest.raises(RuntimeError):
            cam.read_rgb()
