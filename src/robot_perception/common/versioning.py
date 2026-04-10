from __future__ import annotations

import os
import subprocess
from pathlib import Path

DEFAULT_BASE_VERSION = "0.1"
VERSION_ENV = "ROBOT_PERCEPTION_VERSION"
APP_AUTHOR = "J2S"


def _repo_root() -> Path:
    """Return repository root path inferred from this module location."""
    return Path(__file__).resolve().parents[3]


def _run_git_command(args: list[str]) -> str | None:
    """Execute a git command and return stripped stdout or None on failure."""
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=_repo_root(),
            check=True,
            capture_output=True,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return completed.stdout.strip()


def _main_commit_count() -> int | None:
    """Return number of commits reachable from main branch."""
    # Celowo liczymy patch wyłącznie z historii gałęzi main,
    # aby numeracja buildów była deterministyczna i niezależna
    # od commitów na gałęziach feature.
    raw_count = _run_git_command(["rev-list", "--count", "refs/heads/main"])
    if raw_count is None:
        # Fallback dla checkoutów, które nie mają lokalnej gałęzi main.
        # Dzięki temu nadal używamy historii main, ale z remote tracking branch.
        raw_count = _run_git_command(["rev-list", "--count", "refs/remotes/origin/main"])
    if raw_count is None:
        return None

    try:
        return int(raw_count)
    except ValueError:
        return None


def get_app_version(base_version: str = DEFAULT_BASE_VERSION) -> str:
    """Build application version string.

    Versioning policy:
    - host override via ROBOT_PERCEPTION_VERSION,
    - otherwise base_version + commit count from main branch.
    """
    # Nadpisanie środowiskowe ułatwia pinowanie wersji w release pipeline.
    env_version = os.getenv(VERSION_ENV, "").strip()
    if env_version:
        return env_version

    commit_count = _main_commit_count()
    if commit_count is None:
        return f"{base_version}.0"

    return f"{base_version}.{commit_count}"


def get_app_metadata(base_version: str = DEFAULT_BASE_VERSION) -> dict[str, str]:
    """Return application metadata for CLI/GUI presentation."""
    return {
        "name": "robot_perception",
        "version": get_app_version(base_version=base_version),
        "author": APP_AUTHOR,
    }


def get_version_banner(base_version: str = DEFAULT_BASE_VERSION) -> str:
    """Build compact user-facing version banner."""
    metadata = get_app_metadata(base_version=base_version)
    return f"{metadata['name']} {metadata['version']} | author: {metadata['author']}"
