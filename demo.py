# Mealy - food classifier
# webcam demo using OpenCV, sends frames to flask API and overlays predictions
import cv2
import time
import requests
import numpy as np

CONFIG = {
    "camera_index":  0,
    "api_url":       "http://127.0.0.1:5001/predict",
    "predict_every": 1.0,   # seconds between API calls
    "font":          cv2.FONT_HERSHEY_SIMPLEX,
    "frame_width":   640,
    "frame_height":  480,
}


def send_frame(frame: np.ndarray) -> dict | None:
    _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
    try:
        resp = requests.post(
            CONFIG["api_url"],
            files={"file": ("frame.jpg", buffer.tobytes(), "image/jpeg")},
            timeout=3,
        )
        if resp.status_code == 200:
            return resp.json()
    except requests.exceptions.RequestException:
        pass
    return None


def draw_overlay(frame: np.ndarray, result: dict | None, fps: float) -> np.ndarray:
    h, w = frame.shape[:2]
    # Semi-transparent background bar at bottom
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, h - 90), (w, h), (0, 0, 0), -1)
    frame = cv2.addWeighted(overlay, 0.5, frame, 0.5, 0)

    if result:
        label = result.get("class", "?").replace("_", " ").title()
        conf  = result.get("confidence", 0.0)
        cv2.putText(frame, f"{label}", (10, h - 55), CONFIG["font"], 0.9, (255, 255, 255), 2)
        cv2.putText(frame, f"{conf*100:.1f}%", (10, h - 20), CONFIG["font"], 0.7, (0, 255, 120), 2)
        # Top-5 in small text top-left
        top5 = result.get("top5", [])
        for i, item in enumerate(top5[1:4], start=2):
            cls  = item["class"].replace("_", " ").title()
            c    = item["confidence"]
            cv2.putText(frame, f"{i}. {cls} {c*100:.0f}%", (10, 20 + (i-2)*22),
                        CONFIG["font"], 0.45, (200, 200, 200), 1)
    else:
        cv2.putText(frame, "Waiting for prediction...", (10, h - 35),
                    CONFIG["font"], 0.6, (180, 180, 180), 1)

    cv2.putText(frame, f"FPS: {fps:.1f}", (w - 100, 25), CONFIG["font"], 0.6, (0, 220, 255), 2)
    cv2.putText(frame, "Press Q to quit", (w - 160, h - 10), CONFIG["font"], 0.45, (150, 150, 150), 1)
    return frame


def main():
    cap = cv2.VideoCapture(CONFIG["camera_index"])
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  CONFIG["frame_width"])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT,  CONFIG["frame_height"])

    if not cap.isOpened():
        print(f"[demo] Could not open /dev/video{CONFIG['camera_index']}")
        return

    print("[demo] Starting. Press Q to quit.")
    last_predict = 0.0
    last_result  = None
    prev_time    = time.time()

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[demo] Frame capture failed.")
            break

        # FPS
        now = time.time()
        fps = 1.0 / max(now - prev_time, 1e-6)
        prev_time = now

        # Predict on interval
        if now - last_predict >= CONFIG["predict_every"]:
            last_result  = send_frame(frame)
            last_predict = now

        frame = draw_overlay(frame, last_result, fps)
        cv2.imshow("Mealy - Food Recognition", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("[demo] Done.")


if __name__ == "__main__":
    main()
