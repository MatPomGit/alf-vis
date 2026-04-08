from __future__ import annotations

from common.protocol import read_stdin_json, write_stdout_json, ok_response


def main() -> None:
    payload = read_stdin_json()
    meta = payload.get("image_meta", {})
    width = int(meta.get("width", 640))
    height = int(meta.get("height", 480))

    roi = [width // 4, height // 4, width // 2, height // 2]

    write_stdout_json(
        ok_response(
            roi=roi,
            strategy="task_guided_roi_selection",
        )
    )


if __name__ == "__main__":
    main()