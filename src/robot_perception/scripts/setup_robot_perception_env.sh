#!/usr/bin/env bash
set -Eeuo pipefail

# ============================================================
# Autonomiczne stawianie środowiska dla projektu robot_perception
# ============================================================
# Ten skrypt wspiera trzy niezależne tryby:
#   --conda-only : tylko środowisko Python/Conda
#   --ros-only   : tylko warstwa ROS2 (pakiety systemowe + source)
#   --full       : conda + ROS2 (domyślnie)
#
# Dodatkowo:
#   --dry-run    : diagnostyka i plan działań bez zmian w systemie.
#
# Założenia obligatoryjne i opcjonalne są logowane jawnie.
# ============================================================

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
ENV_NAME="robot_perception"
PYTHON_VERSION="3.11"
MINICONDA_DIR="${HOME}/miniconda3"
ROS_DISTRO_DEFAULT="${ROS_DISTRO:-humble}"
INSTALL_ROS_PACKAGES="${INSTALL_ROS_PACKAGES:-auto}"

MODE="full"
DRY_RUN=0

log()  { printf '[SETUP][INFO] %s\n' "$*"; }
warn() { printf '[SETUP][WARN] %s\n' "$*"; }
err()  { printf '[SETUP][ERROR] %s\n' "$*" >&2; }

# Komentarz PL: Funkcja wykonuje polecenie lub tylko loguje je w trybie dry-run.
run_cmd() {
  if (( DRY_RUN )); then
    log "[DRY-RUN] $*"
    return 0
  fi
  "$@"
}

# Komentarz PL: Walidacja wymaganych poleceń systemowych.
require_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    err "Brak wymaganego polecenia: $1"
    exit 1
  }
}

is_linux() {
  [[ "$(uname -s)" == "Linux" ]]
}

is_debian_like() {
  [[ -f /etc/debian_version ]]
}

have_sudo() {
  command -v sudo >/dev/null 2>&1 && sudo -n true >/dev/null 2>&1
}

# Komentarz PL: Minimalny parser argumentów CLI.
parse_args() {
  while (($#)); do
    case "$1" in
      --conda-only)
        MODE="conda-only"
        ;;
      --ros-only)
        MODE="ros-only"
        ;;
      --full)
        MODE="full"
        ;;
      --dry-run)
        DRY_RUN=1
        ;;
      -h|--help)
        cat <<USAGE
Użycie: $(basename "$0") [--conda-only|--ros-only|--full] [--dry-run]

Tryby:
  --conda-only   Konfiguruje tylko Conda + Python dependencies.
  --ros-only     Konfiguruje tylko ROS2 (warstwa systemowa + source).
  --full         Konfiguruje Conda oraz ROS2 (domyślnie).

Opcje:
  --dry-run      Tylko diagnoza i plan działań bez instalacji i modyfikacji.
USAGE
        exit 0
        ;;
      *)
        err "Nieznany argument: $1"
        exit 2
        ;;
    esac
    shift
  done
}

# Komentarz PL: Jawne logowanie wymagań obowiązkowych i opcjonalnych.
print_requirements_matrix() {
  log "Wymagania OBLIGATORYJNE (zależnie od trybu):"
  if [[ "${MODE}" == "conda-only" || "${MODE}" == "full" ]]; then
    log "  - bash, curl, tar, uname"
    log "  - Conda (zainstalowana lub możliwa do instalacji)"
    log "  - environment.yml lub minimalne utworzenie env"
  fi
  if [[ "${MODE}" == "ros-only" || "${MODE}" == "full" ]]; then
    log "  - Linux (dla auto-instalacji pakietów ROS)"
    log "  - Debian/Ubuntu + sudo (dla auto-instalacji pakietów ROS)"
  fi

  log "Wymagania OPCJONALNE:"
  log "  - INSTALL_ROS_PACKAGES=never (wyłącza auto-instalację ROS)"
  log "  - python3-tk (GUI; zwykle pakiet systemowy)"
  log "  - ROS2 już obecny w /opt/ros/*/setup.bash"
}

