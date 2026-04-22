# FOR K — Everything you need to know about Mealy

This is your guide to your own project. Read it before the presentation.

---

## 1. What is Mealy

Mealy is a food image classifier. You show it a photo of food and it tells you what the food is, with a confidence percentage and an estimated calorie count. It can look at a webcam frame, split it into five overlapping regions, run the model on each region independently, and report up to four different foods in one shot. The whole system runs on your laptop with no internet required once the model is loaded.

---

## 2. How it works

Here is the full pipeline, step by step.

**Input arrives.** Either a webcam frame captured by demo.py or an image uploaded to the Flask API.

**preprocess.py runs.** The image is resized to 224 by 224 pixels. Every pixel value is divided by 255, turning the 0 to 255 range into a 0 to 1 range. That is the only preprocessing step. No channel-specific normalisation, no special scaling. This exactly matches what happened during training.

**The model runs.** The model is MobileNetV2, which was pretrained on ImageNet (1.2 million images, 1,000 classes). On top of it sits a classification head: GlobalAveragePooling2D collapses the spatial dimensions, Dense 256 with ReLU learns food-specific patterns, Dropout 0.4 prevents the model from memorising the training data, and Dense 101 with softmax outputs 101 probability scores, one per food class.

**Prediction is extracted.** The argmax of the 101 scores gives the predicted class index. The score at that index is the confidence.

**Multi-region detection (detect.py).** For the webcam demo and the /detect API endpoint, the frame is split into five regions: the full frame, top-left quadrant, top-right quadrant, bottom-left quadrant, and bottom-right quadrant. The model runs on each region separately. Any region that returns a confidence above 25% is added to the results. Duplicate classes are merged, keeping the highest confidence. Up to four unique foods are reported.

**Calorie lookup.** calories.py holds a dictionary of 101 food classes mapped to estimated kilocalories per standard serving. The detected class name is looked up and the number is returned alongside the prediction.

**Flask API returns JSON.** app.py sends back the prediction, confidence, calories, and top-5 list as a JSON response. The /detect endpoint returns the full list of multi-region detections and a total calorie count.

**The UI renders it.** ui/index.html shows the webcam feed, detection cards with animated confidence bars, calorie counts, and a running session total.

---

## 3. Training history

The original plan was to train on Google Colab using the raw Food-101 JPEG dataset (101,000 images). Colab's free GPU ran out of quota after one epoch. No good.

Switched to Kaggle, which gives 30 hours of free GPU per week (P100 or T4). The catch is that Kaggle uses a different version of Food-101 called kmader/food41, which stores the images in an HDF5 file instead of individual JPEGs. This meant rewriting the entire data loading pipeline. kaggle_train.py reads the HDF5 file directly.

The HDF5 version has 11,099 training images and 1,000 test images at 64 by 64 pixel resolution, not the original 224 by 224. This turned out to be the biggest constraint on final accuracy.

Training used two phases:
- Phase 1: the MobileNetV2 base was frozen. Only the classification head trained. 20 epochs, Adam at learning rate 1e-3.
- Phase 2: the top 30 layers of the base were unfrozen. The whole network fine-tuned together. 20 epochs, Adam at learning rate 1e-5 (much lower to avoid destroying the pretrained weights).

Final result: 37.6% test accuracy, 2.6215 test loss.

---

## 4. Why 37.6% and not higher

This is the question you will definitely get asked. Here is the honest answer.

The source images in the Kaggle HDF5 dataset are 64 by 64 pixels. MobileNetV2 expects 224 by 224. During preprocessing, those 64 by 64 images are upsampled to 224 by 224. Upsampling does not add information. The model is essentially looking at blurry, blocky images and trying to distinguish 101 food categories from them.

There are also only about 110 images per class in the training set. The full Food-101 JPEG dataset has 750 training images per class at proper resolution. More data, clearer images, much better results.

37.6% is still meaningful. Random chance across 101 classes is 1%. The model is 37 times better than random, which means it has genuinely learned to associate visual patterns with food categories, just not as precisely as it would with full-resolution data.

State-of-the-art on the full Food-101 dataset reaches above 90% accuracy using EfficientNetV2 trained on 224 by 224 images with proper augmentation. That comparison is worth mentioning in the presentation: you understand the gap and why it exists.

---

## 5. Project structure

```
Mealy/
app.py            Flask API. Routes: /health, /predict, /detect. Port 5001.
demo.py           OpenCV webcam demo. Multi-food overlay. Press Q to quit, A to toggle auto-scan.
detect.py         Multi-region inference engine. Splits frame into 5 regions, runs model on each.
preprocess.py     Shared preprocessing. Resize to 224x224, divide by 255. Used everywhere.
class_names.py    List of 101 class names loaded from food-101/meta/classes.txt.
calories.py       Dictionary mapping each food class to estimated kcal per serving.
load_data.py      tf.data pipeline for the original Food-101 JPEG format.
model.py          MobileNetV2 model definition with two-phase training setup.
train.py          Local training script (CPU, for reference only).
evaluate.py       Loads model, runs on test data if available, writes metrics report.
requirements.txt  All Python dependencies.
README.md         Setup and usage instructions.
FOR_K.md          This file.
ui/index.html     Browser UI. Thermal scan aesthetic. Works as file:// in Firefox.
keggle/           Trained model weights (not in git, too large).
food-101/         Raw dataset (not in git, 5 GB).
internal/         AI workspace files (not in git).
```

