from __future__ import annotations

import json
import sys
from typing import Any, Dict


def read_stdin_json() -> Dict[str, Any]:
    raw = sys.stdin.read().strip()
    if not raw:
        raise ValueError("Brak danych wejściowych JSON na stdin.")
    return json.loads(raw)


def write_stdout_json(payload: Dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False))


def ok_response(**kwargs: Any) -> Dict[str, Any]:
    response = {"status": "ok"}
    response.update(kwargs)
    return response


def error_response(message: str, **kwargs: Any) -> Dict[str, Any]:
    response = {"status": "error", "message": message}
    response.update(kwargs)
    return response