ensure_basic_tools() {
  log "Sprawdzanie podstawowych narzędzi systemowych..."
  require_cmd bash
  require_cmd curl
  require_cmd tar
  require_cmd uname
}

install_miniconda_if_needed() {
  if command -v conda >/dev/null 2>&1; then
    log "Conda jest już dostępna: $(command -v conda)"
    return 0
  fi

  if [[ -x "${MINICONDA_DIR}/bin/conda" ]]; then
    log "Znaleziono lokalną instalację Miniconda w ${MINICONDA_DIR}"
    return 0
  fi

  log "Nie znaleziono Conda. Instaluję lokalnie Miniconda do ${MINICONDA_DIR}..."
  local installer="${HOME}/miniconda_installer.sh"
  run_cmd curl -fsSL https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -o "${installer}"
  run_cmd bash "${installer}" -b -p "${MINICONDA_DIR}"
  run_cmd rm -f "${installer}"
  log "Miniconda została zainstalowana."
}

setup_conda_shell() {
  if command -v conda >/dev/null 2>&1; then
    # shellcheck disable=SC1091
    eval "$(conda shell.bash hook)"
    return 0
  fi

  if [[ -x "${MINICONDA_DIR}/bin/conda" ]]; then
    # shellcheck disable=SC1091
    eval "$(${MINICONDA_DIR}/bin/conda shell.bash hook)"
    return 0
  fi

  if (( DRY_RUN )); then
    warn "[DRY-RUN] Nie znaleziono Conda shell hook. To jest brak do uzupełnienia poza dry-run."
    return 0
  fi

  err "Nie udało się aktywować Conda."
  exit 1
}

create_or_update_conda_env() {
  log "Tworzenie / aktualizacja środowiska Conda: ${ENV_NAME}"

  if [[ -f "${PROJECT_ROOT}/environment.yml" ]]; then
    run_cmd conda env update -n "${ENV_NAME}" -f "${PROJECT_ROOT}/environment.yml" --prune || \
      run_cmd conda env create -n "${ENV_NAME}" -f "${PROJECT_ROOT}/environment.yml"
  else
    warn "Brak environment.yml. Tworzę środowisko minimalne ręcznie."
    run_cmd conda create -y -n "${ENV_NAME}" "python=${PYTHON_VERSION}" pip
  fi

  if (( DRY_RUN )); then
    log "[DRY-RUN] Pominąłem aktywację środowiska ${ENV_NAME}."
    return 0
  fi

  conda activate "${ENV_NAME}"
  log "Aktywowane środowisko: ${ENV_NAME}"
}

install_python_dependencies() {
  log "Instalacja zależności Python..."
  run_cmd python -m pip install --upgrade pip setuptools wheel

  # Komentarz PL: Wymuszamy pojedyncze źródło prawdy.
  # Jeżeli istnieje environment.yml, to dependencies pip są już tam zdefiniowane.
  # Dzięki temu unikamy redundancji i potencjalnych konfliktów wersji (np. transforms3d).
  if [[ ! -f "${PROJECT_ROOT}/environment.yml" && -f "${PROJECT_ROOT}/requirements.txt" ]]; then
    log "Brak environment.yml, używam requirements.txt jako fallback."
    run_cmd python -m pip install -r "${PROJECT_ROOT}/requirements.txt"
  else
    log "Pomijam requirements.txt, bo dependencies pochodzą z environment.yml (brak duplikatów instalacji)."
  fi

  if (( DRY_RUN )); then
    log "[DRY-RUN] Pominąłem pip check i weryfikację importów Python."
    return 0
  fi

  # Kontrola spójności środowiska (informacyjna, bez przerywania bootstrapu).
  python -m pip check || true

  python - <<'PY'
import importlib
mods = ["pydantic", "numpy", "cv2", "open3d", "yaml", "ultralytics", "pupil_apriltags", "transforms3d"]
missing = [m for m in mods if importlib.util.find_spec(m) is None]
if missing:
    raise SystemExit("Brakujące moduły Python po instalacji: " + ", ".join(missing))
print("[SETUP][INFO] Importy Python zweryfikowane poprawnie.")
PY
}

