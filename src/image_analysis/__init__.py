"""Image analysis package for the Unitree G1 EDU robot.

The package intentionally avoids eager imports of submodules because several
features depend on optional native libraries (for example OpenCV/Open3D).
Import specific functionality directly from submodules, e.g.
`from image_analysis.detection import Detection`.
"""

__all__ = [
    "KalmanMultiObjectTracker",
    "TrackedObject",
    "get_array_backend",
    "is_pyscript_runtime",
    "run_pywebio_app",
    "to_numpy",
]


def __getattr__(name: str) -> object:
    if name in {"KalmanMultiObjectTracker", "TrackedObject"}:
        from image_analysis.kalman_tracking import KalmanMultiObjectTracker, TrackedObject

        exports = {
            "KalmanMultiObjectTracker": KalmanMultiObjectTracker,
            "TrackedObject": TrackedObject,
        }
        return exports[name]
    if name in {"get_array_backend", "is_pyscript_runtime", "to_numpy"}:
        from image_analysis.array_backend import (
            get_array_backend,
            is_pyscript_runtime,
            to_numpy,
        )

        exports = {
            "get_array_backend": get_array_backend,
            "is_pyscript_runtime": is_pyscript_runtime,
            "to_numpy": to_numpy,
        }
        return exports[name]
    if name == "run_pywebio_app":
        from image_analysis.pywebio_app import run_pywebio_app

        return run_pywebio_app
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
