import numpy as np

class WorldMap:
    def __init__(self):
        self.T_world_cam = None
        self.map_points = []

    def update_from_tag(self, R, t):
        T = np.eye(4)
        T[:3,:3] = R
        T[:3,3] = t.flatten()

        # pierwsza obserwacja → definiuje świat
        if self.T_world_cam is None:
            self.T_world_cam = np.linalg.inv(T)
        else:
            # filtracja / wygładzanie transformacji
            self.T_world_cam = 0.9*self.T_world_cam + 0.1*np.linalg.inv(T)

    def to_world(self, point_cam):
        p = np.append(point_cam, 1)
        pw = self.T_world_cam @ p
        return pw[:3]

    def add_point(self, p):
        self.map_points.append(p)