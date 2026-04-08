#!/usr/bin/env bash
set -Eeuo pipefail

# ============================================================
# Autonomiczne stawianie środowiska dla projektu robot_perception
# ============================================================
# Co robi skrypt:
# 1. Wykrywa katalog projektu.
# 2. Instaluje Miniconda lokalnie do HOME, jeśli conda nie jest dostępna.
# 3. Tworzy / aktualizuje środowisko Conda na podstawie environment.yml.
# 4. Doinstalowuje wymagane biblioteki Python, których może brakować.
# 5. Próbuje podpiąć ROS2. Jeśli wykryje Ubuntu/Debian i ma sudo, może
#    doinstalować podstawowe pakiety potrzebne do działania warstwy ROS2.
# 6. Weryfikuje importy krytycznych bibliotek.
# 7. Tworzy pomocniczy skrypt uruchomieniowy z aktywacją środowiska.
#
# Uwaga:
# - Część ROS2 / RTAB-Map zależy od dystrybucji systemu i uprawnień sudo.
# - Moduły standalone (markers, rgbd) nie wymagają ROS2.
# - Skrypt jest idempotentny: można uruchamiać wielokrotnie.
# ============================================================

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
ENV_NAME="robot_perception"
PYTHON_VERSION="3.11"
MINICONDA_DIR="${HOME}/miniconda3"
ROS_DISTRO_DEFAULT="${ROS_DISTRO:-humble}"
INSTALL_ROS_PACKAGES="${INSTALL_ROS_PACKAGES:-auto}"

log()  { printf '[SETUP][INFO] %s\n' "$*"; }
warn() { printf '[SETUP][WARN] %s\n' "$*"; }
err()  { printf '[SETUP][ERROR] %s\n' "$*" >&2; }

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
  curl -fsSL https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -o "${installer}"
  bash "${installer}" -b -p "${MINICONDA_DIR}"
  rm -f "${installer}"
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

  err "Nie udało się aktywować Conda."
  exit 1
}

create_or_update_conda_env() {
  log "Tworzenie / aktualizacja środowiska Conda: ${ENV_NAME}"

  if [[ -f "${PROJECT_ROOT}/environment.yml" ]]; then
    conda env update -n "${ENV_NAME}" -f "${PROJECT_ROOT}/environment.yml" --prune || \
    conda env create -n "${ENV_NAME}" -f "${PROJECT_ROOT}/environment.yml"
  else
    warn "Brak environment.yml. Tworzę środowisko minimalne ręcznie."
    conda create -y -n "${ENV_NAME}" "python=${PYTHON_VERSION}" pip
  fi

  conda activate "${ENV_NAME}"
  log "Aktywowane środowisko: ${ENV_NAME}"
}

install_python_dependencies() {
  log "Instalacja zależności Python..."
  python -m pip install --upgrade pip setuptools wheel

  if [[ -f "${PROJECT_ROOT}/requirements.txt" ]]; then
    # Instalacja zależności Python
    python -m pip install -r "${PROJECT_ROOT}/requirements.txt"

    # Dodatkowe pakiety używane przez projekt
    python -m pip install transforms3d

    # Torch 2.11.0 wymaga setuptools < 82
    python -m pip install "numpy==1.26.4" "setuptools<82" "transforms3d>=0.4.2"
              
    # Kontrola spójności środowiska
    python -m pip check || true
  fi

  # Dodatkowe zależności użyte w kodzie, które warto wymusić jawnie.
  python -m pip install transforms3d

  # tkinter zwykle jest pakietem systemowym, więc tylko informujemy.
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
    warn "Jeśli chcesz wymusić próbę, uruchom skrypt ręcznie z uprawnieniami root lub skonfiguruj sudo."
    return 0
  fi

  log "Próba instalacji pakietów systemowych ROS2 dla dystrybucji: ${distro}"
  sudo apt-get update
  sudo apt-get install -y \
    python3-tk \
    python3-colcon-common-extensions \
    "ros-${distro}-ros-base" \
    "ros-${distro}-tf2-ros" \
    "ros-${distro}-sensor-msgs-py" \
    "ros-${distro}-rtabmap-msgs" || {
      warn "Nie udało się zainstalować części pakietów ROS2. To może być normalne dla innej dystrybucji ROS / Ubuntu."
    }
}

source_ros_if_available() {
  local ros_setup
  if ros_setup="$(find_ros_setup)"; then
    # shellcheck disable=SC1090
    source "${ros_setup}"
    log "Załadowano środowisko ROS2 z: ${ros_setup}"
  else
    warn "Nie znaleziono /opt/ros/*/setup.bash. Część ROS2 może nie działać."
  fi
}

verify_ros_imports_if_available() {
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
  cat > "${helper}" <<EOF
#!/usr/bin/env bash
set -Eeuo pipefail
PROJECT_ROOT="${PROJECT_ROOT}"
ENV_NAME="${ENV_NAME}"
MINICONDA_DIR="${MINICONDA_DIR}"
ROS_SETUP="$(find_ros_setup || true)"

if command -v conda >/dev/null 2>&1; then
  eval "4(conda shell.bash hook)"
elif [[ -x "4{MINICONDA_DIR}/bin/conda" ]]; then
  eval "4(4{MINICONDA_DIR}/bin/conda shell.bash hook)"
else
  echo "[RUN][ERROR] Nie znaleziono conda." >&2
  exit 1
fi

conda activate "4{ENV_NAME}"

if [[ -n "4{ROS_SETUP}" && -f "4{ROS_SETUP}" ]]; then
  # shellcheck disable=SC1090
  source "4{ROS_SETUP}"
fi

cd "4{PROJECT_ROOT}"
exec "4@"
EOF
  chmod +x "${helper}"
  log "Utworzono pomocniczy skrypt uruchomieniowy: ${helper}"
}

print_summary() {
  cat <<EOF

[SETUP][INFO] ================================================
[SETUP][INFO] Środowisko projektu zostało przygotowane.
[SETUP][INFO] Katalog projektu: ${PROJECT_ROOT}
[SETUP][INFO] Środowisko Conda: ${ENV_NAME}
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
[SETUP][INFO] - GUI, perception, slam i rtabmap_bridge wymagają poprawnego środowiska ROS2.
[SETUP][INFO] ================================================
EOF
}

main() {
  log "Start konfiguracji środowiska dla projektu robot_perception"
  log "Katalog projektu: ${PROJECT_ROOT}"

  ensure_basic_tools
  install_miniconda_if_needed
  setup_conda_shell
  create_or_update_conda_env
  install_python_dependencies
  install_ros_system_packages_if_possible
  source_ros_if_available
  verify_ros_imports_if_available
  create_helper_run_script
  print_summary
}

main "$@"
