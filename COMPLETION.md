# Mealy Project - Completion Session
# Read this entire file before doing anything.
# Work from /home/K/Storage/Projects/Mealy/

---

## CONTEXT

Mealy is a food image classifier built with MobileNetV2 transfer learning
on the Food-101 dataset. It is a university submission for CMS22202
Computer Vision and AI at Ravensbourne University London. Deadline: Week 12.

Training is complete. The model is saved. This session completes everything
needed for submission.

## TRAINING RESULTS (use these exact numbers everywhere)

- Architecture: MobileNetV2 (ImageNet pretrained) + classification head
- Dataset: Food-101 via Kaggle HDF5 format (kmader/food41)
  - Train: 11,099 images across 101 classes (~110 per class)
  - Test: 1,000 images across 101 classes
- Phase 1: frozen base, head only, 20 epochs, lr=1e-3
- Phase 2: top 30 layers unfrozen, 20 epochs, lr=1e-5
- Final test accuracy: 37.6%
- Final test loss: 2.6215
- Model file: /home/K/Storage/Projects/Mealy/keggle/mealy_model.keras
- Training curves: /home/K/Storage/Projects/Mealy/keggle/training_curves.png

## ENVIRONMENT

- Machine: ASUS X510UAR (hyperspace), Fedora 43, KDE Plasma 6, Wayland
- Python venv: venv_archive/ — always use full path venv_archive/bin/python3
  Never use system python3 or pip directly, shebang is stale
- Port 5000: OCCUPIED by fedora-controller.service
- Use port 5001 for all Mealy Flask work
- Webcam: Logitech C920 at /dev/video0
- Project root: /home/K/Storage/Projects/Mealy/

---

## YOUR TASKS — DO IN ORDER, DO NOT SKIP

---

### STEP 1 — Verify model loads

```bash
cd /home/K/Storage/Projects/Mealy
venv_archive/bin/python3 -c "
import tensorflow as tf
model = tf.keras.models.load_model('keggle/mealy_model.keras')
print('OK - input:', model.input_shape, 'output:', model.output_shape)
"
```

If this fails, list what is in keggle/ and report. Do not proceed past Step 1
if the model does not load.

---

### STEP 2 — preprocess.py

Write /home/K/Storage/Projects/Mealy/preprocess.py

Preprocessing must match training exactly:
- Resize to 224x224
- Cast to float32
- Divide by 255 (range 0-1)
- Nothing else — EfficientNet preprocessing was NOT used

Three functions:
- preprocess_array(img_array) — takes numpy array, returns (224,224,3) float32
- preprocess_pil(pil_image) — takes PIL Image, returns (224,224,3) float32
- preprocess_bytes(image_bytes) — takes raw bytes, returns (1,224,224,3) float32

---

### STEP 3 — class_names.py

Write /home/K/Storage/Projects/Mealy/class_names.py

The model was trained on kmader/food41 HDF5 data. The label order comes
from argmax on the category one-hot vectors, which follows the order in
the category_names field of the h5 file.

Try to extract actual names from a local h5 file first:
```python
import h5py
files = [
    'keggle/food_c101_n10099_r64x64x3.h5',
    'food-101/meta/classes.txt',
]
# try each, extract class names, verify count is 101
```

If no h5 file is available locally, use standard Food-101 alphabetical order
(apple_pie through waffles, 101 classes). Write the list into CLASS_NAMES.

Verify: len(CLASS_NAMES) must equal 101.

---

### STEP 4 — evaluate.py

Write /home/K/Storage/Projects/Mealy/evaluate.py

Load model. Load test data. Compute metrics. Save report.

If h5 test file is available at keggle/ or food-101/:
- Load X_test, y_test from h5
- Run model.predict
- Compute accuracy, precision, recall, F1 (weighted) with sklearn
- Plot confusion matrix (top 20 most confused classes)
- Save confusion_matrix.png

If no test data is available locally:
- Report the known numbers (37.6% accuracy, 2.6215 loss)
- Note that full evaluation ran on Kaggle during training

Write claude/metrics_report.md with all results regardless.

Run it after writing:
```bash
venv_archive/bin/python3 evaluate.py
```

---

### STEP 5 — app.py

Write /home/K/Storage/Projects/Mealy/app.py

Flask API on port 5001. Load model once at startup.

Routes:
- GET /health
  returns: {"status": "ok", "model": "loaded", "classes": 101}

- POST /predict (multipart file upload)
  returns: {
    "prediction": "pizza",
    "confidence": 0.847,
    "top5": [{"class": "pizza", "confidence": 0.847}, ...]
  }

Use preprocess_bytes() from preprocess.py.
Use CLASS_NAMES from class_names.py.

