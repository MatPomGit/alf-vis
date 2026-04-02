# Global map and coordinate system
from __future__ import annotations

import numpy as np


class WorldMap:
    def __init__(self):
        self.T = np.eye(4, dtype=float)
        self.points = []

    def update(self, R, t):
        T = np.eye(4, dtype=float)
        T[:3, :3] = R
        T[:3, 3] = np.asarray(t, dtype=float).flatten()
        T_inv = np.linalg.inv(T)
        self.T = 0.9 * self.T + 0.1 * T_inv

    def to_world(self, p):
        p_h = np.append(np.asarray(p, dtype=float), 1.0)
        return (self.T @ p_h)[:3]

    def add(self, p):
        p = np.asarray(p, dtype=float)
        if np.any(~np.isfinite(p)):
            return
        self.points.append(p)
        if len(self.points) > 5000:
            self.points = self.points[-5000:]
