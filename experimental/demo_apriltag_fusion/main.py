
import cv2
import numpy as np
import csv
from ultralytics import YOLO
from pupil_apriltags import Detector
from tracker import ByteTracker, compute_R

fx, fy, cx, cy = 600, 600, 320, 240
K = np.array([[fx,0,cx],[0,fy,cy],[0,0,1]])

model = YOLO("yolov8n.pt")
tracker = ByteTracker()

detector = Detector(families="tag36h11")

cap = cv2.VideoCapture(0)

log = open("trajectory.csv","w",newline="")
writer = csv.writer(log)
writer.writerow(["frame","id","x","y","z"])

frame_id = 0

def fuse_tags(tags):
    if not tags:
        return None
    pos = np.zeros(3)
    wsum = 0
    for t in tags:
        w = t.decision_margin
        pos += w * t.pose_t.flatten()
        wsum += w
    return pos/wsum

while True:
    ret, frame = cap.read()
    if not ret:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    tags = detector.detect(gray, estimate_tag_pose=True,
                           camera_params=(fx,fy,cx,cy),
                           tag_size=0.16)

    world_pos = fuse_tags(tags)

    detections = []
    results = model(frame)[0]

    for box in results.boxes:
        bbox = box.xyxy.cpu().numpy()[0]
        conf = float(box.conf)
        detections.append({
            "bbox": bbox,
            "score": conf,
            "cls": int(box.cls),
            "conf": conf
        })

    tracks = tracker.update(detections)

    for t in tracks:
        if world_pos is not None:
            t.position_3d = world_pos
            t.kf.R = compute_R(0.9)
            t.kf.predict()
            t.kf.update(t.position_3d)

            x,y,z = t.kf.get_position()
            writer.writerow([frame_id, t.id, x, y, z])

            cv2.putText(frame, f"{t.id}: {x:.2f},{y:.2f}",
                        (10,30+20*t.id), 0, 0.8, (0, 0, 255), 2)

    cv2.imshow("Tracking 3D", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

    frame_id += 1

cap.release()
log.close()
cv2.destroyAllWindows()
