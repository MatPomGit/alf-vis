from __future__ import annotations
from typing import Dict, List, Tuple
import numpy as np
from common.models import DetectedObject, TrackedObject
class SimpleKalmanTrackerService:
    def __init__(self) -> None:
        self._next_object_id = 1; self._states: Dict[int, np.ndarray] = {}; self._covariances: Dict[int, np.ndarray] = {}
        self.F = np.array([[1,0,1,0],[0,1,0,1],[0,0,1,0],[0,0,0,1]], dtype=float)
        self.H = np.array([[1,0,0,0],[0,1,0,0]], dtype=float)
        self.Q = np.eye(4) * 1.0; self.R = np.eye(2) * 5.0; self.P0 = np.eye(4) * 10.0
    def _create_track(self, det: DetectedObject) -> TrackedObject:
        object_id = self._next_object_id; self._next_object_id += 1
        state = np.array([det.centroid_xy[0], det.centroid_xy[1], 0.0, 0.0], dtype=float)
        self._states[object_id] = state; self._covariances[object_id] = self.P0.copy()
        return TrackedObject(object_id=object_id, label=det.label, class_id=det.class_id, confidence=det.confidence, bbox_xyxy=det.bbox_xyxy, centroid_xy=det.centroid_xy, velocity_xy=(0.0,0.0), kalman_state=state.tolist())
    def _predict(self, object_id: int) -> None:
        x=self._states[object_id]; P=self._covariances[object_id]; self._states[object_id]=self.F@x; self._covariances[object_id]=self.F@P@self.F.T+self.Q
    def _update(self, object_id: int, measurement_xy: Tuple[float,float]) -> None:
        z = np.array([[measurement_xy[0]],[measurement_xy[1]]], dtype=float); x=self._states[object_id].reshape(4,1); P=self._covariances[object_id]
        y = z - self.H @ x; S = self.H @ P @ self.H.T + self.R; K = P @ self.H.T @ np.linalg.inv(S); x = x + K @ y; P = (np.eye(4) - K @ self.H) @ P
        self._states[object_id]=x.flatten(); self._covariances[object_id]=P
    def update_tracks(self, detections: List[DetectedObject], previous_tracks: List[TrackedObject], match_distance_px: float=60.0) -> List[TrackedObject]:
        for tr in previous_tracks:
            if tr.object_id in self._states: self._predict(tr.object_id)
        updated_tracks=[]; used_track_ids=set()
        for det in detections:
            best_track_id=None; best_dist=float('inf')
            for tr in previous_tracks:
                if tr.object_id not in self._states or tr.object_id in used_track_ids or tr.label != det.label: continue
                pred = self._states[tr.object_id]; dx = det.centroid_xy[0]-pred[0]; dy = det.centroid_xy[1]-pred[1]; dist=float((dx*dx+dy*dy)**0.5)
                if dist < best_dist and dist < match_distance_px: best_dist=dist; best_track_id=tr.object_id
            if best_track_id is None: updated_tracks.append(self._create_track(det)); continue
            self._update(best_track_id, det.centroid_xy); state=self._states[best_track_id]; used_track_ids.add(best_track_id)
            updated_tracks.append(TrackedObject(object_id=best_track_id, label=det.label, class_id=det.class_id, confidence=det.confidence, bbox_xyxy=det.bbox_xyxy, centroid_xy=(float(state[0]), float(state[1])), velocity_xy=(float(state[2]), float(state[3])), kalman_state=state.tolist()))
        return updated_tracks
