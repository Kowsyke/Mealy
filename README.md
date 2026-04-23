# Mealy

Point a camera at your food and Mealy tells you what it is.

Mealy is a food image classifier built with MobileNetV2 transfer learning. It recognises 101 food categories (Food-101) and 36 fruit and vegetable categories (Fruits dataset). It returns a confidence score and a calorie estimate per serving. There is a browser UI with a live camera feed, a desktop app launcher, a terminal demo, and a REST API.

Built for CMS22202 Computer Vision and AI at Ravensbourne University London.

---

## How it works

A frame comes in from the webcam or an uploaded image. It gets resized to 224x224 and normalised. The model runs inference across five overlapping regions of the image, so it can spot more than one food in a single frame. Each detection above 25% confidence comes back with a label, a confidence score, and a calorie estimate.

Two models are available:

- **Food model**: MobileNetV2 trained on Food-101 (101 classes, 37.6% test accuracy). Training ran on Kaggle (P100 GPU). Accuracy is constrained by the source images being 64x64 pixels upsampled to 224x224.
- **Fruit model**: MobileNetV2 trained on a real-world Fruits dataset (36 classes, 96.7% test accuracy). Trained locally on CPU in 48 minutes at native image resolution.

**Combined mode** runs both models on the same frame and merges results by class name, covering 137 total classes.

---

## Getting started

```bash
git clone https://github.com/Kowsyke/Mealy.git
cd Mealy
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Model weights are not in git (too large). Drop them here:

```
keggle/mealy_model.keras    — Food-101 model
keggle/fruit_model.keras    — Fruit/Veg model
```

---

## Running it

### Option A — mealy shell alias (quickest)

Add the mealy function to your shell (already done if you cloned from the main repo):

```bash
mealy launch      # opens desktop app
mealy api start   # starts background API (tmux, 36h)
mealy api status  # check if running
mealy api logs    # tail live log
mealy api stop    # kill background session
mealy open        # open browser UI
```

### Option B — background API + browser

```bash
./start_api.sh          # start (stays alive 36h in background tmux session)
./start_api.sh status   # check
./start_api.sh logs     # live log
./start_api.sh stop     # kill
```

Then open `http://localhost:5001` in any browser.

### Option C — desktop app (native window)

```bash
venv_archive/bin/python3 launch.py
```

Starts Flask and opens a native PyQt6 window. Camera permissions auto-granted.

### Option D — manual

```bash
venv_archive/bin/python3 app.py
```

Server starts on port 5001. Models load on first request.

### Terminal demo

```bash
venv_archive/bin/python3 demo.py
```

OpenCV overlay on webcam feed. Press `A` to toggle auto-scan, `Q` to quit.

---

## Auto-start on login (systemd)

A user systemd service is included:

```bash
systemctl --user enable mealy-api.service
systemctl --user start mealy-api.service
systemctl --user status mealy-api.service
```

The API then starts automatically whenever you log in.

---

## API

```
GET  /health              system status, both model states
POST /predict             single-region Food-101 classification
POST /detect              multi-region food detection (up to 4 results)
POST /predict_fruit       single-region Fruit/Veg classification
POST /detect_fruit        multi-region fruit/veg detection
POST /detect_combined     both models, merged results (up to 6)
```

Example:

```bash
curl http://localhost:5001/health

curl -X POST http://localhost:5001/detect_combined \
     -F "file=@plate.jpg"
```

```json
{
  "detections": [
    {"class": "pizza",  "confidence": 0.71, "calories": 285},
    {"class": "apple",  "confidence": 0.88, "calories": 52}
  ],
  "total_calories": 337,
  "food_count": 1,
  "fruit_count": 1,
  "model": "combined"
}
```

---

## Results

| Model | Classes | Test accuracy | Test loss |
|-------|---------|---------------|-----------|
| Food-101 (Kaggle HDF5) | 101 | 37.6% | 2.6215 |
| Fruit/Veg (JPEG, full-res) | 36 | 96.7% | 0.1342 |

Random chance on 101 classes is 1%. The food model is 37x better than random. The fruit model accuracy reflects what is achievable with full-resolution training data.

---

## Project structure

```
app.py                 Flask API (port 5001)
launch.py              Desktop app (PyQt6 native window)
start_api.sh           Background API manager (tmux, 36h)
demo.py                OpenCV webcam demo
detect.py              Multi-region inference engine
preprocess.py          Shared image preprocessing
class_names.py         101 Food-101 class labels
calories.py            Calorie estimates per food class
fruit_classes.py       36 Fruit/Veg class labels
fruit_calories.py      Calorie estimates per fruit class
train_optimized.py     Full-res Food-101 JPEG retrain script
evaluate.py            Metrics and confusion matrix
model.py               MobileNetV2 model definition
ui/index.html          Browser UI (glassmorphism)
keggle/                Model weights (not in git)
food-101/              Food-101 dataset (not in git)
Fruit_dataset/         Fruit training pipeline
```

---

## Tech stack

Python 3.13, TensorFlow 2.21, Keras 3.13, OpenCV 4.13, Flask 3.1, PyQt6, scikit-learn 1.8

---

*CMS22202 Computer Vision and AI, Level 5, Ravensbourne University London*
