import csv
from pathlib import Path
from typing import Optional, Sequence

import numpy as np


class TrackingExporter:
    def __init__(self, csv_path: str):
        self.csv_path = Path(csv_path)
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)
        self.file = self.csv_path.open("w", newline="", encoding="utf-8")
        self.writer = csv.writer(self.file)
        self.writer.writerow(
            [
                "frame_idx",
                "track_id",
                "class_id",
                "class_name",
                "confidence",
                "x1",
                "y1",
                "x2",
                "y2",
                "world_x",
                "world_y",
                "world_z",
            ]
        )

    def write(
        self,
        frame_idx: int,
        track_id: int,
        class_id: int,
        class_name: str,
        confidence: float,
        bbox: Sequence[float],
        world_point: Optional[np.ndarray],
    ) -> None:
        x1, y1, x2, y2 = [float(v) for v in bbox]
        if world_point is None:
            world_values = ["", "", ""]
        else:
            world_values = [float(world_point[0]), float(world_point[1]), float(world_point[2])]
        self.writer.writerow(
            [
                int(frame_idx),
                int(track_id),
                int(class_id),
                class_name,
                float(confidence),
                x1,
                y1,
                x2,
                y2,
                *world_values,
            ]
        )
        self.file.flush()

    def close(self) -> None:
        if not self.file.closed:
            self.file.close()
