from __future__ import annotations

import time
from pathlib import Path

from common.io_utils import ensure_dir
from common.protocol import read_stdin_json, write_stdout_json, ok_response


def main() -> None:
    payload = read_stdin_json()
    frame_id = int(payload.get("frame_id", 0))
    camera_id = int(payload.get("camera_id", 0))

    output_dir = ensure_dir(Path(__file__).resolve().parent.parent / "output" / "frames")
    image_path = output_dir / f"camera_{camera_id}_frame_{frame_id}.png"

    # Tu docelowo: odczyt z OpenCV / kamery RGB-D / streamu ROS2.
    # W szkielecie zapisujemy placeholder ścieżki.
    image_path.write_text("placeholder_frame_data", encoding="utf-8")

    write_stdout_json(
        ok_response(
            image_path=str(image_path),
            image_meta={
                "width": 640,
                "height": 480,
                "encoding": "bgr8",
                "camera_id": camera_id,
                "captured_at": time.time(),
            },
        )
    )


if __name__ == "__main__":
    main()