from __future__ import annotations

import json
from pathlib import Path

from common.io_utils import ensure_dir
from common.protocol import read_stdin_json, write_stdout_json, ok_response


def main() -> None:
    payload = read_stdin_json()
    frame_id = payload.get("frame_id")
    point_cloud = payload.get("point_cloud", {})

    output_dir = ensure_dir(Path(__file__).resolve().parent.parent / "output" / "pointclouds")
    save_path = output_dir / f"pointcloud_frame_{frame_id}.json"

    save_path.write_text(json.dumps(point_cloud, ensure_ascii=False, indent=2), encoding="utf-8")
    # później zamienić format na PCD, PLY albo ROS sensor_msgs/PointCloud2.

    write_stdout_json(
        ok_response(
            point_cloud_save_path=str(save_path),
            saved=True,
        )
    )


if __name__ == "__main__":
    main()