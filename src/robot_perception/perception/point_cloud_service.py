from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Tuple

import numpy as np
import open3d as o3d

from common.models import PointCloudData, SlamStatus
from common.utils import ensure_dir


class PointCloudService:
    """Usługa budowy i zapisu chmury punktów przy użyciu Open3D."""

    def __init__(self, output_dir: str) -> None:
        self.output_dir = ensure_dir(Path(output_dir) / "pointclouds")

    def build_from_slam_status(self, slam_status: SlamStatus) -> PointCloudData:
        """Buduje reprezentację chmury punktów na podstawie stanu SLAM.

        Wersja bazowa tworzy syntetyczne punkty wokół pozy robota. W systemie docelowym
        źródłem danych powinny być rzeczywiste punkty mapy RTAB-Map.
        """
        pose = slam_status.pose or slam_status.pose or None
        if pose is None:
            return PointCloudData(coordinate_frame="map", points=[], colors=[])

        point_count = slam_status.map_point_count
        if point_count <= 0:
            return PointCloudData(coordinate_frame="map", points=[], colors=[])

        points: List[Tuple[float, float, float]] = []
        colors: List[Tuple[float, float, float]] = []

        for i in range(point_count):
            px = pose.x + (i % 20) * 0.01
            py = pose.y + ((i // 20) % 20) * 0.01
            pz = (i % 5) * 0.005
            points.append((float(px), float(py), float(pz)))
            colors.append((0.3, 0.7, 1.0))

        # TODO: podmienić syntetyczne punkty na realny eksport map points z RTAB-Map.
        return PointCloudData(coordinate_frame="map", points=points, colors=colors)

    def to_open3d(self, cloud: PointCloudData) -> o3d.geometry.PointCloud:
        """Konwertuje chmurę punktów do formatu Open3D."""
        pc = o3d.geometry.PointCloud()
        if cloud.points:
            pc.points = o3d.utility.Vector3dVector(np.array(cloud.points, dtype=float))
        if cloud.colors and len(cloud.colors) == len(cloud.points):
            pc.colors = o3d.utility.Vector3dVector(np.array(cloud.colors, dtype=float))
        return pc

    def save_ply(self, cloud: PointCloudData, frame_id: int) -> str:
        """Zapisuje chmurę punktów do pliku PLY."""
        pc = self.to_open3d(cloud)
        file_path = self.output_dir / f"pointcloud_frame_{frame_id:06d}.ply"

        ok = o3d.io.write_point_cloud(str(file_path), pc, write_ascii=False, compressed=False)
        if not ok:
            raise RuntimeError("Nie udało się zapisać chmury punktów do PLY.")

        return str(file_path)




""" old
from __future__ import annotations
import json
from pathlib import Path
from common.io_utils import ensure_dir
from common.protocol import read_stdin_json, write_stdout_json, ok_response


def main() -> None:
    payload = read_stdin_json()
    frame_id = payload.get("frame_id")
    point_cloud = payload.get("point_cloud", {})

    output_dir = ensure_dir(Path(__file__).resolve().parent.parent / "output" / "pointclouds")
    save_path = output_dir / f"pointcloud_frame_{frame_id}.json"

    save_path.write_text(json.dumps(point_cloud, ensure_ascii=False, indent=2), encoding="utf-8")
    # później zamienić format na PCD, PLY albo ROS sensor_msgs/PointCloud2.

    write_stdout_json(
        ok_response(
            point_cloud_save_path=str(save_path),
            saved=True,
        )
    )

if __name__ == "__main__":
    main() """