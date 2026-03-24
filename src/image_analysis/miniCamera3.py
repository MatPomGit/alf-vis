import cv2
import time
import threading
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ===============================
# THREADED CAMERA
# ===============================
class ThreadedCamera:
    def __init__(self, source=0, width=640, height=480, fps=30):
        self.source = source
        self.width = width
        self.height = height
        self.fps = fps

        self.cap = cv2.VideoCapture(source, cv2.CAP_V4L2)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.cap.set(cv2.CAP_PROP_FPS, fps)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        if not self.cap.isOpened():
            raise RuntimeError(f"Cannot open camera {source}")

        self.frame = None
        self.running = True
        self.lock = threading.Lock()

        self.thread = threading.Thread(target=self.update, daemon=True)
        self.thread.start()

        logger.info("Camera started (threaded)")

    def update(self):
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                continue

            with self.lock:
                self.frame = frame

    def read(self):
        with self.lock:
            return None if self.frame is None else self.frame.copy()

    def release(self):
        self.running = False
        self.thread.join()
        self.cap.release()
        logger.info("Camera stopped")


# ===============================
# OVERLAY (lekki)
# ===============================
def draw_overlay(frame, fps):
    h, w = frame.shape[:2]
    font = cv2.FONT_HERSHEY_SIMPLEX
    fontScale = 0.6
    color = (0, 0, 255)
    thickness = 1

    timestamp = time.strftime("%H:%M:%S")

    # teksty (bez blendingu dla wydajności)
    cv2.putText(frame, f"{timestamp}", (10, 25),
                font, fontScale, color, thickness)

    cv2.putText(frame, f"{w}x{h}", (10, 50),
                font, fontScale, color, thickness)

    cv2.putText(frame, f"{fps:.1f} FPS", (10, 75),
                font, fontScale, color, thickness)

    return frame


# ===============================
# MAIN LOOP
# ===============================
if __name__ == "__main__":
    cam = ThreadedCamera(source=0, width=640, height=480, fps=30)

    prev_time = time.time()
    fps = 0.0

    frame_count = 0

    try:
        while True:
            frame = cam.read()
            if frame is None:
                continue

            # --- FPS ---
            now = time.time()
            dt = now - prev_time
            prev_time = now

            if dt > 0:
                fps = 0.9 * fps + 0.1 * (1.0 / dt)

            # --- overlay ---
            frame = draw_overlay(frame, fps)

            # --- show ---
            cv2.imshow("Camera (HP)", frame)

            # --- kontrola ---
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC
                break
            if key == ord('q'):  # ESC
                break

            frame_count += 1

    finally:
        cam.release()
        cv2.destroyAllWindows()