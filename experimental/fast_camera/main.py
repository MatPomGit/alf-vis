"""Fast camera – minimal-latency real-time YOLO detection.

Optimisations applied
---------------------
* Capture and inference run in separate threads (producer/consumer queue).
* Frame queue is capped at 1 so stale frames are dropped automatically.
* YOLO runs on a half-resolution copy (``imgsz=320``) for lower latency.
* ``verbose=False`` suppresses Ultralytics console noise.
* OpenCV window update is decoupled from the capture/inference loop.

Usage
-----
    python experimental/fast_camera/main.py
    python experimental/fast_camera/main.py --device cuda:0 --imgsz 416
    python experimental/fast_camera/main.py --source video.mp4 --no-display
"""

from __future__ import annotations

import argparse
import queue
import threading
import time
from typing import Any

import cv2
from ultralytics import YOLO

# Label colour: red (BGR)
_LABEL_COLOR: tuple[int, int, int] = (0, 0, 255)
# Label font scale
_FONT_SCALE: float = 0.80
# Maximum frames kept in the queue between capture and inference
_QUEUE_MAXSIZE: int = 1


def _draw_results(frame: Any, result: Any) -> Any:
    """Overlay YOLO detections on *frame* with red labels."""
    names: dict[int, str] = result.names
    for box in result.boxes:
        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
        cls_id = int(box.cls[0])
        conf = float(box.conf[0])
        label = f"{names.get(cls_id, str(cls_id))} {conf:.2f}"

        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(
            frame,
            label,
            (x1, max(y1 - 6, 18)),
            cv2.FONT_HERSHEY_SIMPLEX,
            _FONT_SCALE,
            _LABEL_COLOR,
            2,
            cv2.LINE_AA,
        )
    return frame


def capture_loop(
    source: int | str,
    frame_queue: "queue.Queue[Any]",
    stop_event: threading.Event,
) -> None:
    """Continuously read frames from *source* and push them to *frame_queue*.

    Drops the oldest frame when the queue is full to avoid memory growth.
    """
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video source: {source!r}")

    # Request 30 fps if the source supports it
    cap.set(cv2.CAP_PROP_FPS, 30)

    while not stop_event.is_set():
        ret, frame = cap.read()
        if not ret:
            break
        # Non-blocking put – discard old frame if the consumer is slow
        if frame_queue.full():
            try:
                frame_queue.get_nowait()
            except queue.Empty:
                pass
        try:
            frame_queue.put_nowait(frame)
        except queue.Full:
            pass

    cap.release()


def inference_loop(
    model: YOLO,
    frame_queue: "queue.Queue[Any]",
    result_queue: "queue.Queue[Any]",
    stop_event: threading.Event,
    device: str,
    imgsz: int,
) -> None:
    """Run YOLO on every frame taken from *frame_queue*."""
    while not stop_event.is_set():
        try:
            frame = frame_queue.get(timeout=0.1)
        except queue.Empty:
            continue

        results = model(
            frame,
            verbose=False,
            device=device,
            imgsz=imgsz,
            half=False,
        )
        annotated = _draw_results(frame, results[0])

        # Keep only the latest result
        if result_queue.full():
            try:
                result_queue.get_nowait()
            except queue.Empty:
                pass
        try:
            result_queue.put_nowait(annotated)
        except queue.Full:
            pass


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Fast camera – minimal-latency real-time YOLO detection"
    )
    parser.add_argument(
        "--source",
        default=0,
        help="Camera index (int) or video file path (default: 0)",
    )
    parser.add_argument(
        "--model",
        default="yolov8n.pt",
        help="YOLO weights path or name (default: yolov8n.pt)",
    )
    parser.add_argument(
        "--device",
        default="cpu",
        help="Inference device: cpu / cuda:0 / mps (default: cpu)",
    )
    parser.add_argument(
        "--imgsz",
        type=int,
        default=320,
        help="YOLO inference image size in pixels (default: 320)",
    )
    parser.add_argument(
        "--no-display",
        action="store_true",
        help="Disable OpenCV preview window (useful for benchmarks)",
    )
    return parser.parse_args()


def main() -> None:
    """Run the fast-camera pipeline."""
    args = parse_args()

    # Convert source to int if it looks like a camera index
    source: int | str = args.source
    try:
        source = int(source)
    except (ValueError, TypeError):
        pass

    model = YOLO(args.model)

    frame_q: queue.Queue[Any] = queue.Queue(maxsize=_QUEUE_MAXSIZE)
    result_q: queue.Queue[Any] = queue.Queue(maxsize=_QUEUE_MAXSIZE)
    stop = threading.Event()

    cap_thread = threading.Thread(
        target=capture_loop, args=(source, frame_q, stop), daemon=True
    )
    inf_thread = threading.Thread(
        target=inference_loop,
        args=(model, frame_q, result_q, stop, args.device, args.imgsz),
        daemon=True,
    )

    cap_thread.start()
    inf_thread.start()

    fps_counter = 0
    fps_start = time.perf_counter()

    try:
        while True:
            try:
                annotated = result_q.get(timeout=0.5)
            except queue.Empty:
                if not cap_thread.is_alive():
                    break
                continue

            fps_counter += 1
            elapsed = time.perf_counter() - fps_start
            if elapsed >= 1.0:
                fps = fps_counter / elapsed
                fps_counter = 0
                fps_start = time.perf_counter()
                cv2.putText(
                    annotated,
                    f"FPS: {fps:.1f}",
                    (8, annotated.shape[0] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.65,
                    (255, 255, 0),
                    2,
                )

            if not args.no_display:
                cv2.imshow("Fast Camera", annotated)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
    finally:
        stop.set()
        cap_thread.join(timeout=2)
        inf_thread.join(timeout=2)
        if not args.no_display:
            cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
