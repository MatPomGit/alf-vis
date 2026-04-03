"""Camera calibration utilities using chessboard patterns.

Implements camera calibration based on Zhang's method (OpenCV implementation).
A calibrated camera provides an intrinsic matrix ``K`` and distortion
coefficients ``D`` that allow accurate 3D reconstruction, pose estimation, and
lens-distortion correction.

Calibration workflow
--------------------
1. Print or display a chessboard pattern of known dimensions.
2. Capture 15-30 images of the pattern from different angles and distances.
3. Call :func:`find_chessboard_corners` on each image to detect inner corners.
4. Collect results and call :func:`calibrate_camera` to compute ``K`` and ``D``.
5. Persist the result with :func:`save_calibration`.
6. At runtime, load with :func:`load_calibration` and correct frames with
   :func:`undistort_image`.

Implementation notes:
    - ``cv2.findChessboardCorners`` + ``cv2.cornerSubPix`` for sub-pixel accuracy.
    - ``cv2.calibrateCamera`` for intrinsics + distortion.
    - ``cv2.stereoCalibrate`` for stereo rigs (not yet implemented - see TODO).
    - Aim for RMS reprojection error < 0.5 px; > 1.0 px usually means
        poor image quality or too few views.
    - Calibration files are stored as YAML using ``cv2.FileStorage``.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

# Default chessboard pattern used in the Unitree G1 EDU calibration kit.
DEFAULT_BOARD_COLS: int = 9  # inner corners along the horizontal axis
DEFAULT_BOARD_ROWS: int = 6  # inner corners along the vertical axis
DEFAULT_SQUARE_SIZE_M: float = 0.025  # square side length in metres


@dataclass
class CalibrationResult:
    """Result of a camera calibration procedure.

    Attributes:
        camera_matrix: Intrinsic matrix ``K`` with shape ``(3, 3)``,
            dtype ``float64``.  Encodes focal lengths ``(fx, fy)`` and
            principal point ``(cx, cy)``.
        dist_coeffs: Distortion coefficients array with shape ``(1, 5)`` or
            ``(1, 14)`` depending on the distortion model, dtype ``float64``.
        rms_error: Root-mean-square reprojection error in pixels.
            Values below **0.5 px** are considered good calibration.
        image_size: ``(width, height)`` of the images used for calibration.
        rvecs: Per-view rotation vectors (list of ``(3, 1)`` arrays).
        tvecs: Per-view translation vectors (list of ``(3, 1)`` arrays).
    """

    camera_matrix: np.ndarray
    dist_coeffs: np.ndarray
    rms_error: float
    image_size: tuple[int, int]
    rvecs: list[np.ndarray] = field(default_factory=list)
    tvecs: list[np.ndarray] = field(default_factory=list)


def find_chessboard_corners(
    image: np.ndarray,
    board_size: tuple[int, int] = (DEFAULT_BOARD_COLS, DEFAULT_BOARD_ROWS),
    *,
    refine: bool = True,
) -> tuple[bool, np.ndarray | None]:
    """Detect inner chessboard corners in *image*.

    Converts to greyscale if needed, then calls ``cv2.findChessboardCorners``.
    When *refine* is ``True``, sub-pixel accuracy is achieved with
    ``cv2.cornerSubPix``.

    Args:
        image: BGR or greyscale ``uint8`` image array.
        board_size: ``(cols, rows)`` - number of **inner** corners along each
            axis of the chessboard.
        refine: If ``True``, refine corner positions to sub-pixel accuracy.

    Returns:
        Tuple ``(found, corners)`` where *found* is ``True`` when all corners
        were detected and *corners* is an array of shape ``(N, 1, 2)`` with
        ``float32`` pixel coordinates.  When *found* is ``False``, *corners*
        is ``None``.

    Raises:
        TypeError: If *image* is not a ``np.ndarray``.
        ValueError: If *image* is not a 2-D or 3-D uint8 array.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(f"Expected np.ndarray, got {type(image).__name__}")
    if image.dtype != np.uint8:
        raise ValueError(f"Expected uint8 image, got dtype={image.dtype}")

    import cv2

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image

    found, corners = cv2.findChessboardCorners(gray, board_size, None)
    if not found:
        logger.debug("Chessboard corners not found (board_size=%s).", board_size)
        return False, None

    if refine and corners is not None:
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 1e-3)
        corners = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)

    logger.debug("Found %d chessboard corners (board_size=%s).", len(corners), board_size)
    return True, corners


def calibrate_camera(
    all_corners: list[np.ndarray],
    image_size: tuple[int, int],
    board_size: tuple[int, int] = (DEFAULT_BOARD_COLS, DEFAULT_BOARD_ROWS),
    square_size_m: float = DEFAULT_SQUARE_SIZE_M,
) -> CalibrationResult:
    """Compute intrinsic parameters from a set of chessboard views.

    Args:
        all_corners: List of corner arrays returned by
            :func:`find_chessboard_corners` (one entry per calibration image).
            Each array has shape ``(N, 1, 2)`` with dtype ``float32``.
        image_size: ``(width, height)`` of the calibration images in pixels.
        board_size: ``(cols, rows)`` - number of inner corners.
        square_size_m: Physical side length of one chessboard square in metres.

    Returns:
        :class:`CalibrationResult` containing the camera matrix, distortion
        coefficients, and per-view extrinsics.

    Raises:
        ValueError: If *all_corners* is empty or if the calibration fails.
    """
    if not all_corners:
        raise ValueError("all_corners must contain at least one view.")

    cols, rows = board_size
    objp = np.zeros((cols * rows, 3), dtype=np.float32)
    objp[:, :2] = np.mgrid[0:cols, 0:rows].T.reshape(-1, 2) * square_size_m

    obj_points = [objp] * len(all_corners)

    import cv2

    rms, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.calibrateCamera(
        obj_points,
        all_corners,
        image_size,
        None,
        None,  # type: ignore[call-overload]
    )

    logger.info("Calibration complete: RMS reprojection error = %.4f px", rms)
    if rms > 1.0:
        logger.warning(
            "High reprojection error (%.4f px > 1.0 px). Consider recapturing calibration images.",
            rms,
        )

    return CalibrationResult(
        camera_matrix=camera_matrix,
        dist_coeffs=dist_coeffs,
        rms_error=float(rms),
        image_size=image_size,
        rvecs=list(rvecs),
        tvecs=list(tvecs),
    )


