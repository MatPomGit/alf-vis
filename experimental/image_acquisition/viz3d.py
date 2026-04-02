import open3d as o3d
import numpy as np

class LiveMap:
    def __init__(self):
        self.vis = o3d.visualization.Visualizer()
        self.vis.create_window()
        self.pc = o3d.geometry.PointCloud()

    def update(self, map_points):
        if len(map_points) == 0:
            return

        pts = np.array(map_points)
        self.pc.points = o3d.utility.Vector3dVector(pts)

        self.vis.clear_geometries()
        self.vis.add_geometry(self.pc)
        self.vis.poll_events()
        self.vis.update_renderer()