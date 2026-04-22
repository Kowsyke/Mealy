# Mealy

Point a camera at your food and Mealy tells you what it is.

Mealy is a food image classifier built with MobileNetV2 transfer learning on the Food-101 dataset. It recognises 101 food categories, returns a confidence score, and estimates calories per serving. There is a browser UI with a live camera feed, a terminal demo that runs on your webcam, and a REST API you can call from anything.

Built for CMS22202 Computer Vision and AI at Ravensbourne University London.

---

## How it works

A frame comes in from the webcam or an uploaded image. It gets resized to 224x224 and normalised. The model runs inference across five overlapping regions of the image, so it can spot more than one food in a single frame. Each detection above 25% confidence comes back with a label, a confidence score, and a calorie estimate.

The model is MobileNetV2 pretrained on ImageNet, fine-tuned on Food-101 using two-phase transfer learning. Training ran on Kaggle (P100 GPU, ~45 minutes). Final test accuracy is 37.6% across 101 classes. Random chance would be 1%, so the model is about 37x better than guessing.

---

## Getting started

```bash
git clone https://github.com/Kowsyke/Mealy.git
cd Mealy
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

The model weights are too large for git. Download `mealy_model.keras` from the Kaggle training run and drop it here:

```
keggle/mealy_model.keras
```

---

## Running it

**Start the API first.** Everything else depends on it.

```bash
venv_archive/bin/python3 app.py
```

The server starts on port 5001. The model loads on the first request (takes about 30 seconds on CPU).

**Open the browser UI:**

```bash
firefox ui/index.html
```

Allow camera access when prompted. Hit **Scan Frame** to classify what the camera sees, or toggle **Auto Scan** to keep classifying every two seconds.

**Run the terminal demo:**

```bash
venv_archive/bin/python3 demo.py
```

OpenCV overlay on your webcam feed. Press `A` to toggle auto-scan, `Q` to quit.

**Run evaluation:**

```bash
venv_archive/bin/python3 evaluate.py
```

---

## API

```
GET  /health   system status
POST /predict  single-region classification
POST /detect   multi-region detection (up to 4 foods per frame)
```

Example:

```bash
curl http://localhost:5001/health

curl -X POST http://localhost:5001/predict \
     -F "file=@pizza.jpg"
```

```json
{
  "prediction": "pizza",
  "confidence": 0.71,
  "calories": 285,
  "top5": [
    {"class": "pizza", "confidence": 0.71},
    {"class": "bruschetta", "confidence": 0.09}
  ]
}
```

---

## Results

| Metric | Value |
|--------|-------|
| Test accuracy | 37.6% |
| Test loss | 2.6215 |
| Classes | 101 |
| Training images | 11,099 |
| Random baseline | ~1% |

The main constraint was image resolution. The Kaggle training dataset stores images at 64x64 pixels, which get upsampled to 224x224. State of the art on full-resolution Food-101 reaches above 90%.

---

## Project structure

```
app.py            Flask API (port 5001)
demo.py           OpenCV webcam demo
detect.py         Multi-region inference engine
preprocess.py     Shared image preprocessing
class_names.py    101 Food-101 class labels
calories.py       Calorie estimates per class
evaluate.py       Metrics and confusion matrix
model.py          MobileNetV2 model definition
train.py          Local training script
ui/index.html     Browser UI
keggle/           Model weights (not in git)
food-101/         Dataset (not in git)
requirements.txt  Dependencies
```

---

## Tech stack

Python 3.13, TensorFlow 2.21, Keras 3.13, OpenCV 4.13, Flask 3.1, scikit-learn 1.8

---

*CMS22202 Computer Vision and AI, Level 5, Ravensbourne University London*
