
import cv2
from ultralytics import YOLO
from realsense import RealSense
from world_map import WorldMap
from depth_projection import bbox_to_3d

rs = RealSense()
world = WorldMap()
model = YOLO("yolov8n.pt")

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret: break

    color, depth = (frame, None)
    if rs.available:
        color, depth = rs.get_frame()

    results = model(frame)[0]

    for box in results.boxes:
        bbox = box.xyxy.cpu().numpy()[0]

        if rs.available and depth:
            p = bbox_to_3d(bbox, depth, rs)
            if p is not None:
                pw = world.to_world(p)
                if pw is not None:
                    world.add(pw)

    cv2.imshow("v4 system", frame)
    if cv2.waitKey(1)&0xFF==ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
