# Mealy — webcam demo
# Opens the laptop camera and runs live food recognition in a desktop window
# using OpenCV. Press A to toggle auto-scan every 2 seconds, Q to quit.

import os
import time
import cv2
import numpy as np
import tensorflow as tf
from preprocess import preprocess_cv2_frame
from detect import detect_foods, total_calories, get_regions

MODEL_PATH = os.path.join(os.path.dirname(__file__), "keggle", "mealy_model.keras")
CAMERA_INDEX = 0
PREDICT_INTERVAL = 1.5
FONT = cv2.FONT_HERSHEY_SIMPLEX

ORANGE = (0, 115, 249)
AMBER  = (11, 158, 245)
GREEN  = (85, 197, 34)
WHITE  = (245, 245, 245)
MUTED  = (112, 113, 107)
BLACK  = (10, 10, 10)


def draw_region_box(frame, name, h, w):
    mh, mw = h // 2, w // 2
    boxes = {
        'full':         (0, 0, w, h),
        'top_left':     (0, 0, mw, mh),
        'top_right':    (mw, 0, w, mh),
        'bottom_left':  (0, mh, mw, h),
        'bottom_right': (mw, mh, w, h),
    }
    if name not in boxes:
        return
    x1, y1, x2, y2 = boxes[name]
    cv2.rectangle(frame, (x1+2, y1+2), (x2-2, y2-2), ORANGE, 1)


def draw_overlay(frame, detections, fps, auto_mode):
    h, w = frame.shape[:2]

    for d in detections:
        draw_region_box(frame, d['region'], h, w)

    # Bottom panel
    panel_h = min(80 + 22 * len(detections), 160)
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, h - panel_h), (w, h), BLACK, -1)
    frame = cv2.addWeighted(overlay, 0.75, frame, 0.25, 0)

    if detections:
        for i, d in enumerate(detections):
            label = d['class'].replace('_', ' ').title()
            conf  = int(d['confidence'] * 100)
            kcal  = d['calories']
            y = h - panel_h + 20 + i * 22
            cv2.putText(frame, f"{label}", (10, y), FONT, 0.45, WHITE, 1, cv2.LINE_AA)
            cv2.putText(frame, f"{conf}%", (180, y), FONT, 0.38, AMBER, 1, cv2.LINE_AA)
            cv2.putText(frame, f"{kcal} kcal", (225, y), FONT, 0.38, ORANGE, 1, cv2.LINE_AA)

        total = total_calories(detections)
        cv2.putText(frame, f"TOTAL: {total} kcal", (w - 200, h - 12), FONT, 0.5, ORANGE, 1, cv2.LINE_AA)
    else:
        cv2.putText(frame, "NO FOOD DETECTED", (10, h - panel_h + 24), FONT, 0.5, MUTED, 1, cv2.LINE_AA)

    cv2.putText(frame, "github.com/Kowsyke", (10, h - 4), FONT, 0.28, MUTED, 1, cv2.LINE_AA)

    # Top bar
    cv2.putText(frame, "MEALY", (10, 22), FONT, 0.6, ORANGE, 2, cv2.LINE_AA)
    mode_text = "AUTO" if auto_mode else "MANUAL"
    cv2.putText(frame, mode_text, (10, 40), FONT, 0.32, AMBER, 1, cv2.LINE_AA)
    cv2.putText(frame, f"FPS {fps:.0f}", (w - 85, 22), FONT, 0.45, GREEN, 1, cv2.LINE_AA)
    cv2.putText(frame, "Q:quit  A:auto", (w - 140, h - panel_h - 6), FONT, 0.32, MUTED, 1, cv2.LINE_AA)

    return frame


def main():
    print("[demo] Loading model...")
    model = tf.keras.models.load_model(MODEL_PATH)
    print("[demo] Model ready. Opening camera...")

    cap = cv2.VideoCapture(CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 854)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    if not cap.isOpened():
        print(f"[demo] Cannot open /dev/video{CAMERA_INDEX}")
        return

    print("[demo] Running. Press Q to quit, A to toggle auto-scan.")
    last_predict = 0.0
    last_detections = []
    prev_time = time.time()
    auto_mode = False

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[demo] Frame read failed.")
            break

        now = time.time()
        fps = 1.0 / max(now - prev_time, 1e-6)
        prev_time = now

        if auto_mode or (now - last_predict >= PREDICT_INTERVAL):
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            last_detections = detect_foods(model, rgb)
            last_predict = now

        frame = draw_overlay(frame, last_detections, fps, auto_mode)
        cv2.imshow("Mealy", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('a'):
            auto_mode = not auto_mode
            print(f"[demo] Auto-scan {'ON' if auto_mode else 'OFF'}")

    cap.release()
    cv2.destroyAllWindows()
    print("[demo] Done.")


if __name__ == "__main__":
    main()
