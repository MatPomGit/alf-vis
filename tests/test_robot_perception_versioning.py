from __future__ import annotations

from pathlib import Path
import sys


# Dodajemy katalog projektu robot_perception do sys.path,
# aby testy mogły importować moduły bez instalacji pakietu.
ROBOT_PERCEPTION_ROOT = Path(__file__).resolve().parents[1] / "src" / "robot_perception"
if str(ROBOT_PERCEPTION_ROOT) not in sys.path:
    sys.path.insert(0, str(ROBOT_PERCEPTION_ROOT))

from common import versioning  # noqa: E402


def test_get_app_version_uses_main_commit_count(monkeypatch) -> None:
    """Wersja powinna używać liczby commitów z gałęzi main jako patch."""

    def fake_main_count() -> int:
        return 321

    monkeypatch.delenv(versioning.VERSION_ENV, raising=False)
    monkeypatch.setattr(versioning, "_main_commit_count", fake_main_count)

    assert versioning.get_app_version() == "0.1.321"


def test_get_app_version_respects_env_override(monkeypatch) -> None:
    """Zmienne środowiskowe powinny mieć pierwszeństwo nad wyliczaniem z git."""

    monkeypatch.setenv(versioning.VERSION_ENV, "9.9.9")
    assert versioning.get_app_version() == "9.9.9"


def test_version_banner_contains_author(monkeypatch) -> None:
    """Baner wersji powinien zawierać jawnie autora J2S."""

    def fake_main_count() -> int:
        return 77

    monkeypatch.delenv(versioning.VERSION_ENV, raising=False)
    monkeypatch.setattr(versioning, "_main_commit_count", fake_main_count)

    assert versioning.get_version_banner() == "robot_perception 0.1.77 | author: J2S"
