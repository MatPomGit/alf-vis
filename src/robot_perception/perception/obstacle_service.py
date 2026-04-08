from __future__ import annotations

from common.protocol import read_stdin_json, write_stdout_json, ok_response


def main() -> None:
    _payload = read_stdin_json()
    write_stdout_json(
        ok_response(
            obstacle_detected=True,
            obstacles=[
                {
                    "label": "chair",
                    "bbox": [320, 200, 90, 120],
                    "distance_m": 1.3,
                }
            ],
        )
    )


if __name__ == "__main__":
    main()



""" old
import json
import sys
def main() -> None:
    _payload = json.load(sys.stdin)

    response = {
        "status": "ok",
        "obstacle_detected": True,
        "obstacles": [
            {
                "label": "chair",
                "bbox": [300, 200, 90, 120],
                "distance_m": 1.4
            }
        ]
    }
    print(json.dumps(response, ensure_ascii=False))
 """