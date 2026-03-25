import os
import numpy as np


class WorldMap:
    """Simple global map storage.

    Until an external pose source (e.g. AprilTag / SLAM) is connected, the
    world frame defaults to the current camera frame so the map still works.
    """

    def __init__(self, max_points: int = 5000):
        self.T = np.eye(4, dtype=float)
        self.points = []
        self.max_points = max_points

    def update(self, R, t):
        """Update camera->world transform from rotation and translation."""
        R = np.asarray(R, dtype=float)
        t = np.asarray(t, dtype=float).reshape(3)
        if R.shape != (3, 3):
            raise ValueError("R must have shape (3, 3)")

        T_cam = np.eye(4, dtype=float)
        T_cam[:3, :3] = R
        T_cam[:3, 3] = t
        self.T = np.linalg.inv(T_cam)

    def to_world(self, p):
        p = np.asarray(p, dtype=float).reshape(3)
        return (self.T @ np.append(p, 1.0))[:3]

    def add(self, p):
        self.points.append(np.asarray(p, dtype=float).reshape(3))
        if len(self.points) > self.max_points:
            self.points = self.points[-self.max_points :]

    def save_ply(self, path: str):
        """Save accumulated points to an ASCII PLY file.

        This implementation intentionally avoids extra dependencies so it can
        be used in simple tests and headless environments.
        """
        if not self.points:
            raise ValueError("World map is empty")

        points = np.asarray(self.points, dtype=float).reshape(-1, 3)
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            f.write("ply\n")
            f.write("format ascii 1.0\n")
            f.write(f"element vertex {len(points)}\n")
            f.write("property float x\n")
            f.write("property float y\n")
            f.write("property float z\n")
            f.write("end_header\n")
            for x, y, z in points:
                f.write(f"{x:.6f} {y:.6f} {z:.6f}\n")
