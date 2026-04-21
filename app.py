# Mealy - food classifier
# flask API with /predict and /health endpoints, runs on port 5001
# developed with help from Claude AI
import os
import io
import numpy as np
from flask import Flask, request, jsonify
from PIL import Image
import tensorflow as tf
from preprocess import preprocess_pil
from load_data import load_class_names

CONFIG = {
    "model_path":  os.path.join(os.path.dirname(__file__), "mealy_model.keras"),
    "dataset_dir": os.path.join(os.path.dirname(__file__), "food-101"),
    "port":        5001,
    "top_k":       5,
}

app = Flask(__name__)
model = None
class_names = None


def load_model_once():
    global model, class_names
    if model is None:
        print("[app] Loading model...")
        model = tf.keras.models.load_model(CONFIG["model_path"])
        class_names = load_class_names(CONFIG["dataset_dir"])
        print(f"[app] model ready, {len(class_names)} classes")


@app.before_request
def ensure_model_loaded():
    load_model_once()


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "model_loaded": model is not None,
        "classes": len(class_names) if class_names else 0,
    })


@app.route("/predict", methods=["POST"])
def predict():
    if "file" not in request.files:
        return jsonify({"error": "No file field in request"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    try:
        pil_image = Image.open(io.BytesIO(file.read()))
    except Exception as e:
        return jsonify({"error": f"Could not decode image: {e}"}), 400

    tensor = preprocess_pil(pil_image)
    tensor = tf.expand_dims(tensor, 0)  # add batch dim

    probs = model.predict(tensor, verbose=0)[0]
    top_k_idx = np.argsort(probs)[::-1][:CONFIG["top_k"]]

    top5 = [
        {"class": class_names[i], "confidence": float(probs[i])}
        for i in top_k_idx
    ]

    return jsonify({
        "class":      top5[0]["class"],
        "confidence": top5[0]["confidence"],
        "top5":       top5,
    })


if __name__ == "__main__":
    load_model_once()
    print(f"[app] Starting on http://0.0.0.0:{CONFIG['port']}")
    app.run(host="0.0.0.0", port=CONFIG["port"], debug=False)
