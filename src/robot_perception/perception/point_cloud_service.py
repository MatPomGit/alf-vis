from __future__ import annotations
from pathlib import Path
from typing import Optional
import numpy as np
import open3d as o3d
from common.models import CameraCalibration, PointCloudData, Pose3D
from common.utils import ensure_dir
from perception.console import info, warn
class PointCloudService:
    def __init__(self, output_dir: str) -> None:
        self.output_dir = ensure_dir(Path(output_dir) / 'pointclouds'); info('Zainicjalizowano usługę chmury punktów.')
    def build_from_rgbd(self, color_bgr: np.ndarray, depth_mm: np.ndarray, calibration: CameraCalibration, depth_scale: float=1000.0, depth_trunc_m: float=5.0) -> PointCloudData:
        color_rgb = color_bgr[:,:,::-1].copy(); color_o3d = o3d.geometry.Image(color_rgb); depth_o3d = o3d.geometry.Image(depth_mm.astype(np.uint16))
        rgbd = o3d.geometry.RGBDImage.create_from_color_and_depth(color=color_o3d, depth=depth_o3d, depth_scale=depth_scale, depth_trunc=depth_trunc_m, convert_rgb_to_intensity=False)
        K = np.array(calibration.camera_matrix, dtype=float)
        intrinsic = o3d.camera.PinholeCameraIntrinsic(width=calibration.image_width, height=calibration.image_height, fx=float(K[0,0]), fy=float(K[1,1]), cx=float(K[0,2]), cy=float(K[1,2]))
        pc = o3d.geometry.PointCloud.create_from_rgbd_image(rgbd, intrinsic); points=np.asarray(pc.points); colors=np.asarray(pc.colors)
        return PointCloudData(coordinate_frame='camera_link', points=[tuple(map(float,p)) for p in points], colors=[tuple(map(float,c)) for c in colors])
    def build_sparse_from_rgb_only(self, color_bgr: np.ndarray, calibration: CameraCalibration) -> PointCloudData:
        gray=np.mean(color_bgr, axis=2); h,w=gray.shape; step=max(4,min(h,w)//80)
        K=np.array(calibration.camera_matrix, dtype=float); fx,fy=float(K[0,0]), float(K[1,1]); cx,cy=float(K[0,2]), float(K[1,2])
        points=[]; colors=[]
        for v in range(0,h,step):
            for u in range(0,w,step):
                z=1.0 + float(gray[v,u])/255.0; x=(u-cx)*z/fx; y=(v-cy)*z/fy; points.append((float(x),float(y),float(z))); b,g,r=color_bgr[v,u]; colors.append((float(r)/255.0,float(g)/255.0,float(b)/255.0))
        return PointCloudData(coordinate_frame='camera_link', points=points, colors=colors)
    def validate_transform(self, camera_pose_in_map: Optional[Pose3D], translation_limit_m: float, rotation_limit_rad: float) -> bool:
        if camera_pose_in_map is None: warn('Brak pozy kamery w mapie.'); return False
        translation_norm = float(np.linalg.norm([camera_pose_in_map.x, camera_pose_in_map.y, camera_pose_in_map.z])); rotation_max=max(abs(camera_pose_in_map.roll), abs(camera_pose_in_map.pitch), abs(camera_pose_in_map.yaw))
        return translation_norm <= translation_limit_m and rotation_max <= rotation_limit_rad
    def transform_to_map(self, cloud: PointCloudData, camera_pose_in_map: Optional[Pose3D]) -> PointCloudData:
        if camera_pose_in_map is None or not cloud.points: warn('Pomijam transformację chmury.'); return cloud
        pc=self.to_open3d(cloud); cx,cy,cz=camera_pose_in_map.x, camera_pose_in_map.y, camera_pose_in_map.z; roll,pitch,yaw=camera_pose_in_map.roll, camera_pose_in_map.pitch, camera_pose_in_map.yaw
        cr,sr=np.cos(roll),np.sin(roll); cp,sp=np.cos(pitch),np.sin(pitch); cyaw,syaw=np.cos(yaw),np.sin(yaw)
        rx=np.array([[1,0,0],[0,cr,-sr],[0,sr,cr]], dtype=float); ry=np.array([[cp,0,sp],[0,1,0],[-sp,0,cp]], dtype=float); rz=np.array([[cyaw,-syaw,0],[syaw,cyaw,0],[0,0,1]], dtype=float)
        rotation=rz@ry@rx; T=np.eye(4, dtype=float); T[:3,:3]=rotation; T[:3,3]=np.array([cx,cy,cz], dtype=float); pc.transform(T)
        points=np.asarray(pc.points); colors=np.asarray(pc.colors) if pc.has_colors() else np.empty((0,3))
        return PointCloudData(coordinate_frame='map', points=[tuple(map(float,p)) for p in points], colors=[tuple(map(float,c)) for c in colors] if len(colors)==len(points) else [])
    def to_open3d(self, cloud: PointCloudData) -> o3d.geometry.PointCloud:
        pc=o3d.geometry.PointCloud();
        if cloud.points: pc.points=o3d.utility.Vector3dVector(np.array(cloud.points, dtype=float))
        if cloud.colors and len(cloud.colors)==len(cloud.points): pc.colors=o3d.utility.Vector3dVector(np.array(cloud.colors, dtype=float))
        return pc
    def save_ply(self, cloud: PointCloudData, frame_id: int) -> str:
        pc=self.to_open3d(cloud); file_path=self.output_dir / f'pointcloud_frame_{frame_id:06d}.ply'; ok=o3d.io.write_point_cloud(str(file_path), pc, write_ascii=False, compressed=False)
        if not ok: raise RuntimeError('Nie udało się zapisać chmury punktów do PLY.')
        return str(file_path)
