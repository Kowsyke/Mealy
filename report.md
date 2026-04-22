# Mealy: Food Image Classification
**CMS22202 — Kowsyke — Ravensbourne University London**

---

## 1. Objectives

Mealy identifies food in photographs and returns a confidence score. Diet tracking apps and food logging tools need accurate image-to-label mapping, which motivated this project. The task is 101-class classification over the Food-101 dataset, delivered as a Flask API and live webcam demo.

## 2. System Requirements

**Data:** Food-101 contains 101 food categories with around 1,000 images each, collected from food review websites (Bossard et al., 2014). Training used the kmader/food41 HDF5 version on Kaggle: 11,099 training images and 1,000 test images at 64×64 resolution.

**Libraries:** Python 3.13, TensorFlow 2.21, Keras 3.13, OpenCV 4.13, Flask 3.1, scikit-learn 1.8, NumPy 2.4, Pillow 12.2. Training ran on Kaggle's cloud GPU. Inference runs on CPU.

**Hardware:** The local machine (Intel i5-8250U, 16 GB RAM, no GPU) cannot train a deep network, so Kaggle was used.

## 3. Design

Images are resized to 224×224, cast to float32, and divided by 255. No channel normalisation was applied. This pipeline is defined once in `preprocess.py` and imported everywhere, ensuring training and inference always match.

The model uses MobileNetV2 with ImageNet pretrained weights (Sandler et al., 2018). It was chosen for its small size, fast CPU inference, and strong transfer learning track record. A classification head was added: GlobalAveragePooling2D, Dense 256 with ReLU, Dropout 0.4, then Dense 101 with softmax.

The Flask API exposes `/predict` (multipart image upload, returns top-5 JSON) and `/health`. The webcam demo reads `/dev/video0`, sends a frame to `/predict` every second, and overlays the result on screen.

## 4. Implementation

Training used two phases, which is standard practice in transfer learning (Geron, 2019).

Phase 1: the base was frozen and the head trained for 20 epochs at lr=1e-3. This lets the head learn before pretrained weights are touched.

Phase 2: the top 30 base layers were unfrozen and fine-tuned for 20 epochs at lr=1e-5. The low rate prevents catastrophic forgetting while allowing upper layers to adapt to food patterns.

The HDF5 dataset used 64×64 images, upsampled to 224×224 during preprocessing. This lower source resolution was a known limitation from the start.

## 5. Results

Final test accuracy: **37.6%**, test loss: **2.6215**. Random chance across 101 classes is 1%, so meaningful features were learned. State-of-the-art on Food-101 exceeds 90%, but those results use full-resolution training data and larger networks.

The main bottleneck was image resolution and ~110 samples per class. Future work would train on full Food-101 at 224×224 with EfficientNetV2 or ResNet-50.

The API responds in under 200ms on CPU. The demo runs above 20 FPS.

GitHub: https://github.com/Kowsyke/Mealy

---

**References**

Bossard, L., Guillaumin, M. and Van Gool, L., 2014. Food-101 — Mining Discriminative Components with Random Forests. *European Conference on Computer Vision*, pp.446–461.

Geron, A., 2019. *Hands-on Machine Learning with Scikit-Learn, Keras, and TensorFlow*. 2nd ed. Sebastopol: O'Reilly Media.

Sandler, M., Howard, A., Zhu, M., Zhmoginov, A. and Chen, L., 2018. MobileNetV2: Inverted Residuals and Linear Bottlenecks. *Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition*, pp.4510–4520.
