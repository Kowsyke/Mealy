import os
import io
import numpy as np
from flask import Flask, request, jsonify
import tensorflow as tf
from preprocess import preprocess_bytes
from class_names import CLASS_NAMES

CONFIG = {
    "model_path": os.path.join(os.path.dirname(__file__), "keggle", "mealy_model.keras"),
    "port": 5001,
    "top_k": 5,
}

app = Flask(__name__)
model = None


def load_model_once():
    global model
    if model is None:
        print("[app] Loading model...")
        model = tf.keras.models.load_model(CONFIG["model_path"])
        print(f"[app] Model ready — {len(CLASS_NAMES)} classes")


@app.before_request
def ensure_loaded():
    load_model_once()


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "model": "loaded" if model is not None else "not loaded",
        "classes": len(CLASS_NAMES),
    })


@app.route("/predict", methods=["POST"])
def predict():
    if "file" not in request.files:
        return jsonify({"error": "No file field in request"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    try:
        tensor = preprocess_bytes(file.read())
    except Exception as e:
        return jsonify({"error": f"Could not decode image: {e}"}), 400

    probs = model.predict(tensor, verbose=0)[0]
    top_idx = np.argsort(probs)[::-1][:CONFIG["top_k"]]
    top5 = [{"class": CLASS_NAMES[i], "confidence": float(probs[i])} for i in top_idx]

    return jsonify({
        "prediction": top5[0]["class"],
        "confidence": top5[0]["confidence"],
        "top5": top5,
    })


if __name__ == "__main__":
    load_model_once()
    print(f"[app] Starting on http://0.0.0.0:{CONFIG['port']}")
    app.run(host="0.0.0.0", port=CONFIG["port"], debug=False)
