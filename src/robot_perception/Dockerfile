# syntax=docker/dockerfile:1.7

# Bazowy obraz Linux z Micromambą do szybkiego tworzenia środowisk Conda.
FROM mambaorg/micromamba:2.0.5

# Używamy basha z pipefail dla bezpieczniejszego wykonywania kroków builda.
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Konfiguracja podstawowych ścieżek roboczych obrazu.
ENV PROJECT_DIR=/workspace/robot_perception \
    ENV_NAME=robot_perception

WORKDIR ${PROJECT_DIR}

# Kopiujemy definicję środowiska Conda i listę zależności pip.
COPY src/robot_perception/environment.yml ./environment.yml
COPY src/robot_perception/requirements.txt ./requirements.txt

# Tworzymy lub aktualizujemy środowisko Conda.
# Jeśli środowisko już istnieje, używamy update --prune, aby utrzymać zgodność z YAML.
RUN micromamba env list | grep -q "^${ENV_NAME}[[:space:]]" \
    && micromamba run -n base conda env update -n ${ENV_NAME} -f environment.yml --prune \
    || micromamba run -n base conda env create -f environment.yml

# Instalujemy tylko te zależności pip, które nie są już pokryte przez environment.yml.
RUN python - <<'PY' > /tmp/pip_extra_requirements.txt
from __future__ import annotations

import pathlib


def normalize(name: str) -> str:
    return name.strip().split(';', 1)[0].split('[', 1)[0].split('=', 1)[0].split('<', 1)[0].split('>', 1)[0].strip().lower().replace('_', '-').replace('.', '-')


env_path = pathlib.Path('environment.yml')
req_path = pathlib.Path('requirements.txt')

covered = set()
lines = env_path.read_text(encoding='utf-8').splitlines()
in_pip_block = False
for raw in lines:
    line = raw.rstrip()
    stripped = line.strip()
    if not stripped or stripped.startswith('#'):
        continue
    if stripped.startswith('- pip:'):
        in_pip_block = True
        continue
    if in_pip_block:
        if line.startswith('      - '):
            covered.add(normalize(stripped[2:].strip()))
            continue
        in_pip_block = False
    if stripped.startswith('- '):
        covered.add(normalize(stripped[2:].strip()))

extras: list[str] = []
for raw in req_path.read_text(encoding='utf-8').splitlines():
    stripped = raw.strip()
    if not stripped or stripped.startswith('#'):
        continue
    if normalize(stripped) not in covered:
        extras.append(stripped)

pathlib.Path('/tmp/pip_extra_requirements.txt').write_text('\n'.join(extras) + ('\n' if extras else ''), encoding='utf-8')
print('\n'.join(extras))
PY

RUN if [[ -s /tmp/pip_extra_requirements.txt ]]; then \
      echo "Installing extra pip dependencies:" && cat /tmp/pip_extra_requirements.txt && \
      micromamba run -n ${ENV_NAME} pip install --no-cache-dir -r /tmp/pip_extra_requirements.txt; \
    else \
      echo "No additional pip dependencies required."; \
    fi

# Walidujemy kluczowe importy runtime, aby szybko wykryć problemy builda.
RUN micromamba run -n ${ENV_NAME} python - <<'PY'
import cv2
import numpy
import open3d
import pydantic
import pupil_apriltags
import transforms3d
import ultralytics

print('OK: imports validated for robot_perception environment')
PY

# Kopiujemy kod projektu po zbudowaniu środowiska, żeby poprawić cache warstw.
COPY src/robot_perception/ ./

# Domyślnie wykonujemy komendy wewnątrz środowiska Conda.
ENTRYPOINT ["micromamba", "run", "-n", "robot_perception"]
CMD ["python", "--version"]
