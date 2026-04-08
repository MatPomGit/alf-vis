from __future__ import annotations
from pathlib import Path
from typing import Tuple
import numpy as np
import open3d as o3d
from common.models import CameraCalibration, PointCloudData
from common.utils import ensure_dir

class PointCloudService:
    """Usługa budowy i zapisu chmury punktów przy użyciu Open3D."""

    def __init__(self, output_dir: str) -> None:
        self.output_dir = ensure_dir(Path(output_dir) / "pointclouds")

    def build_from_rgbd(
        self,
        color_bgr: np.ndarray,
        depth_mm: np.ndarray,
        calibration: CameraCalibration,
        depth_scale: float = 1000.0,
        depth_trunc_m: float = 5.0,
    ) -> PointCloudData:
        """Buduje rzeczywistą chmurę punktów z obrazu RGB i mapy głębi."""
        color_rgb = color_bgr[:, :, ::-1].copy()

        color_o3d = o3d.geometry.Image(color_rgb)
        depth_o3d = o3d.geometry.Image(depth_mm.astype(np.uint16))

        rgbd = o3d.geometry.RGBDImage.create_from_color_and_depth(
            color=color_o3d,
            depth=depth_o3d,
            depth_scale=depth_scale,
            depth_trunc=depth_trunc_m,
            convert_rgb_to_intensity=False,
        )

        K = np.array(calibration.camera_matrix, dtype=float)
        intrinsic = o3d.camera.PinholeCameraIntrinsic(
            width=calibration.image_width,
            height=calibration.image_height,
            fx=float(K[0, 0]),
            fy=float(K[1, 1]),
            cx=float(K[0, 2]),
            cy=float(K[1, 2]),
        )

        pc = o3d.geometry.PointCloud.create_from_rgbd_image(rgbd, intrinsic)
        points = np.asarray(pc.points)
        colors = np.asarray(pc.colors)

        return PointCloudData(
            coordinate_frame="camera",
            points=[tuple(map(float, p)) for p in points],
            colors=[tuple(map(float, c)) for c in colors],
        )

    def to_open3d(self, cloud: PointCloudData) -> o3d.geometry.PointCloud:
        """Konwertuje model aplikacyjny do Open3D PointCloud."""
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

    # TODO: dodać transformację chmury z frame `camera` do `map` przez TF / RTAB-Map.