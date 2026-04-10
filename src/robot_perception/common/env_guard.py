from __future__ import annotations

import os
from pathlib import Path

CONTAINER_FLAG_ENV = "ROBOT_PERCEPTION_IN_CONTAINER"
ENV_GUARD_FLAG = "ROBOT_PERCEPTION_ENV_GUARD"
EXPECTED_CONDA_ENV = "robot_perception"


def is_container_runtime() -> bool:
    """Detect whether application runs inside a container runtime."""
    # Flaga środowiskowa pozwala wymusić wykrycie kontenera np. w CI.
    env_flag = os.getenv(CONTAINER_FLAG_ENV, "").strip().lower()
    if env_flag in {"1", "true", "yes", "on"}:
        return True

    # Obecność /.dockerenv to standardowy sygnał uruchomienia w Dockerze.
    return Path("/.dockerenv").exists()


def env_guard_enabled() -> bool:
    """Return whether host-side conda environment guard should be enforced."""
    raw_value = os.getenv(ENV_GUARD_FLAG, "0").strip().lower()
    return raw_value in {"1", "true", "yes", "on"}


def validate_host_conda_env(expected_env: str = EXPECTED_CONDA_ENV) -> tuple[bool, str]:
    """Validate active conda environment on host runtime.

    Args:
        expected_env: Required conda environment name.

    Returns:
        Tuple with validation status and human-readable message.
    """
    if is_container_runtime():
        return True, "Container runtime detected - conda host validation skipped."

    active_env = os.getenv("CONDA_DEFAULT_ENV", "").strip()
    if active_env == expected_env:
        return True, f"Active conda environment is '{expected_env}'."

    if not active_env:
        return (
            False,
            "Brak aktywnego środowiska Conda. Aktywuj je poleceniem: "
            "conda activate robot_perception",
        )

    return (
        False,
        "Aktywne środowisko Conda to "
        f"'{active_env}', oczekiwano '{expected_env}'. Użyj: conda activate robot_perception",
    )
