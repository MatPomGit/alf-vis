from __future__ import annotations

import json
import queue
import threading
import time
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple


# ============================================================
# ENUM STANÓW
# ============================================================

class PerceptionState(Enum):
    IDLE = auto()
    ACTIVE_VISION = auto()
    DETECT_VISUAL_MARKERS = auto()
    DETECT_HUMAN = auto()
    DETECT_OBSTACLE = auto()
    DETECT_NEW_OBJECTS = auto()
    TRACK_OBJECTS_KALMAN = auto()
    CHECK_PATH_DEVIATION = auto()
    UPDATE_SLAM = auto()
    PRINT_STATE = auto()
    PUBLISH_ROS2_STATE = auto()
    ERROR = auto()


# ============================================================
# STRUKTURY DANYCH
# ============================================================

@dataclass
class TrackedObject:
    object_id: int
    label: str
    bbox: Tuple[int, int, int, int]
    position: Tuple[float, float]
    velocity: Tuple[float, float] = (0.0, 0.0)
    confidence: float = 1.0


@dataclass
class PerceptionContext:
    frame_id: int = 0
    timestamp: float = 0.0
    image: Optional[Any] = None
    roi: Optional[Tuple[int, int, int, int]] = None

    visual_markers: List[Dict[str, Any]] = field(default_factory=list)
    human_detected: bool = False
    obstacle_detected: bool = False
    new_objects: List[Dict[str, Any]] = field(default_factory=list)
    tracked_objects: List[TrackedObject] = field(default_factory=list)

    path_deviation_detected: bool = False
    slam_pose: Optional[Dict[str, float]] = None
    slam_map_status: str = "UNKNOWN"

    system_ok: bool = True
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        return data


# ============================================================
# STUBY / INTERFEJSY ALGORYTMÓW
# W tych klasach podmieniasz implementacje na właściwe:
# OpenCV, YOLO, AprilTag/Aruco, Kalman, SLAM, itd.
# ============================================================

class ActiveVisionModule:
    def find_relevant_roi(self, image: Any) -> Tuple[int, int, int, int]:
        # TODO: rzeczywista implementacja active vision
        # np. saliency map, gaze policy, region proposal, task-guided ROI
        return (100, 100, 300, 300)


class VisualMarkerDetector:
    def detect(self, image: Any, roi: Optional[Tuple[int, int, int, int]]) -> List[Dict[str, Any]]:
        # TODO: detekcja markerów ArUco / AprilTag / QR
        return [
            {"id": 1, "type": "aruco", "pose": {"x": 1.2, "y": 0.4, "z": 0.0}}
        ]


class HumanDetector:
    def detect(self, image: Any) -> bool:
        # TODO: detekcja człowieka
        return False


class ObstacleDetector:
    def detect(self, image: Any) -> bool:
        # TODO: detekcja przeszkód do ominięcia
        return True


class NewObjectDetector:
    def detect(self, image: Any, tracked_objects: List[TrackedObject]) -> List[Dict[str, Any]]:
        # TODO: detekcja nowych obiektów
        return [
            {"label": "box", "bbox": (220, 180, 80, 60), "confidence": 0.92}
        ]


class KalmanTracker:
    def update(self, tracked_objects: List[TrackedObject], image: Any) -> List[TrackedObject]:
        # TODO: rzeczywisty update filtru Kalmana dla śledzonych obiektów
        updated = []
        for obj in tracked_objects:
            new_x = obj.position[0] + obj.velocity[0]
            new_y = obj.position[1] + obj.velocity[1]
            updated.append(
                TrackedObject(
                    object_id=obj.object_id,
                    label=obj.label,
                    bbox=obj.bbox,
                    position=(new_x, new_y),
                    velocity=obj.velocity,
                    confidence=obj.confidence,
                )
            )
        return updated


class PathDeviationChecker:
    def check(self, slam_pose: Optional[Dict[str, float]]) -> bool:
        # TODO: porównanie pozycji robota z trajektorią referencyjną
        if slam_pose is None:
            return False
        return abs(slam_pose.get("y", 0.0)) > 0.5


