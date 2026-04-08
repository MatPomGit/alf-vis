from __future__ import annotations
from common.protocol import read_stdin_json, write_stdout_json, ok_response

def main() -> None:
    payload = read_stdin_json()
    tracked_objects = payload.get("tracked_objects", [])

    updated = []
    for obj in tracked_objects:
        pos_x, pos_y = obj.get("position", [0.0, 0.0])
        vel_x, vel_y = obj.get("velocity", [0.0, 0.0])

        updated.append(
            {
                "object_id": obj["object_id"],
                "label": obj["label"],
                "bbox": obj["bbox"],
                "position": [pos_x + vel_x, pos_y + vel_y],
                "velocity": [vel_x, vel_y],
                "confidence": obj.get("confidence", 1.0),
            }
        )

    write_stdout_json(ok_response(tracked_objects=updated))


if __name__ == "__main__":
    main()




""" old
import json
import sys
def main() -> None:
    payload = json.load(sys.stdin)
    tracked_objects = payload.get("tracked_objects", [])

    updated = []
    for obj in tracked_objects:
        pos_x, pos_y = obj.get("position", [0.0, 0.0])
        vel_x, vel_y = obj.get("velocity", [0.0, 0.0])

        updated.append({
            "object_id": obj["object_id"],
            "label": obj["label"],
            "bbox": obj["bbox"],
            "position": [pos_x + vel_x, pos_y + vel_y],
            "velocity": [vel_x, vel_y],
            "confidence": obj.get("confidence", 1.0)
        })

    response = {
        "status": "ok",
        "tracked_objects": updated
    }
    print(json.dumps(response, ensure_ascii=False))
 """