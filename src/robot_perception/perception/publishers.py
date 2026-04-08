from __future__ import annotations
from sensor_msgs.msg import PointCloud2, PointField
from sensor_msgs_py import point_cloud2
from std_msgs.msg import Header, String
from common.models import PerceptionSnapshot, PointCloudData


class PublisherFactory:
    """Konwertery stanu percepcji do wiadomości ROS2."""

    @staticmethod
    def snapshot_to_string(snapshot: PerceptionSnapshot) -> String:
        """Serializuje snapshot percepcji do JSON."""
        msg = String()
        msg.data = snapshot.model_dump_json()
        return msg

    @staticmethod
    def point_cloud_to_msg(cloud: PointCloudData, frame_id: str = "map") -> PointCloud2:
        """Konwertuje chmurę punktów do `sensor_msgs/PointCloud2`."""
        header = Header()
        header.frame_id = frame_id
        fields = [
            PointField(name="x", offset=0, datatype=PointField.FLOAT32, count=1),
            PointField(name="y", offset=4, datatype=PointField.FLOAT32, count=1),
            PointField(name="z", offset=8, datatype=PointField.FLOAT32, count=1),
        ]
        points = [(float(x), float(y), float(z)) for x, y, z in cloud.points]
        return point_cloud2.create_cloud(header, fields, points)




"""
from __future__ import annotations

import json
from typing import Optional

import numpy as np
import open3d as o3d
from geometry_msgs.msg import Pose
from sensor_msgs.msg import PointCloud2, PointField
from std_msgs.msg import Header, String
from sensor_msgs_py import point_cloud2

from common.models import PerceptionSnapshot, PointCloudData


class PublisherFactory:
    ""Narzędzia pomocnicze do konwersji stanu percepcji na wiadomości ROS2.""

    @staticmethod
    def snapshot_to_string(snapshot: PerceptionSnapshot) -> String:
        ""Serializuje pełny snapshot percepcji do JSON w wiadomości `std_msgs/String`.""
        msg = String()
        msg.data = snapshot.model_dump_json()
        return msg

    @staticmethod
    def point_cloud_to_msg(cloud: PointCloudData, frame_id: str = "map") -> PointCloud2:
        ""Konwertuje chmurę punktów do wiadomości `sensor_msgs/PointCloud2`.""
        header = Header()
        header.frame_id = frame_id

        fields = [
            PointField(name="x", offset=0, datatype=PointField.FLOAT32, count=1),
            PointField(name="y", offset=4, datatype=PointField.FLOAT32, count=1),
            PointField(name="z", offset=8, datatype=PointField.FLOAT32, count=1),
        ]

        points = [(float(x), float(y), float(z)) for x, y, z in cloud.points]
        return point_cloud2.create_cloud(header, fields, points)



 """

""" 
from __future__ import annotations
from common.protocol import read_stdin_json, write_stdout_json, ok_response

# rclpy dla publikacji ROS2.
def main() -> None:
    payload = read_stdin_json()

    # Docelowo tutaj:
    # - rclpy.init()
    # - utworzenie Node
    # - publisher np. na /perception_state
    # - serializacja do wiadomości ROS2
    write_stdout_json(
        ok_response(
            published=True,
            topic="/perception_state",
            frame_id=payload.get("frame_id"),
        )
    )

if __name__ == "__main__":
    main() """

""" 
import json
import sys

def main() -> None:
    payload = json.load(sys.stdin)

    # Tu później podpinasz rclpy i publikację np. na /perception_state
    # Na razie tylko zwracamy potwierdzenie.

    response = {
        "status": "ok",
        "published": True,
        "topic": "/perception_state",
        "frame_id": payload.get("frame_id")
    }
    print(json.dumps(response, ensure_ascii=False))


if __name__ == "__main__":
    main() """