"""Simple smoke test that does not require a RealSense device.

It verifies that:
- the RealSense wrapper degrades gracefully when pyrealsense2/device is absent,
- the world map can accumulate points,
- the PLY export works.
"""

from pathlib import Path

import numpy as np

try:  # Support both `python -m src.cv2.test_no_realsense` and script mode.
    from .realsense import RealSense
    from .world_map import WorldMap
except ImportError:
    from realsense import RealSense
    from world_map import WorldMap


def run_test(output_path="test_outputs/world_map_test.ply"):
    rs = RealSense()
    world = WorldMap(max_points=16)

    # Add a small synthetic point cloud in front of the camera.
    synthetic_points = [
        np.array([0.0, 0.0, 1.0]),
        np.array([0.1, 0.0, 1.0]),
        np.array([0.0, 0.1, 1.0]),
        np.array([0.1, 0.1, 1.1]),
    ]
    for point in synthetic_points:
        world.add(world.to_world(point))

    output = Path(output_path)
    world.save_ply(str(output))

    print(f"RealSense available: {rs.available}")
    print(f"Saved {len(world.points)} points to {output.resolve()}")
    return output


if __name__ == "__main__":
    run_test()