def save_calibration(result: CalibrationResult, path: str | Path) -> None:
    """Persist a calibration result to a YAML file.

    The file is written using ``cv2.FileStorage`` so it can be read back by
    both Python and C++ OpenCV code.

    Args:
        result: Calibration result to save.
        path: Destination file path.  Parent directories are created if they
            do not yet exist.

    Raises:
        IOError: If the file cannot be written.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    import cv2

    fs = cv2.FileStorage(str(path), cv2.FILE_STORAGE_WRITE)
    fs.write("camera_matrix", result.camera_matrix)
    fs.write("dist_coeffs", result.dist_coeffs)
    fs.write("rms_error", result.rms_error)
    fs.write("image_width", result.image_size[0])
    fs.write("image_height", result.image_size[1])
    fs.release()

    logger.info("Calibration saved to '%s'.", path)


def load_calibration(path: str | Path) -> CalibrationResult:
    """Load a calibration result from a YAML file.

    Args:
        path: Path to a YAML file previously saved by :func:`save_calibration`.

    Returns:
        :class:`CalibrationResult` with the stored parameters.

    Raises:
        FileNotFoundError: If *path* does not exist.
        ValueError: If the file does not contain expected calibration keys.
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Calibration file not found: {path}")

    import cv2

    fs = cv2.FileStorage(str(path), cv2.FILE_STORAGE_READ)
    camera_matrix = fs.getNode("camera_matrix").mat()
    dist_coeffs = fs.getNode("dist_coeffs").mat()
    rms_error = fs.getNode("rms_error").real()
    width = int(fs.getNode("image_width").real())
    height = int(fs.getNode("image_height").real())
    fs.release()

    if camera_matrix is None or dist_coeffs is None:
        raise ValueError(f"Invalid calibration file: missing keys in '{path}'")

    logger.info("Calibration loaded from '%s' (RMS=%.4f px).", path, rms_error)
    return CalibrationResult(
        camera_matrix=camera_matrix,
        dist_coeffs=dist_coeffs,
        rms_error=rms_error,
        image_size=(width, height),
    )


def undistort_image(
    image: np.ndarray,
    calibration: CalibrationResult,
) -> np.ndarray:
    """Remove lens distortion from *image* using calibration parameters.

    Uses ``cv2.undistort`` with the stored camera matrix and distortion
    coefficients.

    Args:
        image: Distorted BGR ``uint8`` image array.
        calibration: Camera calibration result from :func:`calibrate_camera`
            or :func:`load_calibration`.

    Returns:
        Undistorted image array with the same shape and dtype as *image*.

    Raises:
        TypeError: If *image* is not a ``np.ndarray``.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError(f"Expected np.ndarray, got {type(image).__name__}")

    import cv2

    return cv2.undistort(
        image,
        calibration.camera_matrix,
        calibration.dist_coeffs,
    )


def compute_reprojection_error(
    result: CalibrationResult,
    board_size: tuple[int, int] = (DEFAULT_BOARD_COLS, DEFAULT_BOARD_ROWS),
    square_size_m: float = DEFAULT_SQUARE_SIZE_M,
) -> list[float]:
    """Compute per-view reprojection errors from a calibration result.

    Re-projects the 3D object points using the stored extrinsics and returns
    the RMS reprojection error for each calibration view.

    Args:
        result: Calibration result containing ``rvecs`` and ``tvecs``.
        board_size: ``(cols, rows)`` - number of inner corners.
        square_size_m: Physical side length of one chessboard square in metres.

    Returns:
        List of per-view RMS reprojection errors (one float per view).
        Empty list if *result* has no extrinsic vectors stored.
        Entries are :data:`math.nan` when per-view image points are not
        available in *result* (see TODO in implementation).
    """
    if not result.rvecs or not result.tvecs:
        return []

    cols, rows = board_size
    objp = np.zeros((cols * rows, 3), dtype=np.float32)
    objp[:, :2] = np.mgrid[0:cols, 0:rows].T.reshape(-1, 2) * square_size_m

    errors: list[float] = []
    import cv2

    for rvec, tvec in zip(result.rvecs, result.tvecs, strict=True):
        projected, _ = cv2.projectPoints(
            objp,
            rvec,
            tvec,
            result.camera_matrix,
            result.dist_coeffs,
        )
        # image_points are not stored in CalibrationResult, so per-view error
        # cannot be computed here.  Return NaN to signal unavailability.
        # TODO(#calibration): Store image_points in CalibrationResult and use
        # them here for accurate per-view error computation.
        _ = projected
        errors.append(float("nan"))

    return errors
