import argparse

import cv2
from ultralytics import YOLO

from depth_projection import bbox_to_3d
from realsense import RealSense
from tracker import SortTracker
from tracking_export import TrackingExporter
from world_map import WorldMap


def draw_detection(frame, tracked):
    x1, y1, x2, y2 = map(int, tracked.bbox)
    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
    label = f"ID {tracked.track_id} | {tracked.class_name} {tracked.confidence:.2f}"
    if tracked.world_point is not None:
        label += f" | [{tracked.world_point[0]:.2f}, {tracked.world_point[1]:.2f}, {tracked.world_point[2]:.2f}]"
    cv2.putText(
        frame,
        label,
        (x1, max(20, y1 - 8)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.45,
        (0, 255, 0),
        1,
        cv2.LINE_AA,
    )


def parse_args():
    parser = argparse.ArgumentParser(description="YOLO + RealSense + SORT-style tracking")
    parser.add_argument("--save-tracking", type=str, default=None, help="Path to CSV tracking export")
    parser.add_argument("--max-distance", type=float, default=60.0, help="Max centroid distance for assignment")
    parser.add_argument("--max-missing", type=int, default=10, help="How many missed frames to keep a track")
    parser.add_argument("--no-display", action="store_true", help="Disable OpenCV preview window")
    parser.add_argument("--max-frames", type=int, default=None, help="Optional limit for processed frames")
    return parser.parse_args()


def main():
    args = parse_args()

    rs = RealSense()
    world = WorldMap()
    tracker = SortTracker(max_distance=args.max_distance, max_missing=args.max_missing)
    exporter = TrackingExporter(args.save_tracking) if args.save_tracking else None
    model = YOLO("yolov8n.pt")

    cap = None
    if not rs.available:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            raise RuntimeError("No RealSense device and webcam 0 could not be opened")

    frame_idx = 0
    try:
        while True:
            if args.max_frames is not None and frame_idx >= args.max_frames:
                break

            if rs.available:
                color, depth = rs.get_frame()
                if color is None:
                    continue
                frame = color.copy()
            else:
                ret, frame = cap.read()
                if not ret:
                    break
                depth = None

            results = model(frame, verbose=False)[0]
            detections = []

            for box in results.boxes:
                bbox = box.xyxy.cpu().numpy()[0]
                class_id = int(box.cls.item())
                confidence = float(box.conf.item())
                class_name = model.names.get(class_id, str(class_id))
                world_point = None

                if rs.available and depth is not None:
                    point_camera = bbox_to_3d(bbox, depth, rs)
                    if point_camera is not None:
                        world_point = world.to_world(point_camera)
                        world.add(world_point)

                detections.append(
                    {
                        "bbox": bbox,
                        "class_id": class_id,
                        "class_name": class_name,
                        "confidence": confidence,
                        "world_point": world_point,
                    }
                )

            tracked_objects = tracker.update(detections)

            for tracked in tracked_objects:
                draw_detection(frame, tracked)
                if exporter is not None:
                    exporter.write(
                        frame_idx=frame_idx,
                        track_id=tracked.track_id,
                        class_id=tracked.class_id,
                        class_name=tracked.class_name,
                        confidence=tracked.confidence,
                        bbox=tracked.bbox,
                        world_point=tracked.world_point,
                    )

            if not args.no_display:
                cv2.imshow("v4 system", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

            frame_idx += 1
    finally:
        if exporter is not None:
            exporter.close()
        if cap is not None:
            cap.release()
        rs.stop()
        if not args.no_display:
            cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
