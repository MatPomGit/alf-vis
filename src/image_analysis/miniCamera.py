# Skrypt do sprawdzania kamery bez dodatkowych rzeczy
import cv2
import time
import os
os.environ["QT_QPA_FONTDIR"] = "/usr/share/fonts"

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    cv2.imshow("test", frame)
    if cv2.waitKey(1) == 27:
        break

cap.release()


if __name__ == "__main__":
    config = CameraConfig(source=0)

    with UnitreeCamera(config) as cam:
        prev_time = time.time()
        fps = 0.0

        for frame in cam.stream_rgb():

            # --- FPS ---
            current_time = time.time()
            dt = current_time - prev_time
            prev_time = current_time
            if dt > 0:
                fps = 0.9 * fps + 0.1 * (1.0 / dt)  # wygładzenie

            # --- Timestamp ---
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

            # --- Rozdzielczość ---
            h, w = frame.shape[:2]
            resolution_text = f"{w}x{h}"

            # --- Teksty ---
            text1 = f"Time: {timestamp}"
            text2 = f"Res: {resolution_text}"
            text3 = f"FPS: {fps:.1f}"

            # --- Rysowanie (lewy górny róg) ---
            cv2.putText(frame, text1, (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            cv2.putText(frame, text2, (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            cv2.putText(frame, text3, (10, 90),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            # --- Wyświetlanie ---
            cv2.imshow("Camera", frame)

            if cv2.waitKey(1) & 0xFF == 27:
                break

    cv2.destroyAllWindows()