import pyrealsense2 as rs
import numpy as np

class RealSense:
    def __init__(self):
        self.pipeline = rs.pipeline()
        self.config = rs.config()

        # sprawdź czy kamera istnieje
        ctx = rs.context()
        devices = ctx.query_devices()
        if len(devices) == 0:
            self.available = False
            return

        self.available = True

        self.config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
        self.config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

        self.profile = self.pipeline.start(self.config)

        self.align = rs.align(rs.stream.color)

        intr = self.profile.get_stream(rs.stream.color)\
            .as_video_stream_profile().get_intrinsics()

        self.fx = intr.fx
        self.fy = intr.fy
        self.cx = intr.ppx
        self.cy = intr.ppy

    def get_frame(self):
        frames = self.pipeline.wait_for_frames()
        frames = self.align.process(frames)

        depth = frames.get_depth_frame()
        color = frames.get_color_frame()

        if not depth or not color:
            return None, None

        depth_image = np.asanyarray(depth.get_data())
        color_image = np.asanyarray(color.get_data())

        return color_image, depth

    def deproject(self, x, y, depth_frame):
        z = depth_frame.get_distance(int(x), int(y))
        if z == 0:
            return None

        X = (x - self.cx) / self.fx * z
        Y = (y - self.cy) / self.fy * z

        return np.array([X, Y, z])