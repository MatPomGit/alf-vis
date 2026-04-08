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
    main()






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