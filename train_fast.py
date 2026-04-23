"""
train_fast.py - Lightweight Food-101 training for CPU.

Uses only the first TRAIN_PER_CLASS images per class from the training split
and first TEST_PER_CLASS from the test split. No augmentation. Single phase
(frozen base, head only). Targets 55-65% accuracy in roughly 1 hour on CPU.

Saves directly to keggle/mealy_model.keras so the API uses it immediately.
"""
import os
import tensorflow as tf
from model import build_model

BASE_DIR        = os.path.dirname(os.path.abspath(__file__))
DATA_DIR        = os.path.join(BASE_DIR, "food-101")
OUT_PATH        = os.path.join(BASE_DIR, "keggle", "mealy_model.keras")

TRAIN_PER_CLASS = 75    # 75 x 101 = 7,575 training images
TEST_PER_CLASS  = 25    # 25 x 101 = 2,525 test images
BATCH_SIZE      = 64
EPOCHS          = 15
LR              = 1e-3
IMAGE_SIZE      = 224


def parse_split(split, per_class):
    """Read the meta split file and return (paths, labels) limited to per_class each."""
    classes_file = os.path.join(DATA_DIR, "meta", "classes.txt")
    with open(classes_file) as f:
        class_names = [l.strip() for l in f if l.strip()]
    class_to_idx = {name: i for i, name in enumerate(class_names)}

    split_file = os.path.join(DATA_DIR, "meta", f"{split}.txt")
    counts = {}
    paths, labels = [], []
    with open(split_file) as f:
        for line in f:
            entry = line.strip()
            if not entry:
                continue
            cls = entry.split("/")[0]
            if counts.get(cls, 0) >= per_class:
                continue
            img = os.path.join(DATA_DIR, "images", entry + ".jpg")
            paths.append(img)
            labels.append(class_to_idx[cls])
            counts[cls] = counts.get(cls, 0) + 1
    return paths, labels, len(class_names)


def preprocess(path, label):
    raw = tf.io.read_file(path)
    img = tf.image.decode_jpeg(raw, channels=3)
    img = tf.image.resize(img, [IMAGE_SIZE, IMAGE_SIZE])
    img = tf.cast(img, tf.float32) / 255.0
    return img, label


def make_ds(split, per_class, shuffle=False):
    paths, labels, _ = parse_split(split, per_class)
    print(f"[fast] {split}: {len(paths)} images")
    ds = tf.data.Dataset.from_tensor_slices((paths, labels))
    if shuffle:
        ds = ds.shuffle(len(paths), reshuffle_each_iteration=True)
    ds = ds.map(preprocess, num_parallel_calls=tf.data.AUTOTUNE)
    ds = ds.batch(BATCH_SIZE).prefetch(tf.data.AUTOTUNE)
    return ds


def main():
    print(f"[fast] TF {tf.__version__}")
    print(f"[fast] {TRAIN_PER_CLASS} images/class train, {TEST_PER_CLASS} images/class test")
    print(f"[fast] Output: {OUT_PATH}")

    train_ds = make_ds("train", TRAIN_PER_CLASS, shuffle=True)
    val_ds   = make_ds("test",  TEST_PER_CLASS,  shuffle=False)

    model = build_model()
    model.compile(
        optimizer=tf.keras.optimizers.Adam(LR),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )

    callbacks = [
        tf.keras.callbacks.EarlyStopping(
            monitor="val_accuracy", patience=5, restore_best_weights=True, verbose=1
        ),
        tf.keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss", factor=0.5, patience=3, min_lr=1e-6, verbose=1
        ),
    ]

    print(f"\n[fast] Training for up to {EPOCHS} epochs...")
    history = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=EPOCHS,
        callbacks=callbacks,
    )

    best_val = max(history.history["val_accuracy"])
    print(f"\n[fast] Best val accuracy: {best_val:.4f} ({round(best_val*100, 1)}%)")

    model.save(OUT_PATH)
    print(f"[fast] Saved to {OUT_PATH}")
    print("[fast] Restart the Flask API to load the new model.")


if __name__ == "__main__":
    main()
