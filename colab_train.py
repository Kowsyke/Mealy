# Mealy - food classifier
# colab training script - upload to Google Colab and run top to bottom
# dataset should be at /content/drive/MyDrive/Mealy/food-101/
# developed with help from Claude AI

# Cell 1: mount Google Drive
from google.colab import drive
drive.mount("/content/drive")

# Cell 2: Install dependencies (Colab usually has these; pin versions just in case)
# !pip install -q tensorflow==2.21.0 keras==3.13.2 matplotlib scikit-learn pillow opencv-python-headless

# Cell 3: Imports and config
import os
import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt
from sklearn.metrics import classification_report

DATASET_DIR = "/content/drive/MyDrive/Mealy/food-101"
SAVE_DIR    = "/content/drive/MyDrive/Mealy"
IMAGE_SIZE  = 224
INPUT_SHAPE = (IMAGE_SIZE, IMAGE_SIZE, 3)
NUM_CLASSES = 101
BATCH_SIZE  = 64   # larger batch fits on Colab GPU
AUTOTUNE    = tf.data.AUTOTUNE

PHASE1_EPOCHS = 10
PHASE2_EPOCHS = 10
PHASE1_LR     = 1e-3
PHASE2_LR     = 1e-5
FINE_TUNE_LAYERS = 30

print("TF version:", tf.__version__)
print("GPU:", tf.config.list_physical_devices("GPU"))

# Cell 4: Data loading helpers
def load_class_names(dataset_dir):
    with open(os.path.join(dataset_dir, "meta", "classes.txt")) as f:
        return [l.strip() for l in f if l.strip()]

def parse_split(dataset_dir, split):
    class_names = load_class_names(dataset_dir)
    class_to_idx = {n: i for i, n in enumerate(class_names)}
    paths, labels = [], []
    with open(os.path.join(dataset_dir, "meta", f"{split}.txt")) as f:
        for line in f:
            entry = line.strip()
            if not entry:
                continue
            cls = entry.split("/")[0]
            paths.append(os.path.join(dataset_dir, "images", entry + ".jpg"))
            labels.append(class_to_idx[cls])
    return paths, labels

def preprocess(path):
    raw   = tf.io.read_file(path)
    image = tf.image.decode_jpeg(raw, channels=3)
    image = tf.image.resize(image, [IMAGE_SIZE, IMAGE_SIZE])
    image = tf.cast(image, tf.float32) / 255.0
    return image

def augment(image):
    image = tf.image.random_flip_left_right(image)
    image = tf.image.random_brightness(image, 0.15)
    image = tf.image.random_contrast(image, 0.85, 1.15)
    image = tf.image.random_saturation(image, 0.85, 1.15)
    image = tf.clip_by_value(image, 0.0, 1.0)
    return image

def make_dataset(split, do_augment=False):
    paths, labels = parse_split(DATASET_DIR, split)
    print(f"  {split}: {len(paths)} images")
    ds = tf.data.Dataset.from_tensor_slices((paths, labels))
    ds = ds.map(lambda p, l: (preprocess(p), l), num_parallel_calls=AUTOTUNE)
    if do_augment:
        ds = ds.map(lambda img, l: (augment(img), l), num_parallel_calls=AUTOTUNE)
    if split == "train":
        ds = ds.shuffle(2000)
    else:
        ds = ds.cache()
    return ds.batch(BATCH_SIZE).prefetch(AUTOTUNE)

print("Loading datasets...")
train_ds = make_dataset("train", do_augment=True)
test_ds  = make_dataset("test",  do_augment=False)

# Cell 5: Build model
def build_model():
    base = tf.keras.applications.MobileNetV2(
        input_shape=INPUT_SHAPE, include_top=False, weights="imagenet"
    )
    base.trainable = False
    inputs  = tf.keras.Input(shape=INPUT_SHAPE)
    x       = base(inputs, training=False)
    x       = tf.keras.layers.GlobalAveragePooling2D()(x)
    x       = tf.keras.layers.Dense(256, activation="relu")(x)
    x       = tf.keras.layers.Dropout(0.4)(x)
    outputs = tf.keras.layers.Dense(NUM_CLASSES, activation="softmax")(x)
    return tf.keras.Model(inputs, outputs)

model = build_model()
model.summary()

# Cell 6: Phase 1 — train head only
model.compile(
    optimizer=tf.keras.optimizers.Adam(PHASE1_LR),
    loss="sparse_categorical_crossentropy",
    metrics=["accuracy"],
)
callbacks_p1 = [
    tf.keras.callbacks.EarlyStopping(patience=3, restore_best_weights=True),
    tf.keras.callbacks.ModelCheckpoint(
        os.path.join(SAVE_DIR, "mealy_checkpoint_p1.keras"), save_best_only=True
    ),
]
print("\nPhase 1: training classification head...")
h1 = model.fit(train_ds, epochs=PHASE1_EPOCHS, validation_data=test_ds, callbacks=callbacks_p1)

# Cell 7: Phase 2 — fine-tune top layers
base = model.layers[1]
base.trainable = True
for layer in base.layers[:-FINE_TUNE_LAYERS]:
    layer.trainable = False
print(f"\nPhase 2: fine-tuning top {FINE_TUNE_LAYERS} layers...")

model.compile(
    optimizer=tf.keras.optimizers.Adam(PHASE2_LR),
    loss="sparse_categorical_crossentropy",
    metrics=["accuracy"],
)
callbacks_p2 = [
    tf.keras.callbacks.EarlyStopping(patience=3, restore_best_weights=True),
    tf.keras.callbacks.ModelCheckpoint(
        os.path.join(SAVE_DIR, "mealy_checkpoint_p2.keras"), save_best_only=True
    ),
]
h2 = model.fit(train_ds, epochs=PHASE2_EPOCHS, validation_data=test_ds, callbacks=callbacks_p2)

# Cell 8: Save final model
model.save(os.path.join(SAVE_DIR, "mealy_model.keras"))
model.save(os.path.join(SAVE_DIR, "mealy_model.h5"))
print("Model saved to Google Drive")

# Cell 9: Training curves
def plot_curves(h1, h2, save_path):
    acc     = h1.history["accuracy"]     + h2.history["accuracy"]
    val_acc = h1.history["val_accuracy"] + h2.history["val_accuracy"]
    loss    = h1.history["loss"]         + h2.history["loss"]
    val_loss= h1.history["val_loss"]     + h2.history["val_loss"]
    ep      = range(1, len(acc) + 1)
    split   = len(h1.history["accuracy"])

    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    axes[0].plot(ep, acc, label="Train"); axes[0].plot(ep, val_acc, label="Val")
    axes[0].axvline(split, color="grey", linestyle="--", label="Fine-tune")
    axes[0].set_title("Accuracy"); axes[0].legend()
    axes[1].plot(ep, loss, label="Train"); axes[1].plot(ep, val_loss, label="Val")
    axes[1].axvline(split, color="grey", linestyle="--")
    axes[1].set_title("Loss"); axes[1].legend()
    plt.tight_layout()
    plt.savefig(save_path)
    plt.show()
    print(f"Curves saved to {save_path}")

plot_curves(h1, h2, os.path.join(SAVE_DIR, "training_curves.png"))

# Cell 10: Final evaluation
print("\nFinal test evaluation:")
test_loss, test_acc = model.evaluate(test_ds)
print(f"Test accuracy: {test_acc:.4f}  |  Test loss: {test_loss:.4f}")
