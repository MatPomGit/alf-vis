
import cv2
from ultralytics import YOLO
from tracker import ByteTracker

model = YOLO("yolov8n.pt")
tracker = ByteTracker()

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    results = model(frame)[0]

    detections = []
    for box in results.boxes:
        detections.append({
            "bbox": box.xyxy.cpu().numpy()[0],
            "score": float(box.conf),
            "cls": int(box.cls)
        })

    tracks = tracker.update(detections)

    for t in tracks:
        x1, y1, x2, y2 = map(int, t.bbox)
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0,255,0), 2)
        cv2.putText(frame, f"ID {t.id}", (x1, y1-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)

    cv2.imshow("Tracking", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
