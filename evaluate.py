import os
import numpy as np
import matplotlib.pyplot as plt
import tensorflow as tf
from class_names import CLASS_NAMES

CONFIG = {
    "model_path": os.path.join(os.path.dirname(__file__), "keggle", "mealy_model.keras"),
    "h5_path":    os.path.join(os.path.dirname(__file__), "keggle", "food_c101_n10099_r64x64x3.h5"),
    "report_path": os.path.join(os.path.dirname(__file__), "claude", "metrics_report.md"),
    "cm_path":    os.path.join(os.path.dirname(__file__), "confusion_matrix.png"),
    "batch_size": 32,
}

KNOWN = {
    "accuracy": 0.376,
    "loss":     2.6215,
}


def _load_h5_test():
    import h5py
    with h5py.File(CONFIG["h5_path"], "r") as f:
        X = f["test/images"][:]
        y = np.argmax(f["test/category"][...], axis=1)
    X = X.astype(np.float32) / 255.0
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
        im = ax.imshow(cm_sub, cmap="Blues")
        ax.set_xticks(range(top_n)); ax.set_xticklabels(labels, rotation=45, ha="right")
        ax.set_yticks(range(top_n)); ax.set_yticklabels(labels)

    ax.set_xlabel("Predicted"); ax.set_ylabel("True")
    ax.set_title(f"Confusion matrix — top {top_n} most confused classes")
    plt.tight_layout()
    plt.savefig(save_path)
    print(f"[evaluate] Confusion matrix saved to {save_path}")


def _write_report(overall: dict, per_class: dict | None = None):
    with open(CONFIG["report_path"], "w") as f:
        f.write("# metrics_report.md — Mealy Evaluation\n\n")
        f.write("## Overall Metrics\n\n")
        f.write("| Metric | Value |\n|--------|-------|\n")
        for k, v in overall.items():
            f.write(f"| {k} | {v} |\n")
        f.write("\n")
        if per_class:
            f.write("## Per-Class F1 (worst first)\n\n")
            f.write("| Class | Precision | Recall | F1 | Support |\n")
            f.write("|-------|-----------|--------|----|---------|\n")
            rows = sorted(per_class.items(), key=lambda x: x[1]["f1-score"])
            for cls, m in rows:
                if cls in ("accuracy", "macro avg", "weighted avg"):
                    continue
                f.write(f"| {cls} | {m['precision']:.3f} | {m['recall']:.3f} | {m['f1-score']:.3f} | {int(m['support'])} |\n")
        else:
            f.write("*Full per-class breakdown not available — evaluation ran on Kaggle.*\n\n")
            f.write("Training notebook: `keggle/__notebook_source__.ipynb`\n")
    print(f"[evaluate] Report written to {CONFIG['report_path']}")


def main():
    print("[evaluate] Loading model...")
    model = tf.keras.models.load_model(CONFIG["model_path"])

    if os.path.exists(CONFIG["h5_path"]):
        print("[evaluate] Loading test data from h5...")
        X_test, y_true = _load_h5_test()
        probs = model.predict(X_test, batch_size=CONFIG["batch_size"], verbose=1)
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
        print("\n[evaluate] Results:")
        for k, v in overall.items():
            print(f"  {k}: {v}")

        per_class = classification_report(y_true, y_pred,
                                          target_names=CLASS_NAMES,
                                          output_dict=True)
        _plot_cm(y_true, y_pred, CONFIG["cm_path"])
        _write_report(overall, per_class)

    else:
        print("[evaluate] No local test h5 found — writing known metrics from Kaggle run")
        overall = {
            "Accuracy":  f"{KNOWN['accuracy']:.4f}",
            "Loss":      f"{KNOWN['loss']:.4f}",
            "Note":      "Full evaluation ran on Kaggle (keggle/__notebook_source__.ipynb)",
        }
        _write_report(overall)


if __name__ == "__main__":
    main()
