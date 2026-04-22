# Mealy

Food image classification system built with MobileNetV2 transfer learning on the Food-101 dataset. Mealy takes a photograph of food and returns the category name with a confidence score across 101 classes. It was built as the assessed artefact for CMS22202 Computer Vision and AI at Ravensbourne University London.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Model weights** are not included in this repository (file size). Download `mealy_model.keras` from the Kaggle training run and place it at:

```
keggle/mealy_model.keras
```

## Running the API

```bash
python3 app.py
```

The Flask API starts on port 5001. Test it:

```bash
curl http://localhost:5001/health
curl -X POST http://localhost:5001/predict -F "file=@your_food_image.jpg"
```

The `/predict` endpoint returns JSON:

```json
{
  "prediction": "pizza",
  "confidence": 0.847,
  "top5": [{"class": "pizza", "confidence": 0.847}, ...]
}
```

## Running the Webcam Demo

The API must be running first. Then:

```bash
python3 demo.py
```

Opens the webcam at `/dev/video0`, classifies frames every second, and overlays the result on screen. Press **Q** to quit.

## Running Evaluation

```bash
python3 evaluate.py
```

If the HDF5 test file (`keggle/food_c101_n10099_r64x64x3.h5`) is present, it runs full metrics and generates a confusion matrix. Otherwise it writes the known results from the Kaggle training run to `claude/metrics_report.md`.

**Known results:** 37.6% test accuracy, 2.6215 test loss.

## Project Structure

```
Mealy/
├── app.py              # Flask API (/predict, /health) — port 5001
├── demo.py             # OpenCV webcam demo
├── evaluate.py         # Metrics, confusion matrix
├── preprocess.py       # Shared preprocessing (224×224, /255)
├── class_names.py      # 101 Food-101 class labels
├── load_data.py        # tf.data pipeline for Food-101
├── model.py            # MobileNetV2 + classification head
├── train.py            # Local training script
├── kaggle_train.py     # Kaggle/HDF5 training script
├── keggle/             # Trained model weights (not in git)
├── food-101/           # Dataset (not in git)
└── requirements.txt
```

## Academic Context

Module: CMS22202 Computer Vision and AI, Level 5, 20 credits
University: Ravensbourne University London
GitHub: https://github.com/Kowsyke/Mealy
