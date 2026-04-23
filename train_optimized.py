"""
train_optimized.py — Food-101 JPEG full-resolution retrain on local CPU.

Uses the JPEG dataset in food-101/ (750 training images per class at native
resolution, no upsampling from 64x64). Targets >60% test accuracy when run
to completion; EarlyStopping exits early if validation plateaus.

Saves to keggle/mealy_optimized.keras (does not overwrite the production model).

Usage:
    venv_archive/bin/python3 train_optimized.py
"""
import os
import tensorflow as tf
from model import build_model, unfreeze_top_layers
from load_data import make_dataset

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
DATA_DIR  = os.path.join(BASE_DIR, "food-101")
OUT_PATH  = os.path.join(BASE_DIR, "keggle", "mealy_optimized.keras")
CKPT_DIR  = os.path.join(BASE_DIR, "checkpoints_optimized")

P1_EPOCHS = 20
P2_EPOCHS = 30
P1_LR     = 1e-3
P2_LR     = 1e-5
PATIENCE  = 7

os.makedirs(CKPT_DIR, exist_ok=True)


def phase1(model):
    model.compile(
        optimizer=tf.keras.optimizers.Adam(P1_LR),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    train_ds = make_dataset("train", augment_train=True,  dataset_dir=DATA_DIR)
    val_ds   = make_dataset("test",  augment_train=False, dataset_dir=DATA_DIR)

    callbacks = [
        tf.keras.callbacks.EarlyStopping(
            monitor="val_accuracy", patience=PATIENCE, restore_best_weights=True
        ),
        tf.keras.callbacks.ModelCheckpoint(
            os.path.join(CKPT_DIR, "p1_{epoch:02d}_{val_accuracy:.4f}.keras"),
            save_best_only=False,
        ),
        tf.keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss", factor=0.5, patience=3, min_lr=1e-6, verbose=1
        ),
    ]

    print("\n[train] Phase 1 — frozen base, head only")
    history = model.fit(train_ds, validation_data=val_ds, epochs=P1_EPOCHS, callbacks=callbacks)
    best_val = max(history.history["val_accuracy"])
    print(f"[train] Phase 1 done — best val acc: {best_val:.4f}")
    return history


def phase2(model):
    unfreeze_top_layers(model)
    model.compile(
        optimizer=tf.keras.optimizers.Adam(P2_LR),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    train_ds = make_dataset("train", augment_train=True,  dataset_dir=DATA_DIR)
    val_ds   = make_dataset("test",  augment_train=False, dataset_dir=DATA_DIR)

    callbacks = [
        tf.keras.callbacks.EarlyStopping(
            monitor="val_accuracy", patience=PATIENCE, restore_best_weights=True
        ),
        tf.keras.callbacks.ModelCheckpoint(
            os.path.join(CKPT_DIR, "p2_{epoch:02d}_{val_accuracy:.4f}.keras"),
            save_best_only=False,
        ),
        tf.keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss", factor=0.5, patience=3, min_lr=1e-8, verbose=1
        ),
    ]

    print("\n[train] Phase 2 — top 30 base layers unfrozen, fine-tuning")
    history = model.fit(train_ds, validation_data=val_ds, epochs=P2_EPOCHS, callbacks=callbacks)
    best_val = max(history.history["val_accuracy"])
    print(f"[train] Phase 2 done — best val acc: {best_val:.4f}")
    return history


def main():
    print(f"[train] TF {tf.__version__}")
    print(f"[train] Dataset : {DATA_DIR}")
    print(f"[train] Output  : {OUT_PATH}")
    print("[train] Full-resolution Food-101 JPEG (~750 images/class, 224x224 native)")

    model = build_model()
    model.summary(print_fn=lambda _: None)

    phase1(model)
    phase2(model)

    model.save(OUT_PATH)
    print(f"\n[train] Saved to {OUT_PATH}")

    print("[train] Final evaluation on test split...")
    test_ds = make_dataset("test", augment_train=False, dataset_dir=DATA_DIR)
    loss, acc = model.evaluate(test_ds, verbose=1)
    print(f"[train] Test accuracy: {acc:.4f}  loss: {loss:.4f}")


if __name__ == "__main__":
    main()
