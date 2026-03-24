"""Tests for image_analysis.slam module."""

from __future__ import annotations

import numpy as np
import pytest

from image_analysis.slam import (
    SUPPORTED_BACKENDS,
    SlamConfig,
    SlamFrame,
    SlamKeyframe,
    SlamMap,
    SlamSession,
)


class TestSlamConfig:
    def test_default_backend(self) -> None:
        cfg = SlamConfig()
        assert cfg.backend == "open3d"

    def test_viewer_disabled_by_default(self) -> None:
        cfg = SlamConfig()
        assert cfg.enable_viewer is False


class TestSlamFrame:
    def test_can_be_created(self) -> None:
        rgb = np.zeros((100, 100, 3), dtype=np.uint8)
        depth = np.zeros((100, 100), dtype=np.float32)
        frame = SlamFrame(rgb=rgb, depth=depth, timestamp_s=1.23)
        assert frame.timestamp_s == pytest.approx(1.23)


class TestSlamKeyframe:
    def test_default_timestamp(self) -> None:
        pose = np.eye(4, dtype=np.float64)
        kf = SlamKeyframe(frame_id=0, pose_world=pose)
        assert kf.timestamp_s == pytest.approx(0.0)


class TestSlamMap:
    def test_empty_by_default(self) -> None:
        m = SlamMap()
        assert len(m.keyframes) == 0
        assert m.map_points.shape == (0, 3)
        assert not m.is_lost

    def test_trajectory_starts_empty(self) -> None:
        m = SlamMap()
        assert m.trajectory == []


class TestSlamSession:
    def test_raises_for_unsupported_backend(self) -> None:
        with pytest.raises(ValueError, match="Unsupported SLAM backend"):
            SlamSession(SlamConfig(backend="unknown_backend"))

    def test_all_supported_backends_accepted(self) -> None:
        for backend in SUPPORTED_BACKENDS:
            session = SlamSession(SlamConfig(backend=backend))
            assert session is not None

    def test_process_frame_returns_identity_for_stub(self) -> None:
        session = SlamSession(SlamConfig(backend="open3d"))
        session.start()
        rgb = np.zeros((100, 100, 3), dtype=np.uint8)
        depth = np.zeros((100, 100), dtype=np.float32)
        frame = SlamFrame(rgb=rgb, depth=depth)
        pose = session.process_frame(frame)
        np.testing.assert_array_equal(pose, np.eye(4))
        session.stop()

    def test_trajectory_grows_with_frames(self) -> None:
        session = SlamSession(SlamConfig(backend="open3d"))
        session.start()
        rgb = np.zeros((50, 50, 3), dtype=np.uint8)
        depth = np.zeros((50, 50), dtype=np.float32)
        for _ in range(3):
            session.process_frame(SlamFrame(rgb=rgb, depth=depth))
        assert len(session.get_map().trajectory) == 3
        session.stop()

    def test_context_manager(self) -> None:
        with SlamSession(SlamConfig(backend="rtabmap")) as slam:
            assert slam is not None
