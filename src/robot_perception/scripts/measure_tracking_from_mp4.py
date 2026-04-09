from __future__ import annotations

import argparse
import csv
import math
import time
from pathlib import Path
from typing import Dict, List, Tuple

from common.utils import ensure_dir, load_config
from perception.state_machine import RobotPerceptionStateMachine
from perception.video_file_camera_service import VideoFileCameraService


class OfflineRosNode:
    def publish_snapshot(self, snapshot) -> None:
        return None

    def publish_point_cloud(self, snapshot) -> None:
        return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Pomiar metryk śledzenia i etapów maszyny stanów na pliku MP4.",
    )
    parser.add_argument("video", help="Ścieżka do pliku MP4")
    parser.add_argument("--config", default="config/settings.yaml")
    parser.add_argument("--source", choices=["rgb", "rgbd"], default="rgb")
    parser.add_argument("--max-frames", type=int, default=None)
    parser.add_argument(
        "--csv",
        default="output/tracking_measurements.csv",
        help="Ścieżka pliku CSV wynikowego.",
    )
    return parser.parse_args()


def _track_motion_metrics(
    prev_centroids: Dict[int, Tuple[float, float]],
    current_centroids: Dict[int, Tuple[float, float]],
) -> Dict[str, float]:
    shared_ids = set(prev_centroids).intersection(current_centroids)
    displacements: List[float] = []

    for object_id in shared_ids:
        px, py = prev_centroids[object_id]
        cx, cy = current_centroids[object_id]
        displacements.append(math.dist((px, py), (cx, cy)))

    mean_disp = sum(displacements) / len(displacements) if displacements else 0.0
    max_disp = max(displacements) if displacements else 0.0

    return {
        "tracks_shared_count": float(len(shared_ids)),
        "tracks_new_count": float(len(set(current_centroids) - set(prev_centroids))),
        "tracks_lost_count": float(len(set(prev_centroids) - set(current_centroids))),
        "tracks_mean_displacement_px": round(mean_disp, 4),
        "tracks_max_displacement_px": round(max_disp, 4),
    }


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    ensure_dir(Path(args.csv).parent)

    camera = VideoFileCameraService(args.video, output_dir=config.output_dir)
    machine = RobotPerceptionStateMachine(
        config,
        OfflineRosNode(),
        selected_source=args.source,
        camera_service=camera,
    )
    machine.print_snapshot = lambda: None  # type: ignore[assignment]

    rows: List[Dict[str, float | int | str | bool]] = []
    processed_frames = 0
    prev_track_centroids: Dict[int, Tuple[float, float]] = {}

    try:
        while True:
            state_before = machine.state.name
            run_ok = machine.run_once()
            state_after = machine.state.name
            snapshot = machine.snapshot

            current_track_centroids = {
                tracked.object_id: tracked.centroid_xy for tracked in snapshot.tracked_objects
            }
            motion = _track_motion_metrics(prev_track_centroids, current_track_centroids)

            row: Dict[str, float | int | str | bool] = {
                "wall_timestamp_sec": round(time.time(), 6),
                "frame_id": snapshot.frame_id,
                "frame_timestamp_sec": round(snapshot.timestamp_sec, 6),
                "video_timestamp_sec": round(camera.get_current_video_timestamp_sec(), 6),
                "state_before": state_before,
                "state_after": state_after,
                "run_ok": run_ok,
                "markers_count": len(snapshot.markers),
                "humans_count": len(snapshot.humans),
                "obstacles_count": len(snapshot.obstacles),
                "new_objects_count": len(snapshot.new_objects),
                "tracked_count": len(snapshot.tracked_objects),
                "path_deviation_detected": snapshot.path_deviation_detected,
                "path_deviation_value": round(snapshot.path_deviation_value, 6),
                "point_cloud_points": snapshot.point_cloud.point_count,
                "slam_initialized": snapshot.slam.initialized,
                "slam_map_point_count": snapshot.slam.map_point_count,
            }
            row.update(motion)
            for key, value in snapshot.processing_times_ms.items():
                row[f"time_ms::{key}"] = value

            rows.append(row)
            prev_track_centroids = current_track_centroids

            if not run_ok:
                break

            if machine.state.name == "IDLE":
                processed_frames += 1
                if args.max_frames is not None and processed_frames >= args.max_frames:
                    break
    finally:
        machine.shutdown()

    fieldnames: List[str] = []
    for row in rows:
        for key in row.keys():
            if key not in fieldnames:
                fieldnames.append(key)

    with open(args.csv, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Zapisano {len(rows)} pomiarów do: {args.csv}")
    print(f"Pełne klatki przetworzone w pipeline: {processed_frames}")


if __name__ == "__main__":
    main()
