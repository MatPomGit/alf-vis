
import numpy as np
from kalman3d import Kalman3D

def iou(b1, b2):
    x1 = max(b1[0], b2[0])
    y1 = max(b1[1], b2[1])
    x2 = min(b1[2], b2[2])
    y2 = min(b1[3], b2[3])
    inter = max(0, x2-x1) * max(0, y2-y1)
    a1 = (b1[2]-b1[0])*(b1[3]-b1[1])
    a2 = (b2[2]-b2[0])*(b2[3]-b2[1])
    union = a1 + a2 - inter
    return inter/union if union>0 else 0

def linear_assignment(tracks, detections, iou_thr):
    matches, ut, ud = [], list(range(len(tracks))), list(range(len(detections)))
    for ti, t in enumerate(tracks):
        best, best_j = 0, -1
        for dj, d in enumerate(detections):
            if t.cls != d["cls"]:
                continue
            s = iou(t.bbox, d["bbox"])
            if s > best:
                best, best_j = s, dj
        if best >= iou_thr:
            matches.append((ti, best_j))
            if ti in ut: ut.remove(ti)
            if best_j in ud: ud.remove(best_j)
    return matches, ut, ud

def compute_R(conf):
    base = 0.02
    scale = (1.0 - conf)**2
    return np.eye(3) * (base + 0.2 * scale)

class Track:
    def __init__(self, det, tid):
        self.bbox = det["bbox"]
        self.cls = det["cls"]
        self.id = tid
        self.lost = 0
        self.kf = Kalman3D()
        self.position_3d = None

    def update(self, det):
        self.bbox = det["bbox"]
        self.cls = det["cls"]
        self.lost = 0

class ByteTracker:
    def __init__(self):
        self.tracks = []
        self.next_id = 0
        self.high = 0.5
        self.low = 0.1
        self.gate = 9.0

    def update(self, detections):
        high = [d for d in detections if d["score"] >= self.high]
        low = [d for d in detections if self.low <= d["score"] < self.high]

        matches, ut, ud = linear_assignment(self.tracks, high, 0.3)

        for ti, di in matches:
            self.tracks[ti].update(high[di])

        if ut and low:
            sub = [self.tracks[i] for i in ut]
            m2, ut2, _ = linear_assignment(sub, low, 0.5)
            for ti, di in m2:
                real = ut[ti]
                self.tracks[real].update(low[di])
            ut = [ut[i] for i in ut2]

        for t in self.tracks:
            if t.position_3d is not None:
                d2 = t.kf.gating_distance(t.position_3d)
                if d2 < self.gate:
                    t.kf.update(t.position_3d)
                else:
                    t.kf.predict()
            else:
                t.kf.predict()

        for di in ud:
            self.tracks.append(Track(high[di], self.next_id))
            self.next_id += 1

        for i in ut:
            self.tracks[i].lost += 1

        self.tracks = [t for t in self.tracks if t.lost < 30]

        return self.tracks
