# ORB-SLAM / RTAB-Map / własny backend dla visual SLAM,

from __future__ import annotations
from common.protocol import read_stdin_json, write_stdout_json, ok_response

def main() -> None:
    payload = read_stdin_json()
    image_path = payload.get("image_path")

    # Tu docelowo:
    # - inicjalizacja front-endu visual SLAM,
    # - stworzenie pierwszej mapy cech,
    # - ustalenie initial pose.
    write_stdout_json(
        ok_response(
            slam_initialized=True,
            slam_init_status="INITIALIZED",
            slam_pose={
                "x": 0.0,
                "y": 0.0,
                "z": 0.0,
                "theta": 0.0,
                "source_image": image_path,
            },
        )
    )


if __name__ == "__main__":
    main()