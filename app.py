"""
Mealy API — port 5001
TensorFlow is imported lazily inside load_*_model() so Flask starts immediately.
Models load on the first request that needs them.
"""
import io
import os
import numpy as np
from PIL import Image
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# Non-TF imports — fast
from class_names import CLASS_NAMES
from calories import get_calories
from fruit_classes import FRUIT_CLASSES
from fruit_calories import get_fruit_calories

BASE_DIR       = os.path.dirname(os.path.abspath(__file__))
FOOD_MODEL_PATH = os.path.join(BASE_DIR, "keggle", "mealy_model.keras")
FRUIT_MODEL_PATH = os.path.join(BASE_DIR, "keggle", "fruit_model.keras")
UI_DIR          = os.path.join(BASE_DIR, "ui")
PORT  = 5001
TOP_K = 5
COMBINED_MAX = 6   # more slots when merging two databases

app = Flask(__name__)
CORS(app)

food_model  = None
fruit_model = None


# ── lazy model loading ────────────────────────────────────────────────────
def load_food_model():
    global food_model
    if food_model is None:
        import tensorflow as tf
        print("[app] Loading food model…")
        food_model = tf.keras.models.load_model(FOOD_MODEL_PATH)
        print(f"[app] Food model ready — {len(CLASS_NAMES)} classes")


def load_fruit_model():
    global fruit_model
    if fruit_model is None:
        import tensorflow as tf
        print("[app] Loading fruit model…")
        fruit_model = tf.keras.models.load_model(FRUIT_MODEL_PATH)
        print(f"[app] Fruit model ready — {len(FRUIT_CLASSES)} classes")


# ── serve UI ──────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return send_from_directory(UI_DIR, "index.html")

@app.route("/<path:filename>")
def ui_static(filename):
    return send_from_directory(UI_DIR, filename)


# ── health (no model load) ────────────────────────────────────────────────
@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "food_model":   "loaded" if food_model  is not None else "not loaded",
        "fruit_model":  "loaded" if fruit_model is not None else "not loaded",
        "food_classes":  len(CLASS_NAMES),
        "fruit_classes": len(FRUIT_CLASSES),
        "port": PORT,
    })


# ── food endpoints ────────────────────────────────────────────────────────
@app.route("/predict", methods=["POST"])
def predict():
    load_food_model()
    from preprocess import preprocess_bytes
    data = _read_file(request)
    if isinstance(data, tuple): return data
    try:
        tensor = preprocess_bytes(data)
    except Exception as e:
        return jsonify({"error": f"decode failed: {e}"}), 400
    probs   = food_model.predict(tensor, verbose=0)[0]
    top_idx = np.argsort(probs)[::-1][:TOP_K]
    top5    = [{"class": CLASS_NAMES[i], "confidence": float(probs[i])} for i in top_idx]
    return jsonify({
        "prediction": top5[0]["class"],
        "confidence": top5[0]["confidence"],
        "calories":   get_calories(top5[0]["class"]),
        "top5": top5, "model": "food",
    })


@app.route("/detect", methods=["POST"])
def detect():
    load_food_model()
    from detect import detect_foods, total_calories
    frame_rgb = _decode_image(request)
    if isinstance(frame_rgb, tuple): return frame_rgb
    dets = detect_foods(food_model, frame_rgb, CLASS_NAMES, get_calories)
    return jsonify({"detections": dets, "total_calories": total_calories(dets),
                    "count": len(dets), "model": "food"})


# ── fruit endpoints ───────────────────────────────────────────────────────
@app.route("/predict_fruit", methods=["POST"])
def predict_fruit():
    load_fruit_model()
    from preprocess import preprocess_bytes
    data = _read_file(request)
    if isinstance(data, tuple): return data
    try:
        tensor = preprocess_bytes(data)
    except Exception as e:
        return jsonify({"error": f"decode failed: {e}"}), 400
    probs   = fruit_model.predict(tensor, verbose=0)[0]
    top_idx = np.argsort(probs)[::-1][:TOP_K]
    top5    = [{"class": FRUIT_CLASSES[i], "confidence": float(probs[i])} for i in top_idx]
    return jsonify({
        "prediction": top5[0]["class"],
        "confidence": top5[0]["confidence"],
        "calories":   get_fruit_calories(top5[0]["class"]),
        "top5": top5, "model": "fruit",
    })


@app.route("/detect_fruit", methods=["POST"])
def detect_fruit():
    load_fruit_model()
    from detect import detect_foods, total_calories
    frame_rgb = _decode_image(request)
    if isinstance(frame_rgb, tuple): return frame_rgb
    dets = detect_foods(fruit_model, frame_rgb, FRUIT_CLASSES, get_fruit_calories)
    return jsonify({"detections": dets, "total_calories": total_calories(dets),
                    "count": len(dets), "model": "fruit"})


# ── combined endpoint — runs both models, merges results ──────────────────
@app.route("/detect_combined", methods=["POST"])
def detect_combined():
    load_food_model()
    load_fruit_model()
    from detect import detect_foods, total_calories

    frame_rgb = _decode_image(request)
    if isinstance(frame_rgb, tuple): return frame_rgb

    food_dets  = detect_foods(food_model,  frame_rgb, CLASS_NAMES,   get_calories)
    fruit_dets = detect_foods(fruit_model, frame_rgb, FRUIT_CLASSES, get_fruit_calories)

    # Merge: deduplicate by class name, keep highest confidence entry
    merged = {}
    for d in food_dets + fruit_dets:
        name = d["class"]
        if name not in merged or d["confidence"] > merged[name]["confidence"]:
            merged[name] = dict(d)

    all_dets = sorted(merged.values(), key=lambda x: x["confidence"], reverse=True)
    all_dets = all_dets[:COMBINED_MAX]

    return jsonify({
        "detections":     all_dets,
        "total_calories": total_calories(all_dets),
        "count":          len(all_dets),
        "food_count":     len(food_dets),
        "fruit_count":    len(fruit_dets),
        "model":          "combined",
    })


# ── helpers ───────────────────────────────────────────────────────────────
def _read_file(req):
    if "file" not in req.files:
        return jsonify({"error": "no file field"}), 400
    data = req.files["file"].read()
    if not data:
        return jsonify({"error": "empty file"}), 400
    return data


def _decode_image(req):
    data = _read_file(req)
    if isinstance(data, tuple): return data
    try:
        pil = Image.open(io.BytesIO(data)).convert("RGB")
        return np.array(pil)
    except Exception as e:
        return jsonify({"error": f"decode failed: {e}"}), 400


if __name__ == "__main__":
    print(f"[app] Starting — models load on first request that needs them")
    print(f"[app] UI → http://localhost:{PORT}")
    app.run(host="0.0.0.0", port=PORT, debug=False)
