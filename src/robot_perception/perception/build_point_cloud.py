from __future__ import annotations
from common.protocol import read_stdin_json, write_stdout_json, ok_response

# Open3D albo ROS PointCloud2 dla chmury punktów,

def main() -> None:
    payload = read_stdin_json()
    slam_pose = payload.get("slam_pose") or {"x": 0.0, "y": 0.0, "z": 0.0}

    points = [
        [slam_pose["x"] + 0.0, slam_pose["y"] + 0.0, 0.0],
        [slam_pose["x"] + 0.2, slam_pose["y"] + 0.1, 0.0],
        [slam_pose["x"] + 0.3, slam_pose["y"] + 0.2, 0.1],
        [slam_pose["x"] + 0.4, slam_pose["y"] + 0.1, 0.0],
    ]

    write_stdout_json(
        ok_response(
            point_cloud={
                "frame_id": payload.get("frame_id"),
                "coordinate_frame": "map",
                "points": points,
                "point_count": len(points),
            }
        )
    )


if __name__ == "__main__":
    main()