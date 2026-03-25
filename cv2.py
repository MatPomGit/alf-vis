"""Lightweight cv2 compatibility shim for headless test environments.

This module implements only the subset of OpenCV used by this repository's
unit tests. It is *not* a complete replacement for OpenCV.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

COLOR_BGR2GRAY = 6
COLOR_BGR2YCrCb = 36
CV_64F = np.float64
COLORMAP_JET = 2
INTER_LINEAR = 1
INTER_AREA = 3
IMWRITE_JPEG_QUALITY = 1
IMREAD_COLOR = 1
FONT_HERSHEY_SIMPLEX = 0
CAP_PROP_FRAME_WIDTH = 3
CAP_PROP_FRAME_HEIGHT = 4
CAP_PROP_FPS = 5
TERM_CRITERIA_EPS = 2
TERM_CRITERIA_MAX_ITER = 1
FILE_STORAGE_WRITE = 1
FILE_STORAGE_READ = 0
SOLVEPNP_IPPE_SQUARE = 7


class _FileNode:
    def __init__(self, value: Any) -> None:
        self._value = value

    def mat(self) -> np.ndarray | None:
        return self._value if isinstance(self._value, np.ndarray) else None

    def real(self) -> float:
        return float(self._value) if self._value is not None else 0.0


class FileStorage:
    def __init__(self, path: str, mode: int) -> None:
        self._path = Path(path)
        self._mode = mode
        self._data: dict[str, Any] = {}
        if mode == FILE_STORAGE_READ and self._path.exists():
            loaded = np.load(self._path, allow_pickle=True)
            self._data = {k: loaded[k].item() if loaded[k].shape == () else loaded[k] for k in loaded.files}

    def write(self, key: str, value: Any) -> None:
        self._data[key] = value

    def getNode(self, key: str) -> _FileNode:  # noqa: N802
        return _FileNode(self._data.get(key))

    def release(self) -> None:
        if self._mode == FILE_STORAGE_WRITE:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            with self._path.open("wb") as fh:
                np.savez(fh, **self._data)


class VideoCapture:
    def __init__(self, source: int | str, *_: Any) -> None:
        self.source = source
        self._opened = False

    def set(self, *_: Any) -> bool:
        return True

    def isOpened(self) -> bool:  # noqa: N802
        return self._opened

    def read(self) -> tuple[bool, np.ndarray]:
        return False, np.array([], dtype=np.uint8)

    def release(self) -> None:
        self._opened = False


def imread(path: str) -> np.ndarray | None:
    try:
        rgb = np.array(Image.open(path).convert("RGB"), dtype=np.uint8)
    except Exception:
        return None
    return rgb[..., ::-1]


def imwrite(path: str, image: np.ndarray) -> bool:
    arr = image[..., ::-1] if image.ndim == 3 and image.shape[2] == 3 else image
    Image.fromarray(arr).save(path)
    return True


def resize(image: np.ndarray, dsize: tuple[int, int], interpolation: int = INTER_LINEAR) -> np.ndarray:
    width, height = dsize
    mode = Image.BILINEAR if interpolation == INTER_LINEAR else Image.BOX
    if image.ndim == 2:
        return np.array(Image.fromarray(image).resize((width, height), resample=mode))
    pil = Image.fromarray(image[..., ::-1])
    out = np.array(pil.resize((width, height), resample=mode), dtype=np.uint8)
    return out[..., ::-1]


def cvtColor(image: np.ndarray, code: int) -> np.ndarray:
    if code == COLOR_BGR2GRAY:
        b, g, r = image[..., 0], image[..., 1], image[..., 2]
        return (0.114 * b + 0.587 * g + 0.299 * r).astype(np.uint8)
    if code == COLOR_BGR2YCrCb:
        b, g, r = image[..., 0].astype(np.float32), image[..., 1].astype(np.float32), image[..., 2].astype(np.float32)
        y = (0.114 * b + 0.587 * g + 0.299 * r)
        cr = 128 + 0.5 * (r - y)
        cb = 128 + 0.5 * (b - y)
        out = np.stack([y, cr, cb], axis=-1)
        return np.clip(out, 0, 255).astype(np.uint8)
    raise ValueError(f"Unsupported conversion code: {code}")


def GaussianBlur(image: np.ndarray, ksize: tuple[int, int], sigma_x: float) -> np.ndarray:  # noqa: ARG001
    k = np.array([[1, 4, 6, 4, 1]], dtype=np.float32)
    k = (k.T @ k) / 256.0
    pad = ksize[0] // 2
    padded = np.pad(image, pad, mode="edge")
    out = np.zeros_like(image, dtype=np.float32)
    for y in range(image.shape[0]):
        for x in range(image.shape[1]):
            patch = padded[y:y + ksize[0], x:x + ksize[1]]
            out[y, x] = float(np.sum(patch * k))
    return out.astype(image.dtype)


def Laplacian(image: np.ndarray, ddepth: Any) -> np.ndarray:  # noqa: ARG001
    kernel = np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]], dtype=np.float32)
    padded = np.pad(image.astype(np.float32), 1, mode="edge")
    out = np.zeros_like(image, dtype=np.float32)
    for y in range(image.shape[0]):
        for x in range(image.shape[1]):
            out[y, x] = float(np.sum(padded[y:y + 3, x:x + 3] * kernel))
    return out.astype(np.float64)


def applyColorMap(gray: np.ndarray, colormap: int = COLORMAP_JET) -> np.ndarray:  # noqa: ARG001
    g = gray.astype(np.float32) / 255.0
    r = np.clip(1.5 - np.abs(4 * g - 3), 0, 1)
    gch = np.clip(1.5 - np.abs(4 * g - 2), 0, 1)
    b = np.clip(1.5 - np.abs(4 * g - 1), 0, 1)
    return (np.stack([b, gch, r], axis=-1) * 255).astype(np.uint8)


def putText(image: np.ndarray, *_: Any, **__: Any) -> np.ndarray:
    return image


def arrowedLine(image: np.ndarray, pt1: tuple[int, int], pt2: tuple[int, int], color: tuple[int, int, int], thickness: int, tipLength: float = 0.1) -> np.ndarray:  # noqa: ARG001,N803
    x1, y1 = pt1
    x2, y2 = pt2
    n = max(abs(x2 - x1), abs(y2 - y1), 1)
    for i in range(n + 1):
        t = i / n
        x = int(round(x1 + (x2 - x1) * t))
        y = int(round(y1 + (y2 - y1) * t))
        if 0 <= y < image.shape[0] and 0 <= x < image.shape[1]:
            image[max(0, y - thickness + 1):y + thickness, max(0, x - thickness + 1):x + thickness] = color
    return image


def imencode(ext: str, image: np.ndarray, params: list[int] | None = None) -> tuple[bool, np.ndarray]:
    quality = 80
    if params and len(params) >= 2 and params[0] == IMWRITE_JPEG_QUALITY:
        quality = int(params[1])
    arr = image[..., ::-1] if image.ndim == 3 and image.shape[2] == 3 else image
    buff = io.BytesIO()
    Image.fromarray(arr).save(buff, format="JPEG" if ext.lower() == ".jpg" else "PNG", quality=quality)
    data = np.frombuffer(buff.getvalue(), dtype=np.uint8)
    return True, data


def waitKey(delay: int) -> int:  # noqa: N802, ARG001
    return -1


def imshow(*_: Any) -> None:
    return None


def destroyAllWindows() -> None:
    return None


def findChessboardCorners(*_: Any) -> tuple[bool, None]:
    return False, None


def cornerSubPix(image: np.ndarray, corners: np.ndarray, *_: Any) -> np.ndarray:  # noqa: ARG001
    return corners


def calibrateCamera(obj_points: list[np.ndarray], img_points: list[np.ndarray], image_size: tuple[int, int], *_: Any) -> tuple[float, np.ndarray, np.ndarray, list[np.ndarray], list[np.ndarray]]:  # noqa: ARG001
    k = np.array([[500.0, 0.0, image_size[0] / 2], [0.0, 500.0, image_size[1] / 2], [0.0, 0.0, 1.0]], dtype=np.float64)
    d = np.zeros((1, 5), dtype=np.float64)
    rvecs = [np.zeros((3, 1), dtype=np.float64) for _ in img_points]
    tvecs = [np.zeros((3, 1), dtype=np.float64) for _ in img_points]
    return 0.5, k, d, rvecs, tvecs


def undistort(image: np.ndarray, *_: Any) -> np.ndarray:
    return image.copy()


def Rodrigues(src: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    vec = np.asarray(src, dtype=np.float64).reshape(-1)
    theta = np.linalg.norm(vec)
    if theta < 1e-12:
        return np.eye(3, dtype=np.float64), np.zeros((9, 3), dtype=np.float64)
    k = vec / theta
    kx, ky, kz = k
    K = np.array([[0, -kz, ky], [kz, 0, -kx], [-ky, kx, 0]], dtype=np.float64)
    r = np.eye(3) + np.sin(theta) * K + (1 - np.cos(theta)) * (K @ K)
    return r, np.zeros((9, 3), dtype=np.float64)


def solvePnP(object_points: np.ndarray, image_points: np.ndarray, camera_matrix: np.ndarray, dist_coeffs: np.ndarray, flags: int = SOLVEPNP_IPPE_SQUARE) -> tuple[bool, np.ndarray, np.ndarray]:  # noqa: ARG001
    _ = object_points, dist_coeffs, flags
    mean_x = float(np.mean(image_points[:, 0]))
    mean_y = float(np.mean(image_points[:, 1]))
    fx, fy = float(camera_matrix[0, 0]), float(camera_matrix[1, 1])
    cx, cy = float(camera_matrix[0, 2]), float(camera_matrix[1, 2])
    z = 1.0
    tvec = np.array([[(mean_x - cx) * z / fx], [(mean_y - cy) * z / fy], [z]], dtype=np.float64)
    rvec = np.zeros((3, 1), dtype=np.float64)
    return True, rvec, tvec


def projectPoints(object_points: np.ndarray, rvec: np.ndarray, tvec: np.ndarray, camera_matrix: np.ndarray, dist_coeffs: np.ndarray) -> tuple[np.ndarray, None]:  # noqa: ARG001
    rot, _ = Rodrigues(rvec)
    pts = object_points.reshape(-1, 3).astype(np.float64)
    cam = (rot @ pts.T).T + np.asarray(tvec, dtype=np.float64).reshape(1, 3)
    z = np.where(np.abs(cam[:, 2]) < 1e-9, 1e-9, cam[:, 2])
    x = camera_matrix[0, 0] * cam[:, 0] / z + camera_matrix[0, 2]
    y = camera_matrix[1, 1] * cam[:, 1] / z + camera_matrix[1, 2]
    projected = np.stack([x, y], axis=-1).reshape(-1, 1, 2)
    return projected.astype(np.float32), None


class QRCodeDetector:
    def detectAndDecodeMulti(self, image: np.ndarray) -> tuple[bool, list[str], None, None]:  # noqa: ARG002
        return False, [], None, None


class _ArucoDetector:
    def __init__(self, *_: Any) -> None:
        pass

    def detectMarkers(self, image: np.ndarray) -> tuple[list[np.ndarray], None, list[np.ndarray]]:  # noqa: ARG002
        return [], None, []


class _ArucoModule:
    DICT_4X4_50 = 0

    @staticmethod
    def getPredefinedDictionary(dictionary_id: int) -> int:
        return dictionary_id

    @staticmethod
    def DetectorParameters() -> object:  # noqa: N802
        return object()

    ArucoDetector = _ArucoDetector


aruco = _ArucoModule()
