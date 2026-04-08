from __future__ import annotations
import argparse
from pathlib import Path
from common.calibration import calibrate_camera_from_chessboard, save_camera_calibration


def main() -> None:
    """Kalibruje kamerę na podstawie zdjęć szachownicy i zapisuje YAML."""
    parser = argparse.ArgumentParser()
    parser.add_argument("images_dir")
    parser.add_argument("--cols", type=int, default=9)
    parser.add_argument("--rows", type=int, default=6)
    parser.add_argument("--square-size", type=float, default=0.024)
    parser.add_argument("--output", default="config/camera_calibration.yaml")
    args = parser.parse_args()

    image_paths = sorted(str(p) for p in Path(args.images_dir).glob("*.png"))
    calibration = calibrate_camera_from_chessboard(
        image_paths=image_paths,
        board_size=(args.cols, args.rows),
        square_size_m=args.square_size,
    )
    save_camera_calibration(calibration, args.output)
    print(calibration.model_dump())


if __name__ == "__main__":
    main()