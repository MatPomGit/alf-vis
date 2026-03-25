"""Image analysis package for the Unitree G1 EDU robot.

The package intentionally avoids eager imports of submodules because several
features depend on optional native libraries (for example OpenCV/Open3D).
Import specific functionality directly from submodules, e.g.
`from image_analysis.detection import Detection`.
"""

__all__: list[str] = []
