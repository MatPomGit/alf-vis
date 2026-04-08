from __future__ import annotations
from common.protocol import read_stdin_json, write_stdout_json, ok_response


def main() -> None:
    _payload = read_stdin_json()
    write_stdout_json(
        ok_response(
            human_detected=False,
            humans=[],
        )
    )


if __name__ == "__main__":
    main()



""" 
import json
import sys
def main() -> None:
    _payload = json.load(sys.stdin)

    response = {
        "status": "ok",
        "human_detected": False,
        "humans": []
    }
    print(json.dumps(response, ensure_ascii=False))
 """