find_ros_setup() {
  local distro="${ROS_DISTRO_DEFAULT}"
  if [[ -f "/opt/ros/${distro}/setup.bash" ]]; then
    printf '%s' "/opt/ros/${distro}/setup.bash"
    return 0
  fi

  if compgen -G "/opt/ros/*/setup.bash" >/dev/null 2>&1; then
    ls -1 /opt/ros/*/setup.bash 2>/dev/null | head -n 1
    return 0
  fi

  return 1
}

install_ros_system_packages_if_possible() {
  local distro="${ROS_DISTRO_DEFAULT}"

  if [[ "${INSTALL_ROS_PACKAGES}" == "never" ]]; then
    warn "Pomijam instalację pakietów ROS2, bo INSTALL_ROS_PACKAGES=never"
    return 0
  fi

  if find_ros_setup >/dev/null 2>&1; then
    log "ROS2 jest już dostępny w systemie."
    return 0
  fi

  if ! is_linux || ! is_debian_like; then
    warn "Automatyczna instalacja ROS2 jest obsługiwana tutaj tylko dla systemów Debian/Ubuntu."
    return 0
  fi

  if ! have_sudo; then
    warn "Brak bezhasłowego sudo. Nie instaluję automatycznie ROS2 pakietów systemowych."
    warn "Uruchom ręcznie jako root lub skonfiguruj sudo, jeśli chcesz auto-instalację."
    return 0
  fi

  log "Próba instalacji pakietów systemowych ROS2 dla dystrybucji: ${distro}"
  run_cmd sudo apt-get update
  run_cmd sudo apt-get install -y \
    python3-tk \
    python3-colcon-common-extensions \
    "ros-${distro}-ros-base" \
    "ros-${distro}-tf2-ros" \
    "ros-${distro}-sensor-msgs-py" \
    "ros-${distro}-rtabmap-msgs" || {
      warn "Nie udało się zainstalować części pakietów ROS2."
    }
}

source_ros_if_available() {
  local ros_setup
  if ros_setup="$(find_ros_setup)"; then
    if (( DRY_RUN )); then
      log "[DRY-RUN] Wykryto ROS setup: ${ros_setup}"
      return 0
    fi
    # shellcheck disable=SC1090
    source "${ros_setup}"
    log "Załadowano środowisko ROS2 z: ${ros_setup}"
  else
    warn "Nie znaleziono /opt/ros/*/setup.bash. Część ROS2 może nie działać."
  fi
}

verify_ros_imports_if_available() {
  if (( DRY_RUN )); then
    log "[DRY-RUN] Pominąłem import-check modułów ROS Python."
    return 0
  fi

  python - <<'PY'
import importlib.util
mods = ["rclpy", "tf2_ros"]
available = [m for m in mods if importlib.util.find_spec(m) is not None]
missing = [m for m in mods if importlib.util.find_spec(m) is None]
if available:
    print("[SETUP][INFO] Wykryte moduły ROS Python:", ", ".join(available))
if missing:
    print("[SETUP][WARN] Niewykryte moduły ROS Python:", ", ".join(missing))
PY
}

create_helper_run_script() {
  local helper="${PROJECT_ROOT}/run_project_env.sh"
  local ros_setup=""
  ros_setup="$(find_ros_setup || true)"

  if (( DRY_RUN )); then
    log "[DRY-RUN] Pominąłem generowanie ${helper}"
    return 0
  fi

  cat > "${helper}" <<EOF_HELPER
#!/usr/bin/env bash
set -Eeuo pipefail
PROJECT_ROOT="${PROJECT_ROOT}"
ENV_NAME="${ENV_NAME}"
MINICONDA_DIR="${MINICONDA_DIR}"
ROS_SETUP="${ros_setup}"

if command -v conda >/dev/null 2>&1; then
  eval "\$(conda shell.bash hook)"
elif [[ -x "\${MINICONDA_DIR}/bin/conda" ]]; then
  eval "\$(\${MINICONDA_DIR}/bin/conda shell.bash hook)"
else
  echo "[RUN][ERROR] Nie znaleziono conda." >&2
  exit 1
fi

conda activate "\${ENV_NAME}"

if [[ -n "\${ROS_SETUP}" && -f "\${ROS_SETUP}" ]]; then
  # shellcheck disable=SC1090
  source "\${ROS_SETUP}"
fi

cd "\${PROJECT_ROOT}"
exec "$@"
EOF_HELPER
  chmod +x "${helper}"
  log "Utworzono pomocniczy skrypt uruchomieniowy: ${helper}"
}