Test after writing:
```bash
# terminal 1
venv_archive/bin/python3 app.py &

# wait 3 seconds then test
sleep 3
curl http://localhost:5001/health
```

---

### STEP 6 — demo.py

Write /home/K/Storage/Projects/Mealy/demo.py

OpenCV webcam demo:
- Open /dev/video0
- Capture frame every loop iteration
- Every 1.5 seconds, send frame as JPEG bytes to POST /localhost:5001/predict
- Overlay prediction label + confidence on frame with cv2.putText
- Show FPS counter top-right corner
- Show last prediction time bottom-left corner
- Press Q to quit

Do not crash if the Flask server is not running — catch connection errors
and show "server offline" on screen instead.

---

### STEP 7 — report.md

Write /home/K/Storage/Projects/Mealy/report.md

Requirements:
- Exactly 500 words (count carefully, aim for 498-502)
- Sounds like a Level 5 student wrote it
- No em dashes, no "robust", no "seamlessly", no "comprehensive",
  no "leverage", no "utilize"
- Short sentences, mix of technical and plain English

Structure:
1. Objectives (what Mealy does and why it matters)
2. System Requirements (data, libraries, compute)
3. Design (pipeline description, MobileNetV2 choice rationale)
4. Implementation (two-phase training, augmentation, decisions made)
5. Results (37.6% accuracy, what it means, limitations)

Include at the end:

GitHub: https://github.com/Kowsyke/Mealy

References:
Geron, A., 2019. Hands-on Machine Learning with Scikit-Learn, Keras, and
TensorFlow. 2nd ed. Sebastopol: O'Reilly Media.

Sandler, M., Howard, A., Zhu, M., Zhmoginov, A. and Chen, L., 2018.
MobileNetV2: Inverted Residuals and Linear Bottlenecks. Proceedings of
the IEEE Conference on Computer Vision and Pattern Recognition,
pp.4510-4520.

Bossard, L., Guillaumin, M. and Van Gool, L., 2014. Food-101 - Mining
Discriminative Components with Random Forests. European Conference on
Computer Vision, pp.446-461.

---

### STEP 8 — README.md

Write /home/K/Storage/Projects/Mealy/README.md

Cover:
- One paragraph on what Mealy is
- Setup instructions (venv, pip install -r requirements.txt)
- How to run app.py (port 5001)
- How to run demo.py (requires app.py running)
- How to run evaluate.py
- Note: model weights not in repo, place mealy_model.keras in keggle/
- Academic context: CMS22202 at Ravensbourne University London

---

### STEP 9 — requirements.txt

Update /home/K/Storage/Projects/Mealy/requirements.txt to include:

tensorflow>=2.13.0
keras>=2.13.0
numpy>=1.24.0
Pillow>=10.0.0
matplotlib>=3.7.0
scikit-learn>=1.3.0
opencv-python>=4.8.0
flask>=3.0.0
h5py>=3.8.0
requests>=2.28.0

---

### STEP 10 — CHANGELOG and presentation outline

Add new entry at top of claude/CHANGELOG.md:

## [2026-04-22] Session 2 — Completion
### Done
- (list what you completed this session)
### Results
- Final test accuracy: 37.6%
- Model: keggle/mealy_model.keras
### Next
- Git push via git_push_prompt.md
- Present to tutor

Write claude/presentation_outline.md with 15 slides:
1. Title: Mealy — Food Image Classification
2. Problem statement and motivation
3. Dataset: Food-101, 101 classes, HDF5 format, class distribution
4. Full pipeline: data loading > preprocessing > augmentation > model > evaluate > deploy
5. MobileNetV2 architecture: layers, parameter count, why this model
6. Transfer learning: why pretrained weights, ImageNet connection
7. Training setup: two phases, epochs, learning rates, callbacks
8. Training curves: show training_curves.png, explain what the curves show
9. Results: 37.6% accuracy, loss 2.6215, baseline comparison (random = 1%)
10. Confusion matrix: which classes are hardest, why
11. Flask API: /predict endpoint, show curl output
12. Live demo: webcam feed with overlay
13. Ethics: dataset bias, privacy implications of food tracking, transparency
14. Limitations and future work: more data, higher resolution, EfficientNet
15. References

---

## RULES

1. Work through steps in order. Do not skip any.
2. Do not touch port 5000. Mealy uses port 5001 only.
3. Preprocessing is divide by 255 only. Nothing else.
4. Use venv_archive/bin/python3 for everything.
5. Write human-sounding code. No # === dividers. Short docstrings.
6. Do not run git push. That is a separate step.
7. Update CHANGELOG.md when done.

Go.
