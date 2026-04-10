#!/usr/bin/env bash
set -euo pipefail

# Lekki launcher wymuszający poprawne środowisko uruchomieniowe na hoście.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONTAINER_FLAG="${ROBOT_PERCEPTION_IN_CONTAINER:-}"
ACTIVE_CONDA_ENV="${CONDA_DEFAULT_ENV:-}"

is_container_runtime() {
  # Flaga środowiskowa pozwala ręcznie wymusić tryb kontenera (np. w CI).
  if [[ "${CONTAINER_FLAG,,}" =~ ^(1|true|yes|on)$ ]]; then
    return 0
  fi

  # Standardowa detekcja Dockera.
  [[ -f "/.dockerenv" ]]
}

if ! is_container_runtime; then
  # Poza kontenerem wymagamy aktywnego środowiska Conda o nazwie robot_perception.
  if [[ "${ACTIVE_CONDA_ENV}" != "robot_perception" ]]; then
    cat <<'MSG'
[ENV_GUARD] Nie wykryto poprawnego środowiska Conda.
Aktywuj środowisko poleceniem:
  conda activate robot_perception

Następnie uruchom ponownie launcher.
MSG
    exit 1
  fi
fi

# Przekazujemy wszystkie argumenty do modułu uruchamiającego funkcje diagnostyczne.
exec python "${SCRIPT_DIR}/run_module.py" "$@"
