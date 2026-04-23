# Mealy: model evaluator
# Loads the trained model and runs it against the Food-101 test split,
# then prints accuracy and loss and saves a confusion matrix chart

import os
import numpy as np
import matplotlib.pyplot as plt
import tensorflow as tf
from class_names import CLASS_NAMES

MODEL_PATH  = os.path.join(os.path.dirname(__file__), "keggle", "mealy_model.keras")
H5_PATH     = os.path.join(os.path.dirname(__file__), "keggle", "food_c101_n10099_r64x64x3.h5")
REPORT_PATH = os.path.join(os.path.dirname(__file__), "claude", "metrics_report.md")
CM_PATH     = os.path.join(os.path.dirname(__file__), "confusion_matrix.png")
BATCH_SIZE  = 32

KNOWN = {"accuracy": 0.376, "loss": 2.6215}


def _load_h5_test():
    import h5py
    with h5py.File(H5_PATH, "r") as f:
        X = f["test/images"][:].astype(np.float32) / 255.0
        y = np.argmax(f["test/category"][...], axis=1)
    return X, y


def _plot_cm(y_true, y_pred, save_path, top_n=20):
    from sklearn.metrics import confusion_matrix
    cm = confusion_matrix(y_true, y_pred)
    errors = cm.copy()
    np.fill_diagonal(errors, 0)
    idx = np.argsort(errors.sum(axis=1))[-top_n:][::-1]
    cm_sub = cm[np.ix_(idx, idx)]
    labels = [CLASS_NAMES[i] for i in idx]

    try:
        import seaborn as sns
        fig, ax = plt.subplots(figsize=(14, 12))
        sns.heatmap(cm_sub, annot=True, fmt="d", cmap="Blues",
                    xticklabels=labels, yticklabels=labels, ax=ax)
    except ImportError:
        fig, ax = plt.subplots(figsize=(14, 12))
        ax.imshow(cm_sub, cmap="Blues")
        ax.set_xticks(range(top_n)); ax.set_xticklabels(labels, rotation=45, ha="right")
        ax.set_yticks(range(top_n)); ax.set_yticklabels(labels)

    ax.set_xlabel("Predicted"); ax.set_ylabel("True")
    ax.set_title(f"Confusion matrix: top {top_n} most confused classes")
    plt.tight_layout()
    plt.savefig(save_path)
    print(f"[evaluate] Confusion matrix saved: {save_path}")


def _write_report(overall, per_class=None):
    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, "w") as f:
        f.write("# metrics_report.md\n\n## Overall\n\n| Metric | Value |\n|--------|-------|\n")
        for k, v in overall.items():
            f.write(f"| {k} | {v} |\n")
        f.write("\n")
        if per_class:
            f.write("## Per-Class F1 (worst first)\n\n")
            f.write("| Class | Precision | Recall | F1 | Support |\n")
            f.write("|-------|-----------|--------|----|---------|\n")
            rows = sorted(
                [(k, v) for k, v in per_class.items()
                 if k not in ("accuracy", "macro avg", "weighted avg")],
                key=lambda x: x[1]["f1-score"]
            )
            for cls, m in rows:
                f.write(f"| {cls} | {m['precision']:.3f} | {m['recall']:.3f} | {m['f1-score']:.3f} | {int(m['support'])} |\n")
        else:
            f.write("*Full per-class breakdown ran on Kaggle. See keggle/__notebook_source__.ipynb*\n")
    print(f"[evaluate] Report written: {REPORT_PATH}")


def main():
    print("[evaluate] Loading model...")
    model = tf.keras.models.load_model(MODEL_PATH)

    if os.path.exists(H5_PATH):
        print("[evaluate] Loading test data from h5...")
        X_test, y_true = _load_h5_test()
        probs = model.predict(X_test, batch_size=BATCH_SIZE, verbose=1)
        y_pred = np.argmax(probs, axis=1)

        from sklearn.metrics import (accuracy_score, f1_score,
                                     precision_score, recall_score,
                                     classification_report)
        acc  = accuracy_score(y_true, y_pred)
        prec = precision_score(y_true, y_pred, average="weighted", zero_division=0)
        rec  = recall_score(y_true, y_pred, average="weighted", zero_division=0)
        f1   = f1_score(y_true, y_pred, average="weighted")

        overall = {
            "Accuracy":             f"{acc:.4f}",
            "Precision (weighted)": f"{prec:.4f}",
            "Recall (weighted)":    f"{rec:.4f}",
            "F1 (weighted)":        f"{f1:.4f}",
        }
        for k, v in overall.items():
            print(f"  {k}: {v}")

        per_class = classification_report(y_true, y_pred, target_names=CLASS_NAMES, output_dict=True)
        _plot_cm(y_true, y_pred, CM_PATH)
        _write_report(overall, per_class)

    else:
        print("[evaluate] No local h5 found. Writing known Kaggle results.")
        overall = {
            "Accuracy": f"{KNOWN['accuracy']:.4f}",
            "Loss":     f"{KNOWN['loss']:.4f}",
            "Note":     "Evaluation ran on Kaggle. See keggle/__notebook_source__.ipynb",
        }
        _write_report(overall)


if __name__ == "__main__":
    main()