---

## 6. How to run it

Always use the full Python path. The shebang in the scripts is stale.

**Start the API:**
```
venv_archive/bin/python3 app.py
```
Wait for the "Ready" message. The model takes about 10 seconds to load.

**Open the UI:**
```
firefox ui/index.html
```
Allow camera access when Firefox asks. The UI will connect to the API automatically.

**Run the terminal demo:**
```
venv_archive/bin/python3 demo.py
```
The API must already be running. Press Q to quit, A to toggle auto-scan.

**Run evaluation:**
```
venv_archive/bin/python3 evaluate.py
```
Writes results to internal/claude/metrics_report.md.

---

## 7. Questions you might get asked and how to answer them

**"What dataset did you use?"**
Food-101. It has 101 food categories with around 1,000 images each, collected from food review websites. I used the HDF5 version from Kaggle (kmader/food41) because training happened on Kaggle and the full JPEG dataset is 5 GB.

**"What model did you train?"**
MobileNetV2, pretrained on ImageNet. I added a classification head and used transfer learning: first trained just the head with the base frozen, then fine-tuned the top 30 layers of the base with a much lower learning rate.

**"What is transfer learning?"**
Instead of training from scratch, which needs millions of images, I started with a model already trained on 1.2 million ImageNet images. The lower layers already know how to detect edges, textures, and shapes. I only needed to teach the upper layers to recognise food specifically.

**"Why MobileNetV2?"**
It is small (about 10 MB), fast on CPU, and has a strong track record on image classification. EfficientNet is more accurate but requires different preprocessing (it divides by standard deviation per channel). I tried it and hit a preprocessing mismatch that caused the validation accuracy to flatline. MobileNetV2 with simple divide-by-255 is cleaner and worked reliably.

**"What went wrong during training?"**
First tried Google Colab but hit the free GPU usage limit after one epoch. Switched to Kaggle, which gives 30 hours of free GPU per week. The Kaggle version of Food-101 uses HDF5 format instead of JPEGs, so I had to rewrite the data loading pipeline. Each setback taught me something about real-world ML deployment constraints.

**"What is your accuracy and is that good?"**
37.6% test accuracy. Random chance on 101 classes is 1%, so the model is 37 times better than random. The main limitation is that the Kaggle dataset uses 64 by 64 pixel images, far below the 224 by 224 the model expects. State-of-the-art uses full-resolution images and reaches above 90%.

**"What is the difference between classification and detection?"**
Classification answers what is in the image as a whole. Detection answers what and where, drawing bounding boxes. My model is a classifier. To simulate multi-food detection, I run it on five different crops of the frame and combine the results.

**"What is the Flask API?"**
A REST API running on port 5001. The /predict endpoint accepts an image and returns the top prediction with confidence and calories. The /detect endpoint runs multi-region inference and returns all detected foods with their calorie estimates and a total calorie count.

**"What are the ethics considerations?"**
Dataset bias: Food-101 is weighted toward Western and East Asian cuisines. Privacy: food images could reveal health conditions or dietary restrictions. Transparency: the model returns a confidence score, not just a label. No user data is stored, the API is stateless.

**"What would you do differently?"**
Use the full Food-101 dataset at 224 by 224 resolution with 750 images per class. Use EfficientNetV2 as the backbone with correct preprocessing. Train for more epochs with a cosine learning rate schedule. Add test-time augmentation to improve reliability.

**"What frameworks did you use?"**
TensorFlow 2.21 and Keras 3.13 for the model. OpenCV 4.13 for image processing and webcam capture. Flask 3.1 for the API. scikit-learn for evaluation metrics. Everything in Python 3.13.

---

## 8. Glossary

**Transfer learning:** starting from a model pretrained on a large dataset rather than training from random weights.

**MobileNetV2:** a lightweight CNN designed for mobile devices, using depthwise separable convolutions to keep parameter count low.

**HDF5:** Hierarchical Data Format version 5. A binary file format that stores large datasets efficiently, like a database for arrays.

**Epoch:** one full pass through the entire training dataset.

**Softmax:** a function that converts raw output scores into probabilities that all sum to exactly 1.

**Top-1 accuracy:** the percentage of test images where the correct class is the single top prediction.

**Fine-tuning:** unfreezing some layers of a pretrained model and continuing training with a low learning rate so they adapt to the new task.

**Overfitting:** when a model memorises training data instead of learning general patterns. Dropout and keeping validation accuracy close to training accuracy are signs it is not happening.