class SlamModule:
    def update(self, image: Any, visual_markers: List[Dict[str, Any]]) -> Tuple[Dict[str, float], str]:
        # TODO: aktualizacja SLAM
        pose = {"x": 2.4, "y": 0.1, "theta": 0.03}
        status = "UPDATED"
        return pose, status


# ============================================================
# PUBLIKATOR ROS2 W OSOBNYM WĄTKU
# To jest bezpieczny szkielet. W miejscu TODO podpinasz rclpy.
# ============================================================

class ROS2PublisherThread(threading.Thread):
    def __init__(self) -> None:
        super().__init__(daemon=True)
        self._queue: queue.Queue[Dict[str, Any]] = queue.Queue()
        self._stop_event = threading.Event()

        # TODO: zainicjalizować rclpy, node, publisher
        # np. publisher na topic /perception_state
        self.ros2_enabled = False

    def publish_async(self, state: Dict[str, Any]) -> None:
        self._queue.put(state)

    def run(self) -> None:
        while not self._stop_event.is_set():
            try:
                payload = self._queue.get(timeout=0.1)
            except queue.Empty:
                continue

            if self.ros2_enabled:
                # TODO: zamienić payload na wiadomość ROS2 i opublikować
                # np. std_msgs/String albo custom msg
                pass
            else:
                # tryb symulacyjny
                print("[ROS2 THREAD] Symulowana publikacja:", json.dumps(payload, ensure_ascii=False))

    def stop(self) -> None:
        self._stop_event.set()


# ============================================================
# GŁÓWNA MASZYNA STANÓW
# ============================================================

