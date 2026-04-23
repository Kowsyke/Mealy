# Mealy

Point a camera at your food and Mealy tells you what it is and how many calories it has.

Mealy is a food image classifier built with MobileNetV2 transfer learning. It recognises 101 food categories from Food-101 and 36 fruit and vegetable categories. It returns a confidence score and a calorie estimate per serving, shown live in the browser.

**Live demo:** https://56-228-34-22.sslip.io/mealy/
**Via Kowsite dashboard:** https://56-228-34-22.sslip.io → click MEALY in the sidebar

Built for CMS22202 Operating Systems & Cloud Computing at Ravensbourne University London.

---

## How it works

A frame is captured from the webcam and sent to a local Flask server. The server runs it through a MobileNetV2 model, filters results above 15% confidence, looks up calorie estimates, and returns JSON. The browser renders the results as live detection cards.

Two models run side by side:

- **Food model** — MobileNetV2 trained on Food-101 (101 classes, 37.6% test accuracy)
- **Fruit model** — MobileNetV2 fine-tuned on Fruits-360 (36 classes, 96.7% test accuracy)

**Combined mode** runs both models on the same frame, merging results across 137 total categories.

### Deployment architecture

```
Browser → HTTPS 443 → EC2 nginx → /mealy/ → SSH reverse tunnel → Fedora Flask (5001) → TensorFlow
```

The AI runs on a local Fedora machine. An SSH reverse tunnel exposes it through a cloud EC2 server. Nginx on EC2 routes HTTPS traffic to the right service. All three local processes (Flask API, SSH tunnel, system metrics agent) are managed as systemd user services that start automatically on login.

---

## Getting started (local)

```bash
git clone https://github.com/Kowsyke/Mealy.git
cd Mealy
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Model weights are not in git (too large). Download them and place here:

```
models/food_model.keras    — Food-101 model
models/fruit_model.keras   — Fruit/Veg model
```

---

## Running it

**Quickest — shell alias (if configured):**
```bash
mealy launch      # opens desktop app
mealy api start   # starts background API
mealy open        # open browser UI
```

**Background API + browser:**
```bash
./start_api.sh          # starts Flask in a tmux session (auto-restarts)
./start_api.sh status   # check it is running
./start_api.sh stop     # shut it down
```
Then open `http://localhost:5001` in a browser.

**Direct:**
```bash
venv_archive/bin/python3 app.py
```

**Desktop app (PyQt6 native window):**
```bash
venv_archive/bin/python3 launch.py
```

**Terminal demo (OpenCV overlay):**
```bash
venv_archive/bin/python3 demo.py
# Press A to toggle auto-scan, Q to quit
```

---

## Auto-start on login

```bash
systemctl --user enable mealy-api.service mealy-tunnel.service kowsite-agent.service
systemctl --user start  mealy-api.service mealy-tunnel.service kowsite-agent.service
```

---

## API endpoints

```
GET  /health              API and model status
POST /detect              Food-101 detection (image upload)
POST /detect_fruit        Fruit/veg detection
POST /detect_combined     Both models, merged results
```

```bash
curl https://56-228-34-22.sslip.io/mealy/health
curl -X POST https://56-228-34-22.sslip.io/mealy/detect -F "file=@plate.jpg"
```

```json
{
  "detections": [
    { "class": "pizza", "confidence": 0.71, "calories": 285 },
    { "class": "apple", "confidence": 0.88, "calories": 52 }
  ],
  "total_calories": 337,
  "model": "combined"
}
```

---

## Results

| Model | Classes | Accuracy |
|-------|---------|----------|
| Food-101 (MobileNetV2) | 101 | 37.6% |
| Fruit/Veg (fine-tuned) | 36 | 96.7% |

Random chance on 101 classes is ~1%. The food model is 37× better than chance.

---

## Project structure

```
app.py               Flask server — handles image uploads and returns predictions
model.py             Neural network definition — MobileNetV2 + classification head
train_optimized.py   Full-resolution two-phase training script for Food-101
train.py             Original training script (first iteration)
load_data.py         Data pipeline — loads, augments, and batches training images
preprocess.py        Image preprocessor — resize to 224×224, normalise to [0, 1]
detect.py            Inference engine — runs the model, filters by confidence
calories.py          Calorie lookup table for 101 food classes
fruit_calories.py    Calorie lookup table for 36 fruit/veg classes
class_names.py       Ordered list of 101 Food-101 category names
fruit_classes.py     Ordered list of 36 fruit/veg category names
evaluate.py          Runs the test set and prints accuracy and confusion matrix
demo.py              OpenCV webcam demo — runs in a terminal/desktop window
launch.py            PyQt6 desktop launcher — opens Mealy in a native app window
main.py              Simple entry point
start_api.sh         Shell script to start the API in a background tmux session
ui/index.html        Browser frontend — camera, scan button, detection cards, kcal total
requirements.txt     All Python dependencies, pinned for reproducibility
```

---

## Tech stack

Python 3.12 · TensorFlow 2.21 · Keras 3.13 · Flask 3.1 · PyQt6 · OpenCV 4.13 · scikit-learn 1.8

EC2 (Ubuntu) · nginx 1.24 · Let's Encrypt · systemd · SSH reverse tunnel

---

*CMS22202 Operating Systems & Cloud Computing — Ravensbourne University London*
