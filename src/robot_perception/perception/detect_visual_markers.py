from __future__ import annotations

from common.protocol import read_stdin_json, write_stdout_json, ok_response


def main() -> None:
    payload = read_stdin_json()
    roi = payload.get("roi")

    write_stdout_json(
        ok_response(
            visual_markers=[
                {
                    "id": 100,
                    "type": "aruco",
                    "roi_used": roi,
                    "pose": {"x": 1.2, "y": 0.4, "z": 0.0, "yaw": 0.02},
                }
            ]
        )
    )


if __name__ == "__main__":
    main()