class RobotPerceptionStateMachine:
    def __init__(self) -> None:
        self.state = PerceptionState.IDLE
        self.context = PerceptionContext()

        self.active_vision = ActiveVisionModule()
        self.marker_detector = VisualMarkerDetector()
        self.human_detector = HumanDetector()
        self.obstacle_detector = ObstacleDetector()
        self.new_object_detector = NewObjectDetector()
        self.kalman_tracker = KalmanTracker()
        self.path_checker = PathDeviationChecker()
        self.slam = SlamModule()

        self.ros2_publisher = ROS2PublisherThread()
        self.ros2_publisher.start()

        self._next_object_id = 1

    def shutdown(self) -> None:
        self.ros2_publisher.stop()
        self.ros2_publisher.join(timeout=1.0)

    def set_input_image(self, image: Any, frame_id: int) -> None:
        self.context.image = image
        self.context.frame_id = frame_id
        self.context.timestamp = time.time()

    def transition_to(self, next_state: PerceptionState) -> None:
        self.state = next_state

    def run_once(self) -> None:
        try:
            if self.state == PerceptionState.IDLE:
                self.transition_to(PerceptionState.ACTIVE_VISION)

            elif self.state == PerceptionState.ACTIVE_VISION:
                self.context.roi = self.active_vision.find_relevant_roi(self.context.image)
                self.transition_to(PerceptionState.DETECT_VISUAL_MARKERS)

            elif self.state == PerceptionState.DETECT_VISUAL_MARKERS:
                self.context.visual_markers = self.marker_detector.detect(
                    self.context.image,
                    self.context.roi
                )
                self.transition_to(PerceptionState.DETECT_HUMAN)

            elif self.state == PerceptionState.DETECT_HUMAN:
                self.context.human_detected = self.human_detector.detect(self.context.image)
                self.transition_to(PerceptionState.DETECT_OBSTACLE)

            elif self.state == PerceptionState.DETECT_OBSTACLE:
                self.context.obstacle_detected = self.obstacle_detector.detect(self.context.image)
                self.transition_to(PerceptionState.DETECT_NEW_OBJECTS)

            elif self.state == PerceptionState.DETECT_NEW_OBJECTS:
                detected_new = self.new_object_detector.detect(
                    self.context.image,
                    self.context.tracked_objects
                )
                self.context.new_objects = detected_new

                for obj in detected_new:
                    tracked = TrackedObject(
                        object_id=self._next_object_id,
                        label=obj["label"],
                        bbox=obj["bbox"],
                        position=(float(obj["bbox"][0]), float(obj["bbox"][1])),
                        velocity=(0.0, 0.0),
                        confidence=obj.get("confidence", 1.0),
                    )
                    self.context.tracked_objects.append(tracked)
                    self._next_object_id += 1

                self.transition_to(PerceptionState.TRACK_OBJECTS_KALMAN)

            elif self.state == PerceptionState.TRACK_OBJECTS_KALMAN:
                self.context.tracked_objects = self.kalman_tracker.update(
                    self.context.tracked_objects,
                    self.context.image
                )
                self.transition_to(PerceptionState.CHECK_PATH_DEVIATION)

            elif self.state == PerceptionState.CHECK_PATH_DEVIATION:
                self.context.path_deviation_detected = self.path_checker.check(self.context.slam_pose)
                self.transition_to(PerceptionState.UPDATE_SLAM)

            elif self.state == PerceptionState.UPDATE_SLAM:
                pose, status = self.slam.update(self.context.image, self.context.visual_markers)
                self.context.slam_pose = pose
                self.context.slam_map_status = status
                self.transition_to(PerceptionState.PRINT_STATE)

            elif self.state == PerceptionState.PRINT_STATE:
                self.print_perception_state()
                self.transition_to(PerceptionState.PUBLISH_ROS2_STATE)

            elif self.state == PerceptionState.PUBLISH_ROS2_STATE:
                self.publish_perception_state()
                self.transition_to(PerceptionState.IDLE)

            elif self.state == PerceptionState.ERROR:
                self.context.system_ok = False
                self.print_perception_state()

            else:
                raise ValueError(f"Nieobsługiwany stan: {self.state}")

        except Exception as exc:
            self.context.system_ok = False
            self.context.error_message = str(exc)
            self.transition_to(PerceptionState.ERROR)

    def print_perception_state(self) -> None:
        state_snapshot = {
            "frame_id": self.context.frame_id,
            "timestamp": self.context.timestamp,
            "roi": self.context.roi,
            "visual_markers_count": len(self.context.visual_markers),
            "human_detected": self.context.human_detected,
            "obstacle_detected": self.context.obstacle_detected,
            "new_objects_count": len(self.context.new_objects),
            "tracked_objects_count": len(self.context.tracked_objects),
            "path_deviation_detected": self.context.path_deviation_detected,
            "slam_pose": self.context.slam_pose,
            "slam_map_status": self.context.slam_map_status,
            "system_ok": self.context.system_ok,
            "error_message": self.context.error_message,
            "current_state": self.state.name,
        }

        print("\n=== AKTUALNY STAN PERCEPCJI ===")
        print(json.dumps(state_snapshot, indent=2, ensure_ascii=False))

    def publish_perception_state(self) -> None:
        payload = {
            "frame_id": self.context.frame_id,
            "timestamp": self.context.timestamp,
            "roi": self.context.roi,
            "visual_markers": self.context.visual_markers,
            "human_detected": self.context.human_detected,
            "obstacle_detected": self.context.obstacle_detected,
            "new_objects": self.context.new_objects,
            "tracked_objects": [obj.__dict__ for obj in self.context.tracked_objects],
            "path_deviation_detected": self.context.path_deviation_detected,
            "slam_pose": self.context.slam_pose,
            "slam_map_status": self.context.slam_map_status,
            "system_ok": self.context.system_ok,
            "error_message": self.context.error_message,
        }
        self.ros2_publisher.publish_async(payload)


# ============================================================
# PRZYKŁAD UŻYCIA
# ============================================================

def main() -> None:
    sm = RobotPerceptionStateMachine()

    try:
        for frame_id in range(1, 4):
            fake_image = f"frame_{frame_id}"  # placeholder
            sm.set_input_image(fake_image, frame_id)

            # Jeden pełny cykl percepcji:
            while sm.state != PerceptionState.IDLE or sm.context.frame_id != frame_id:
                sm.run_once()
                if sm.state == PerceptionState.IDLE:
                    break

            time.sleep(0.5)

    finally:
        sm.shutdown()


if __name__ == "__main__":
    main()