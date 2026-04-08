from __future__ import annotations

import argparse

from common.utils import load_config
from perception.state_machine import RobotPerceptionStateMachine
from perception.video_file_camera_service import VideoFileCameraService


class OfflineRosNode:
    def publish_snapshot(self, snapshot) -> None:
        return None

    def publish_point_cloud(self, snapshot) -> None:
        return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Uruchamia pipeline percepcji na pliku MP4 zamiast kamery live.",
    )
    parser.add_argument("video", help="Ścieżka do pliku MP4")
    parser.add_argument("--config", default="config/settings.yaml")
    parser.add_argument("--source", choices=["rgb", "rgbd"], default="rgb")
    parser.add_argument("--max-frames", type=int, default=None)
    parser.add_argument(
        "--print-snapshot",
        action="store_true",
        help="Wypisuj pełny snapshot JSON dla każdej klatki.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_config(args.config)

    video_camera = VideoFileCameraService(args.video, output_dir=config.output_dir)
    machine = RobotPerceptionStateMachine(
        config,
        OfflineRosNode(),
        selected_source=args.source,
        camera_service=video_camera,
    )

    if not args.print_snapshot:
        machine.print_snapshot = lambda: None  # type: ignore[assignment]

    processed_frames = 0
    try:
        while True:
            continue_running = machine.run_once()
            if not continue_running:
                break

            if machine.state.name == "IDLE":
                processed_frames += 1
                if args.max_frames is not None and processed_frames >= args.max_frames:
                    break
    finally:
        machine.shutdown()

    print(f"Przetworzono klatek: {processed_frames}")


if __name__ == "__main__":
    main()
