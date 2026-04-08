from __future__ import annotations
import os
import shutil
import subprocess
import sys
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
        raise RuntimeError(
            "Nie znaleziono narzędzia 'conda'. Zainstaluj Miniconda lub Anaconda."
        )
    return conda


def create_or_update_env(conda_bin: str) -> None:
    run([conda_bin, "env", "update", "-f", str(ENV_FILE), "--prune"])


def install_ros_python_dependencies(conda_bin: str) -> None:
    print(
        "[BOOTSTRAP] Uwaga: pakiety ROS2 Python są zwykle dostarczane przez środowisko ROS2,"
        "a nie przez pip/conda. Upewnij się, że source'ujesz odpowiedni setup.bash ROS2."
    )


def print_next_steps(conda_bin: str) -> None:
    print(
"        [BOOTSTRAP] Środowisko gotowe.")
    print(f"Aktywacja: conda activate {ENV_NAME}")
    print("Przykładowe uruchomienie FSM: python main.py")
    print("Uruchomienie modułu indywidualnie: python run_module.py apriltag")
    print(
        "Pamiętaj, aby przed uruchomieniem source'ować środowisko ROS2, np.:"
        "source /opt/ros/humble/setup.bash"
    )


def main() -> None:
    conda_bin = detect_conda()
    create_or_update_env(conda_bin)
    install_ros_python_dependencies(conda_bin)
    print_next_steps(conda_bin)


if __name__ == "__main__":
    main()