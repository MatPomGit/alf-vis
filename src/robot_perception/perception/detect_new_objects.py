from __future__ import annotations
from common.protocol import read_stdin_json, write_stdout_json, ok_response

def main() -> None:
    payload = read_stdin_json()
    tracked_objects = payload.get("tracked_objects", [])

    existing_labels = {obj["label"] for obj in tracked_objects if "label" in obj}
    candidate = {
        "label": "box",
        "bbox": [220, 180, 80, 60],
        "position": [220.0, 180.0],
        "velocity": [0.0, 0.0],
        "confidence": 0.94,
    }

    new_objects = []
    if candidate["label"] not in existing_labels:
        new_objects.append(candidate)

    write_stdout_json(ok_response(new_objects=new_objects))


if __name__ == "__main__":
    main()



""" old version
import json
import sys
def main() -> None:
    payload = json.load(sys.stdin)
    tracked_objects = payload.get("tracked_objects", [])

    known_labels = {obj["label"] for obj in tracked_objects if "label" in obj}

    detected = []
    candidate = {
        "label": "box",
        "bbox": [220, 180, 80, 60],
        "position": [220.0, 180.0],
        "velocity": [0.0, 0.0],
        "confidence": 0.93
    }

    if candidate["label"] not in known_labels:
        detected.append(candidate)

    response = {
        "status": "ok",
        "new_objects": detected
    }
    print(json.dumps(response, ensure_ascii=False))
 """