from __future__ import annotations

from common.protocol import read_stdin_json, write_stdout_json, ok_response


def main() -> None:
    payload = read_stdin_json()
    markers = payload.get("visual_markers", [])
    tracked = payload.get("tracked_objects", [])

    slam_pose = {
        "x": 2.4 + 0.01 * len(markers),
        "y": 0.1,
        "z": 0.0,
        "theta": 0.03,
    }

    write_stdout_json(
        ok_response(
            slam_pose=slam_pose,
            slam_map_status=f"UPDATED_WITH_{len(markers)}_MARKERS_AND_{len(tracked)}_TRACKS",
        )
    )


if __name__ == "__main__":
    main()






""" old version
import json
import sys

def main() -> None:
    payload = json.load(sys.stdin)
    markers = payload.get("visual_markers", [])
    tracked_objects = payload.get("tracked_objects", [])

    slam_pose = {
        "x": 2.40 + 0.01 * len(markers),
        "y": 0.10,
        "theta": 0.03
    }

    response = {
        "status": "ok",
        "slam_pose": slam_pose,
        "slam_map_status": f"UPDATED_WITH_{len(markers)}_MARKERS_AND_{len(tracked_objects)}_TRACKS"
    }
    print(json.dumps(response, ensure_ascii=False))


if __name__ == "__main__":
    main() """