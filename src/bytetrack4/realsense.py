
# RealSense interface
import pyrealsense2 as rs
import numpy as np

class RealSense:
    def __init__(self):
        self.pipeline = rs.pipeline()
        self.config = rs.config()
        ctx = rs.context()
        if len(ctx.query_devices()) == 0:
            self.available = False
            return
        self.available = True
        self.config.enable_stream(rs.stream.depth, 640,480, rs.format.z16,30)
        self.config.enable_stream(rs.stream.color,640,480, rs.format.bgr8,30)
        self.profile = self.pipeline.start(self.config)
        self.align = rs.align(rs.stream.color)
        intr = self.profile.get_stream(rs.stream.color)            .as_video_stream_profile().get_intrinsics()
        self.fx, self.fy, self.cx, self.cy = intr.fx, intr.fy, intr.ppx, intr.ppy

    def get_frame(self):
        frames = self.align.process(self.pipeline.wait_for_frames())
        return frames.get_color_frame(), frames.get_depth_frame()

    def deproject(self,x,y,depth):
        z = depth.get_distance(int(x),int(y))
        if z==0: return None
        X = (x-self.cx)/self.fx*z
        Y = (y-self.cy)/self.fy*z
        return np.array([X,Y,z])
