from __future__ import annotations

import json
import queue
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


BASE_DIR = Path(__file__).resolve().parent
MODULES_DIR = BASE_DIR / "modules"


class PerceptionState(Enum):
    IDLE = auto()
    CAPTURE_CAMERA_FRAME = auto()
    INIT_VISUAL_SLAM = auto()
    ACTIVE_VISION = auto()
    DETECT_VISUAL_MARKERS = auto()
    DETECT_HUMAN = auto()
    DETECT_OBSTACLE = auto()
    DETECT_NEW_OBJECTS = auto()
    TRACK_OBJECTS_KALMAN = auto()
    CHECK_PATH_DEVIATION = auto()
    UPDATE_VISUAL_SLAM = auto()
    BUILD_POINT_CLOUD = auto()
    SAVE_POINT_CLOUD = auto()
    PRINT_STATE = auto()
    PUBLISH_ROS2_STATE = auto()
    ERROR = auto()


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

    camera_id: int = 0
    image_path: Optional[str] = None
    image_meta: Dict[str, Any] = field(default_factory=dict)

    slam_initialized: bool = False
    slam_init_status: str = "NOT_INITIALIZED"
    slam_pose: Optional[Dict[str, float]] = None
    slam_map_status: str = "UNKNOWN"

    roi: Optional[Tuple[int, int, int, int]] = None
    visual_markers: List[Dict[str, Any]] = field(default_factory=list)
    human_detected: bool = False
    obstacle_detected: bool = False
    new_objects: List[Dict[str, Any]] = field(default_factory=list)
    tracked_objects: List[TrackedObject] = field(default_factory=list)

    path_deviation_detected: bool = False
    path_deviation_value: float = 0.0

    point_cloud: Dict[str, Any] = field(default_factory=dict)
    save_point_cloud_enabled: bool = False
    point_cloud_save_path: Optional[str] = None

    processing_times_ms: Dict[str, float] = field(default_factory=dict)

    system_ok: bool = True
    error_message: Optional[str] = None

    def to_payload(self) -> Dict[str, Any]:
        return {
            "frame_id": self.frame_id,
            "timestamp": self.timestamp,
            "camera_id": self.camera_id,
            "image_path": self.image_path,
            "image_meta": self.image_meta,
            "slam_initialized": self.slam_initialized,
            "slam_init_status": self.slam_init_status,
            "slam_pose": self.slam_pose,
            "slam_map_status": self.slam_map_status,
            "roi": self.roi,
            "visual_markers": self.visual_markers,
            "human_detected": self.human_detected,
            "obstacle_detected": self.obstacle_detected,
            "new_objects": self.new_objects,
            "tracked_objects": [asdict(obj) for obj in self.tracked_objects],
            "path_deviation_detected": self.path_deviation_detected,
            "path_deviation_value": self.path_deviation_value,
            "point_cloud": self.point_cloud,
            "save_point_cloud_enabled": self.save_point_cloud_enabled,
            "point_cloud_save_path": self.point_cloud_save_path,
            "processing_times_ms": self.processing_times_ms,
        }


class ExternalModuleError(RuntimeError):
    pass


