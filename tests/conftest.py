from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
TESTS = ROOT / "tests"

# Insert tests/ first so the cv2 headless shim (tests/cv2.py) and the
# ultralytics stub (tests/ultralytics.py) shadow the real packages during the
# test suite.  Insert src/ second so image_analysis is importable without an
# editable install.
for _path in (str(SRC), str(TESTS)):
    if _path not in sys.path:
        sys.path.insert(0, _path)
# Ensure tests/ is before src/ so shims take precedence.
if sys.path.index(str(TESTS)) > sys.path.index(str(SRC)):
    sys.path.remove(str(TESTS))
    sys.path.insert(0, str(TESTS))
