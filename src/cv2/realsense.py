# RealSense interface with graceful fallback
from __future__ import annotations

import numpy as np

try:
    import pyrealsense2 as rs
except Exception:  # pragma: no cover - depends on host environment
    rs = None


class RealSense:
    def __init__(self):
        self.available = False
        self.pipeline = None
        self.config = None
        self.profile = None
        self.align = None
        self.fx = self.fy = self.cx = self.cy = None

        if rs is None:
            return

        try:
            self.pipeline = rs.pipeline()
            self.config = rs.config()
            ctx = rs.context()
            if len(ctx.query_devices()) == 0:
                return
            self.config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
            self.config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
            self.profile = self.pipeline.start(self.config)
            self.align = rs.align(rs.stream.color)
            intr = self.profile.get_stream(rs.stream.color).as_video_stream_profile().get_intrinsics()
            self.fx, self.fy, self.cx, self.cy = intr.fx, intr.fy, intr.ppx, intr.ppy
            self.available = True
        except Exception:
            self.available = False
            self.pipeline = None
            self.profile = None
            self.align = None

    def get_frame(self):
        if not self.available or self.pipeline is None or self.align is None:
            return None, None
        frames = self.align.process(self.pipeline.wait_for_frames())
        color_frame = frames.get_color_frame()
        depth_frame = frames.get_depth_frame()
        if not color_frame or not depth_frame:
            return None, None
        color = np.asanyarray(color_frame.get_data())
        return color, depth_frame

    def deproject(self, x, y, depth):
        if not self.available or depth is None:
            return None
        z = float(depth.get_distance(int(x), int(y)))
        if z <= 0:
            return None
        X = (x - self.cx) / self.fx * z
        Y = (y - self.cy) / self.fy * z
        return np.array([X, Y, z], dtype=float)

    def stop(self):
        if self.pipeline is not None:
            try:
                self.pipeline.stop()
            except Exception:
                pass
