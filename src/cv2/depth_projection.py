import numpy as np


def bbox_to_3d(bbox, depth_frame, rs_device):
    """Convert 2D bbox into a 3D point using depth at bbox center.

    Returns a numpy vector [X, Y, Z] in camera coordinates, or None when
    conversion is not possible.
    """
    if bbox is None or depth_frame is None or rs_device is None:
        return None

    x1, y1, x2, y2 = bbox
    cx = int(round((x1 + x2) / 2.0))
    cy = int(round((y1 + y2) / 2.0))

    point = rs_device.deproject(cx, cy, depth_frame)
    if point is None:
        return None
    return np.asarray(point, dtype=float).reshape(3)