print_container_host_mapping() {
  cat <<EOF_MAPPING
[SETUP][INFO] Mapowanie trybów host/kontener:
[SETUP][INFO]   Host (pełny bootstrap):
[SETUP][INFO]     ./scripts/setup_robot_perception_env.sh --full
[SETUP][INFO]
[SETUP][INFO]   Host (tylko Python, bez ROS2):
[SETUP][INFO]     ./scripts/setup_robot_perception_env.sh --conda-only
[SETUP][INFO]
[SETUP][INFO]   Kontener z preinstalowanym ROS2 (doinstaluj tylko Python):
[SETUP][INFO]     ./scripts/setup_robot_perception_env.sh --conda-only
[SETUP][INFO]
[SETUP][INFO]   Kontener/host z gotowym Conda, ale bez ROS2:
[SETUP][INFO]     ./scripts/setup_robot_perception_env.sh --ros-only
[SETUP][INFO]
[SETUP][INFO]   Diagnostyka braków bez zmian:
[SETUP][INFO]     ./scripts/setup_robot_perception_env.sh --full --dry-run
EOF_MAPPING
}

print_summary() {
  cat <<EOF_SUMMARY

[SETUP][INFO] ================================================
[SETUP][INFO] Środowisko projektu zostało przygotowane.
[SETUP][INFO] Katalog projektu: ${PROJECT_ROOT}
[SETUP][INFO] Środowisko Conda: ${ENV_NAME}
[SETUP][INFO] Tryb: ${MODE}
[SETUP][INFO] Dry-run: ${DRY_RUN}
[SETUP][INFO]
[SETUP][INFO] Przykładowe uruchomienia:
[SETUP][INFO]   ${PROJECT_ROOT}/run_project_env.sh python run_module.py markers
[SETUP][INFO]   ${PROJECT_ROOT}/run_project_env.sh python run_module.py rgbd
[SETUP][INFO]   ${PROJECT_ROOT}/run_project_env.sh python main_perception.py --source rgb
[SETUP][INFO]   ${PROJECT_ROOT}/run_project_env.sh python main_slam.py
[SETUP][INFO]   ${PROJECT_ROOT}/run_project_env.sh python run_module.py gui
[SETUP][INFO]
[SETUP][INFO] Uwaga:
[SETUP][INFO] - Moduły markers i rgbd nie wymagają ROS2.
[SETUP][INFO] - GUI, perception, slam i rtabmap_bridge wymagają środowiska ROS2.
[SETUP][INFO] ================================================
EOF_SUMMARY
}

main() {
  parse_args "$@"

  log "Start konfiguracji środowiska dla projektu robot_perception"
  log "Katalog projektu: ${PROJECT_ROOT}"
  log "Wybrany tryb: ${MODE}"
  (( DRY_RUN )) && warn "Uruchomiono w trybie DRY-RUN: brak zmian w systemie."

  print_requirements_matrix

  case "${MODE}" in
    conda-only)
      ensure_basic_tools
      install_miniconda_if_needed
      setup_conda_shell
      create_or_update_conda_env
      install_python_dependencies
      create_helper_run_script
      ;;
    ros-only)
      install_ros_system_packages_if_possible
      source_ros_if_available
      verify_ros_imports_if_available
      create_helper_run_script
      ;;
    full)
      ensure_basic_tools
      install_miniconda_if_needed
      setup_conda_shell
      create_or_update_conda_env
      install_python_dependencies
      install_ros_system_packages_if_possible
      source_ros_if_available
      verify_ros_imports_if_available
      create_helper_run_script
      ;;
    *)
      err "Nieobsługiwany tryb: ${MODE}"
      exit 2
      ;;
  esac

  print_container_host_mapping
  print_summary
}

main "$@"
