from __future__ import annotations
import shutil
import subprocess
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent
ENV_NAME = "robot_perception"
ENV_FILE = PROJECT_ROOT / "environment.yml"

def run(cmd: list[str]) -> None:
    print("[BOOTSTRAP]", " ".join(cmd))
    subprocess.run(cmd, check=True)

def detect_conda() -> str:
    conda = shutil.which("conda")
    if conda is None:
        raise RuntimeError("Nie znaleziono narzędzia 'conda'. Zainstaluj Miniconda lub Anaconda.")
    return conda

def main() -> None:
    conda_bin = detect_conda()
    run([conda_bin, "env", "update", "-f", str(ENV_FILE), "--prune"])
    print(f"\n[BOOTSTRAP] Środowisko {ENV_NAME} gotowe.")
    print("Pamiętaj o source środowiska ROS2 przed uruchomieniem programu.")

if __name__ == "__main__":
    main()