class ExternalModuleRunner:
    def __init__(self, python_executable: str = sys.executable) -> None:
        self.python_executable = python_executable

    def run(self, script_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        script_path = MODULES_DIR / script_name
        if not script_path.exists():
            raise ExternalModuleError(f"Brak skryptu modułu: {script_path}")

        result = subprocess.run(
            [self.python_executable, str(script_path)],
            input=json.dumps(payload, ensure_ascii=False),
            text=True,
            capture_output=True,
            check=False,
        )

        if result.returncode != 0:
            raise ExternalModuleError(
                f"Moduł {script_name} zakończył się błędem.\n"
                f"STDERR: {result.stderr.strip()}\n"
                f"STDOUT: {result.stdout.strip()}"
            )

        stdout = result.stdout.strip()
        if not stdout:
            raise ExternalModuleError(f"Moduł {script_name} nie zwrócił danych JSON.")

        try:
            response = json.loads(stdout)
        except json.JSONDecodeError as exc:
            raise ExternalModuleError(
                f"Moduł {script_name} zwrócił niepoprawny JSON: {stdout}"
            ) from exc

        if response.get("status") != "ok":
            raise ExternalModuleError(
                f"Moduł {script_name} zwrócił status inny niż ok: {response}"
            )

        return response


class ROS2PublisherThread(threading.Thread):
    def __init__(self, runner: ExternalModuleRunner) -> None:
        super().__init__(daemon=True)
        self.runner = runner
        self._queue: queue.Queue[Dict[str, Any]] = queue.Queue()
        self._stop_event = threading.Event()

    def publish_async(self, state: Dict[str, Any]) -> None:
        self._queue.put(state)

    def run(self) -> None:
        while not self._stop_event.is_set():
            try:
                payload = self._queue.get(timeout=0.1)
            except queue.Empty:
                continue

            try:
                response = self.runner.run("publish_ros2_state.py", payload)
                print("[ROS2 THREAD]", json.dumps(response, ensure_ascii=False))
            except Exception as exc:
                print(f"[ROS2 THREAD ERROR] {exc}")

    def stop(self) -> None:
        self._stop_event.set()


class RobotPerceptionStateMachine:
    def __init__(self, camera_id: int = 0, save_point_cloud_enabled: bool = False) -> None:
        self.state = PerceptionState.IDLE
        self.context = PerceptionContext(
            camera_id=camera_id,
            save_point_cloud_enabled=save_point_cloud_enabled,
        )
        self.runner = ExternalModuleRunner()
        self.ros2_publisher = ROS2PublisherThread(self.runner)
        self.ros2_publisher.start()
        self._next_object_id = 1

    def shutdown(self) -> None:
        self.ros2_publisher.stop()
        self.ros2_publisher.join(timeout=1.0)

    def transition_to(self, next_state: PerceptionState) -> None:
        self.state = next_state

    def _run_module(self, script_name: str) -> Dict[str, Any]:
        start = time.perf_counter()
        response = self.runner.run(script_name, self.context.to_payload())
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        self.context.processing_times_ms[script_name] = round(elapsed_ms, 3)
        return response

    def run_once(self) -> None:
        try:
            if self.state == PerceptionState.IDLE:
                self.context.frame_id += 1
                self.context.timestamp = time.time()
                self.transition_to(PerceptionState.CAPTURE_CAMERA_FRAME)

            elif self.state == PerceptionState.CAPTURE_CAMERA_FRAME:
                result = self._run_module("capture_camera_frame.py")
                self.context.image_path = result["image_path"]
                self.context.image_meta = result["image_meta"]
                self.transition_to(PerceptionState.INIT_VISUAL_SLAM)

            elif self.state == PerceptionState.INIT_VISUAL_SLAM:
                if not self.context.slam_initialized:
                    result = self._run_module("init_visual_slam.py")
                    self.context.slam_initialized = bool(result["slam_initialized"])
                    self.context.slam_init_status = result["slam_init_status"]
                    self.context.slam_pose = result.get("slam_pose")
                self.transition_to(PerceptionState.ACTIVE_VISION)

            elif self.state == PerceptionState.ACTIVE_VISION:
                result = self._run_module("active_vision.py")
                self.context.roi = tuple(result["roi"])
                self.transition_to(PerceptionState.DETECT_VISUAL_MARKERS)

            elif self.state == PerceptionState.DETECT_VISUAL_MARKERS:
                result = self._run_module("detect_visual_markers.py")
                self.context.visual_markers = result.get("visual_markers", [])
                self.transition_to(PerceptionState.DETECT_HUMAN)

            elif self.state == PerceptionState.DETECT_HUMAN:
                result = self._run_module("detect_human.py")
                self.context.human_detected = bool(result.get("human_detected", False))
                self.transition_to(PerceptionState.DETECT_OBSTACLE)

            elif self.state == PerceptionState.DETECT_OBSTACLE:
                result = self._run_module("detect_obstacle.py")
                self.context.obstacle_detected = bool(result.get("obstacle_detected", False))
                self.transition_to(PerceptionState.DETECT_NEW_OBJECTS)

            elif self.state == PerceptionState.DETECT_NEW_OBJECTS:
                result = self._run_module("detect_new_objects.py")
                self.context.new_objects = result.get("new_objects", [])

                for obj in self.context.new_objects:
                    tracked = TrackedObject(
                        object_id=self._next_object_id,
                        label=obj["label"],
                        bbox=tuple(obj["bbox"]),
                        position=tuple(obj["position"]),
                        velocity=tuple(obj.get("velocity", [0.0, 0.0])),
                        confidence=float(obj.get("confidence", 1.0)),
                    )
                    self.context.tracked_objects.append(tracked)
                    self._next_object_id += 1

                self.transition_to(PerceptionState.TRACK_OBJECTS_KALMAN)

            elif self.state == PerceptionState.TRACK_OBJECTS_KALMAN:
                result = self._run_module("track_objects_kalman.py")
                tracked_objects: List[TrackedObject] = []
                for obj in result.get("tracked_objects", []):
                    tracked_objects.append(
                        TrackedObject(
                            object_id=int(obj["object_id"]),
                            label=obj["label"],
                            bbox=tuple(obj["bbox"]),
                            position=tuple(obj["position"]),
                            velocity=tuple(obj.get("velocity", [0.0, 0.0])),
                            confidence=float(obj.get("confidence", 1.0)),
                        )
                    )
                self.context.tracked_objects = tracked_objects
                self.transition_to(PerceptionState.CHECK_PATH_DEVIATION)

            elif self.state == PerceptionState.UPDATE_VISUAL_SLAM:
                result = self._run_module("update_visual_slam.py")
                self.context.slam_pose = result.get("slam_pose")
                self.context.slam_map_status = result.get("slam_map_status", "UNKNOWN")
                self.transition_to(PerceptionState.BUILD_POINT_CLOUD)
            
            elif self.state == PerceptionState.CHECK_PATH_DEVIATION:
                result = self._run_module("check_path_deviation.py")
                self.context.path_deviation_detected = bool(result.get("path_deviation_detected", False))
                self.context.path_deviation_value = float(result.get("path_deviation_value", 0.0))
                self.transition_to(PerceptionState.UPDATE_VISUAL_SLAM)

            elif self.state == PerceptionState.BUILD_POINT_CLOUD:
                result = self._run_module("build_point_cloud.py")
                self.context.point_cloud = result.get("point_cloud", {})
                self.transition_to(PerceptionState.SAVE_POINT_CLOUD)

            elif self.state == PerceptionState.SAVE_POINT_CLOUD:
                if self.context.save_point_cloud_enabled:
                    result = self._run_module("save_point_cloud.py")
                    self.context.point_cloud_save_path = result.get("point_cloud_save_path")
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
            "camera_id": self.context.camera_id,
            "image_path": self.context.image_path,
            "image_meta": self.context.image_meta,
            "slam_initialized": self.context.slam_initialized,
            "slam_init_status": self.context.slam_init_status,
            "slam_pose": self.context.slam_pose,
            "slam_map_status": self.context.slam_map_status,
            "roi": self.context.roi,
            "visual_markers_count": len(self.context.visual_markers),
            "human_detected": self.context.human_detected,
            "obstacle_detected": self.context.obstacle_detected,
            "new_objects_count": len(self.context.new_objects),
            "tracked_objects_count": len(self.context.tracked_objects),
            "path_deviation_detected": self.context.path_deviation_detected,
            "path_deviation_value": self.context.path_deviation_value,
            "point_cloud_points_count": len(self.context.point_cloud.get("points", [])),
            "point_cloud_save_path": self.context.point_cloud_save_path,
            "processing_times_ms": self.context.processing_times_ms,
            "system_ok": self.context.system_ok,
            "error_message": self.context.error_message,
            "current_state": self.state.name,
        }
        print("\n=== AKTUALNY STAN PERCEPCJI ===")
        print(json.dumps(state_snapshot, indent=2, ensure_ascii=False))

    def publish_perception_state(self) -> None:
        payload = self.context.to_payload()
        payload["system_ok"] = self.context.system_ok
        payload["error_message"] = self.context.error_message
        self.ros2_publisher.publish_async(payload)


def main() -> None:
    sm = RobotPerceptionStateMachine(camera_id=0, save_point_cloud_enabled=True)

    try:
        for _ in range(2):
            while True:
                sm.run_once()
                if sm.state == PerceptionState.IDLE:
                    break
            time.sleep(0.2)
    finally:
        sm.shutdown()


if __name__ == "__main__":
    main()