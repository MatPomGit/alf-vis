"""Tests for image_analysis.map_visualizer module."""

from __future__ import annotations

import numpy as np
import pytest

from image_analysis.map_visualizer import (
    SUPPORTED_BACKENDS,
    MapVisualizer,
    MapVisualizerConfig,
    VisualizerSnapshot,
    create_trajectory_line_set,
)
from image_analysis.point_cloud import PointCloud
from image_analysis.slam import SlamMap


class TestMapVisualizerConfig:
    def test_default_backend(self) -> None:
        cfg = MapVisualizerConfig()
        assert cfg.backend == "open3d"

    def test_all_defaults_are_sane(self) -> None:
        cfg = MapVisualizerConfig()
        assert cfg.point_size > 0
        assert 0.0 <= cfg.background_color[0] <= 1.0
        assert cfg.update_interval_ms > 0


class TestMapVisualizer:
    def test_raises_for_unsupported_backend(self) -> None:
        with pytest.raises(ValueError, match="Unsupported backend"):
            MapVisualizer(MapVisualizerConfig(backend="unknown"))

    def test_all_supported_backends_accepted(self) -> None:
        for backend in SUPPORTED_BACKENDS:
            viz = MapVisualizer(MapVisualizerConfig(backend=backend))
            assert viz is not None

    def test_start_and_stop_do_not_raise(self) -> None:
        viz = MapVisualizer(MapVisualizerConfig(backend="open3d"))
        viz.start()
        viz.stop()

    def test_update_with_none_does_not_raise(self) -> None:
        viz = MapVisualizer(MapVisualizerConfig(backend="open3d"))
        viz.start()
        viz.update()  # both arguments None
        viz.stop()

    def test_update_with_cloud(self) -> None:
        viz = MapVisualizer(MapVisualizerConfig(backend="open3d"))
        viz.start()
        pts = np.zeros((5, 3), dtype=np.float64)
        col = np.zeros((5, 3), dtype=np.float32)
        cloud = PointCloud(points=pts, colors=col)
        viz.update(cloud=cloud)
        viz.stop()

    def test_update_with_slam_map(self) -> None:
        viz = MapVisualizer(MapVisualizerConfig(backend="open3d"))
        viz.start()
        slam_map = SlamMap()
        viz.update(slam_map=slam_map)
        viz.stop()


class TestCreateTrajectoryLineSet:
    def test_empty_trajectory_returns_empty(self) -> None:
        pts, lines = create_trajectory_line_set([])
        assert len(pts) == 0

    def test_single_pose_returns_empty(self) -> None:
        pts, lines = create_trajectory_line_set([np.eye(4)])
        assert len(lines) == 0

    def test_two_poses_give_one_line(self) -> None:
        T0 = np.eye(4, dtype=np.float64)
        T1 = np.eye(4, dtype=np.float64)
        T1[:3, 3] = [1.0, 0.0, 0.0]
        pts, lines = create_trajectory_line_set([T0, T1])
        assert pts.shape == (2, 3)
        assert lines.shape == (1, 2)

    def test_positions_extracted_correctly(self) -> None:
        T0 = np.eye(4, dtype=np.float64)
        T1 = np.eye(4, dtype=np.float64)
        T1[:3, 3] = [3.0, 4.0, 5.0]
        pts, _ = create_trajectory_line_set([T0, T1])
        np.testing.assert_array_equal(pts[0], [0.0, 0.0, 0.0])
        np.testing.assert_array_equal(pts[1], [3.0, 4.0, 5.0])


class TestVisualizerSnapshot:
    def test_default_values(self) -> None:
        snap = VisualizerSnapshot()
        assert snap.timestamp_s == pytest.approx(0.0)
        assert snap.num_points == 0
        assert snap.num_keyframes == 0

    def test_can_set_all_fields(self) -> None:
        snap = VisualizerSnapshot(
            timestamp_s=1.5,
            num_points=1000,
            num_keyframes=10,
            camera_position=(1.0, 2.0, 3.0),
        )
        assert snap.num_points == 1000
        assert snap.camera_position == (1.0, 2.0, 3.0)
