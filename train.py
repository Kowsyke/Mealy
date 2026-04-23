# Mealy — original training script
# Two-phase transfer learning: frozen base then fine-tune top layers
# Use train_optimized.py for full-resolution training; this version is the first iteration
import os
import tensorflow as tf
import matplotlib.pyplot as plt
from load_data import make_dataset
from model import build_model, unfreeze_top_layers

CONFIG = {
    "dataset_dir": os.path.join(os.path.dirname(__file__), "food-101"),
    "model_path_keras": os.path.join(os.path.dirname(__file__), "mealy_model.keras"),
    "model_path_h5": os.path.join(os.path.dirname(__file__), "mealy_model.h5"),
    "curves_path": os.path.join(os.path.dirname(__file__), "training_curves.png"),
    "phase1_epochs": 10,
    "phase2_epochs": 10,
    "phase1_lr": 1e-3,
    "phase2_lr": 1e-5,
}


def plot_curves(histories: list, output_path: str) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    acc, val_acc, loss, val_loss = [], [], [], []
    for h in histories:
        acc += h.history["accuracy"]
        val_acc += h.history["val_accuracy"]
        loss += h.history["loss"]
        val_loss += h.history["val_loss"]

    epochs = range(1, len(acc) + 1)
    axes[0].plot(epochs, acc, label="Train acc")
    axes[0].plot(epochs, val_acc, label="Val acc")
    axes[0].axvline(CONFIG["phase1_epochs"], color="grey", linestyle="--", label="Fine-tune start")
    axes[0].set_title("Accuracy")
    axes[0].legend()

    axes[1].plot(epochs, loss, label="Train loss")
    axes[1].plot(epochs, val_loss, label="Val loss")
    axes[1].axvline(CONFIG["phase1_epochs"], color="grey", linestyle="--")
    axes[1].set_title("Loss")
    axes[1].legend()

    plt.tight_layout()
    plt.savefig(output_path)
    print(f"[train] Curves saved to {output_path}")


def main():
    print("[train] Loading data...")
    train_ds = make_dataset("train", dataset_dir=CONFIG["dataset_dir"])
    test_ds = make_dataset("test", augment_train=False, dataset_dir=CONFIG["dataset_dir"])

    print("[train] Building model...")
    model = build_model()

    print("[train] Phase 1: training head only...")
    model.compile(
        optimizer=tf.keras.optimizers.Adam(CONFIG["phase1_lr"]),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    h1 = model.fit(
        train_ds,
        epochs=CONFIG["phase1_epochs"],
        validation_data=test_ds,
        callbacks=[tf.keras.callbacks.EarlyStopping(patience=3, restore_best_weights=True)],
    )

    print("[train] Phase 2: fine-tuning top layers...")
    unfreeze_top_layers(model)
    model.compile(
        optimizer=tf.keras.optimizers.Adam(CONFIG["phase2_lr"]),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    h2 = model.fit(
        train_ds,
        epochs=CONFIG["phase2_epochs"],
        validation_data=test_ds,
        callbacks=[tf.keras.callbacks.EarlyStopping(patience=3, restore_best_weights=True)],
    )

    print("[train] Saving model...")
    model.save(CONFIG["model_path_keras"])
    model.save(CONFIG["model_path_h5"])
    print(f"[train] Saved to {CONFIG['model_path_keras']} and {CONFIG['model_path_h5']}")

    plot_curves([h1, h2], CONFIG["curves_path"])

    print("\n[train] Final evaluation:")
    loss, acc = model.evaluate(test_ds)
    print(f"Test accuracy: {acc:.4f}  |  Test loss: {loss:.4f}")


if __name__ == "__main__":
    main()
