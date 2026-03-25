
# Global map and coordinate system
import numpy as np

class WorldMap:
    def __init__(self):
        self.T = None
        self.points = []

    def update(self,R,t):
        T = np.eye(4)
        T[:3,:3]=R
        T[:3,3]=t.flatten()
        if self.T is None:
            self.T = np.linalg.inv(T)
        else:
            self.T = 0.9*self.T + 0.1*np.linalg.inv(T)

    def to_world(self,p):
        if self.T is None: return None
        return (self.T @ np.append(p,1))[:3]

    def add(self,p):
        self.points.append(p)
        if len(self.points)>5000:
            self.points=self.points[-5000:]
