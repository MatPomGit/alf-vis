#!/usr/bin/env python3
"""Synchronizuje requirements.txt na podstawie canonical environment.yml."""

from __future__ import annotations

import argparse
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENVIRONMENT_FILE = PROJECT_ROOT / "environment.yml"
REQUIREMENTS_FILE = PROJECT_ROOT / "requirements.txt"


def _extract_requirements_from_environment(text: str) -> list[str]:
    """Wyciąga listę pakietów pip z `environment.yml`.

    Parser jest celowo prosty i działa dla naszej konwencji:
    - sekcja `dependencies:`,
    - podsekcja `- pip:`,
    - wpisy pip jako `- package...` z większym wcięciem.
    """

    lines = text.splitlines()
    in_dependencies = False
    in_pip_block = False
    pip_packages: list[str] = []

    for raw_line in lines:
        stripped = raw_line.strip()

        if stripped == "dependencies:":
            in_dependencies = True
            in_pip_block = False
            continue

        if not in_dependencies:
            continue

        if stripped.startswith("- pip:"):
            in_pip_block = True
            continue

        if in_pip_block:
            # Wiersze pakietów pip mają postać: "      - package>=x.y"
            if raw_line.startswith("      - "):
                package_spec = raw_line.replace("      - ", "", 1).strip()
                if package_spec:
                    pip_packages.append(package_spec)
                continue

            # Koniec bloku pip po natrafieniu na inny element listy zależności.
            if raw_line.startswith("  - "):
                in_pip_block = False

    return pip_packages


def generate_requirements_content() -> str:
    """Buduje docelową treść `requirements.txt` z nagłówkiem informacyjnym."""

    environment_text = ENVIRONMENT_FILE.read_text(encoding="utf-8")
    packages = _extract_requirements_from_environment(environment_text)

    header = [
        "# Ten plik jest generowany z environment.yml.",
        "# Nie edytuj ręcznie: użyj skryptu scripts/sync_requirements.py.",
        "",
    ]

    return "\n".join(header + packages + [""])


def main() -> None:
    """CLI: zapisuje plik albo sprawdza drift manifestów."""

    parser = argparse.ArgumentParser(
        description=(
            "Synchronizuje src/robot_perception/requirements.txt z "
            "src/robot_perception/environment.yml"
        )
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Sprawdza, czy requirements.txt jest zsynchronizowany.",
    )
    args = parser.parse_args()

    generated = generate_requirements_content()

    if args.check:
        current = REQUIREMENTS_FILE.read_text(encoding="utf-8") if REQUIREMENTS_FILE.exists() else ""
        if current != generated:
            raise SystemExit(
                "Wykryto drift manifestów. Uruchom: "
                "python src/robot_perception/scripts/sync_requirements.py"
            )
        print("OK: requirements.txt jest zsynchronizowany z environment.yml")
        return

    REQUIREMENTS_FILE.write_text(generated, encoding="utf-8")
    print(f"Zaktualizowano plik: {REQUIREMENTS_FILE}")


if __name__ == "__main__":
    main()
