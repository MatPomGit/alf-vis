from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Optional

from common.models import Pose3D, SlamStatus
from common.utils import ensure_dir


class RTABMapService:
    """Usługa integracji z RTAB-Map.

    W tej architekturze RTAB-Map jest traktowany jako zewnętrzny komponent ROS2.
    To jest podejście bardziej praktyczne produkcyjnie niż próba pełnego odwzorowania
    jego logiki we własnym kodzie Python.
    """

    def __init__(
        self,
        database_path: str,
        launch_package: str,
        launch_file: str,
    ) -> None:
        self.database_path = str(Path(database_path))
        self.launch_package = launch_package
        self.launch_file = launch_file
        self._process: Optional[subprocess.Popen] = None
        self._initialized = False

    def ensure_started(self) -> SlamStatus:
        """Uruchamia RTAB-Map, jeśli jeszcze nie działa."""
        if self._initialized:
            return SlamStatus(
                initialized=True,
                status="RUNNING",
                pose=Pose3D(x=0.0, y=0.0, z=0.0),
                map_point_count=0,
                database_path=self.database_path,
            )

        Path(self.database_path).parent.mkdir(parents=True, exist_ok=True)

        # TODO: dopasować argumenty launch do konkretnej konfiguracji RGB-D / stereo.
        # TODO: dodać monitoring procesu i retry policy.
        cmd = [
            "ros2",
            "launch",
            self.launch_package,
            self.launch_file,
            f"rtabmap_args:=--delete_db_on_start",
            f"database_path:={self.database_path}",
        ]

        self._process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        self._initialized = True

        return SlamStatus(
            initialized=True,
            status="INITIALIZED",
            pose=Pose3D(x=0.0, y=0.0, z=0.0),
            map_point_count=0,
            database_path=self.database_path,
        )

    def update(self) -> SlamStatus:
        """Zwraca aktualny stan SLAM.

        W praktyce dane powinny pochodzić z topiców RTAB-Map lub dedykowanego mostka.
        """
        if not self._initialized:
            raise RuntimeError("RTAB-Map nie został zainicjalizowany.")

        # TODO: odczyt pozy z topicu /tf, /odom lub topiców RTAB-Map.
        # TODO: odczyt liczby map points z topicu /mapData lub własnego agregatora.
        return SlamStatus(
            initialized=True,
            status="UPDATED",
            pose=Pose3D(x=2.4, y=0.1, z=0.0, yaw=0.03),
            map_point_count=520,
            database_path=self.database_path,
        )

    def shutdown(self) -> None:
        """Zamyka proces RTAB-Map, jeśli został uruchomiony przez aplikację."""
        if self._process is not None and self._process.poll() is None:
            self._process.terminate()
            self._process.wait(timeout=5)