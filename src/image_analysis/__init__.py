"""Image analysis package for the Unitree G1 EDU robot.

The package intentionally avoids eager imports of submodules because several
features depend on optional native libraries (for example OpenCV/Open3D).
Import specific functionality directly from submodules, e.g.
`from image_analysis.detection import Detection`.
"""


__all__ = [
    "KalmanMultiObjectTracker",
    "TrackedObject",
]


def __getattr__(name: str) -> object:
    if name in {"KalmanMultiObjectTracker", "TrackedObject"}:
        from image_analysis.kalman_tracking import KalmanMultiObjectTracker, TrackedObject

        exports = {
            "KalmanMultiObjectTracker": KalmanMultiObjectTracker,
            "TrackedObject": TrackedObject,
        }
        return exports[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
