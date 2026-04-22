import io
import os
import numpy as np
from PIL import Image
from flask import Flask, request, jsonify
from flask_cors import CORS
import tensorflow as tf
from preprocess import preprocess_bytes
from class_names import CLASS_NAMES
from calories import get_calories
from detect import detect_foods, total_calories

MODEL_PATH = os.path.join(os.path.dirname(__file__), "keggle", "mealy_model.keras")
PORT = 5001
TOP_K = 5

app = Flask(__name__)
CORS(app)
model = None


def load_model():
    global model
    if model is None:
        print("[app] Loading model...")
        model = tf.keras.models.load_model(MODEL_PATH)
        print(f"[app] Ready — {len(CLASS_NAMES)} classes")


@app.before_request
def ensure_loaded():
    load_model()


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "model": "loaded" if model is not None else "not loaded",
        "classes": len(CLASS_NAMES),
        "port": PORT,
    })


@app.route("/predict", methods=["POST"])
def predict():
    if "file" not in request.files:
        return jsonify({"error": "no file field"}), 400
    data = request.files["file"].read()
    if not data:
        return jsonify({"error": "empty file"}), 400

    try:
        tensor = preprocess_bytes(data)
    except Exception as e:
        return jsonify({"error": f"decode failed: {e}"}), 400

    probs = model.predict(tensor, verbose=0)[0]
    top_idx = np.argsort(probs)[::-1][:TOP_K]
    top5 = [{"class": CLASS_NAMES[i], "confidence": float(probs[i])} for i in top_idx]

    return jsonify({
        "prediction": top5[0]["class"],
        "confidence": top5[0]["confidence"],
        "calories": get_calories(top5[0]["class"]),
        "top5": top5,
    })


@app.route("/detect", methods=["POST"])
def detect():
    if "file" not in request.files:
        return jsonify({"error": "no file field"}), 400
    data = request.files["file"].read()
    if not data:
        return jsonify({"error": "empty file"}), 400

    try:
        pil = Image.open(io.BytesIO(data)).convert("RGB")
        frame_rgb = np.array(pil)
    except Exception as e:
        return jsonify({"error": f"decode failed: {e}"}), 400

    detections = detect_foods(model, frame_rgb)
    kcal = total_calories(detections)

    return jsonify({
        "detections": detections,
        "total_calories": kcal,
        "count": len(detections),
    })


if __name__ == "__main__":
    load_model()
    print(f"[app] http://0.0.0.0:{PORT}")
    app.run(host="0.0.0.0", port=PORT, debug=False)
