import argparse

import cv2
from ultralytics import YOLO

from depth_projection import bbox_to_3d
from realsense import RealSense
from world_map import WorldMap


def draw_detection(frame, bbox, point_world=None):
    x1, y1, x2, y2 = map(int, bbox)
    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
    if point_world is not None:
        label = f"[{point_world[0]:.2f}, {point_world[1]:.2f}, {point_world[2]:.2f}]"
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--save-map", default=None, help="Path to output PLY file")
    parser.add_argument("--max-frames", type=int, default=None, help="Optional frame limit")
    parser.add_argument(
        "--no-display", action="store_true", help="Disable cv2.imshow for headless runs"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    rs = RealSense()
    world = WorldMap()
    model = YOLO("yolov8n.pt")

    cap = None
    if not rs.available:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            raise RuntimeError("No RealSense device and webcam 0 could not be opened")

    frame_count = 0
    try:
        while True:
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

            for box in results.boxes:
                bbox = box.xyxy.cpu().numpy()[0]
                point_world = None

                if rs.available and depth is not None:
                    point_camera = bbox_to_3d(bbox, depth, rs)
                    if point_camera is not None:
                        point_world = world.to_world(point_camera)
                        world.add(point_world)

                draw_detection(frame, bbox, point_world)

            frame_count += 1
            if not args.no_display:
                cv2.imshow("v4 system", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

            if args.max_frames is not None and frame_count >= args.max_frames:
                break
    finally:
        if cap is not None:
            cap.release()
        rs.stop()
        if not args.no_display:
            cv2.destroyAllWindows()

    if args.save_map:
        world.save_ply(args.save_map)
        print(f"Saved map to {args.save_map}")


if __name__ == "__main__":
    main()
