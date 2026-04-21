# Mealy - food classifier
# evaluation script - accuracy, F1, confusion matrix, per-class breakdown
# developed with help from Claude AI
import os
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    classification_report, confusion_matrix,
    accuracy_score, f1_score, precision_score, recall_score,
)
import tensorflow as tf
from load_data import make_dataset, load_class_names

CONFIG = {
    "dataset_dir":  os.path.join(os.path.dirname(__file__), "food-101"),
    "model_path":   os.path.join(os.path.dirname(__file__), "mealy_model.keras"),
    "report_path":  os.path.join(os.path.dirname(__file__), "claude", "metrics_report.md"),
    "cm_path":      os.path.join(os.path.dirname(__file__), "confusion_matrix.png"),
    "batch_size":   32,
}


def collect_predictions(model, test_ds) -> tuple[np.ndarray, np.ndarray]:
    y_true, y_pred = [], []
    for images, labels in test_ds:
        preds = model.predict(images, verbose=0)
        y_true.extend(labels.numpy())
        y_pred.extend(np.argmax(preds, axis=1))
    return np.array(y_true), np.array(y_pred)


def plot_confusion_matrix(y_true, y_pred, class_names, save_path, top_n=20):
    cm = confusion_matrix(y_true, y_pred)
    # Find the top_n most-confused classes (off-diagonal errors)
    errors = cm.copy()
    np.fill_diagonal(errors, 0)
    confused_idx = np.argsort(errors.sum(axis=1))[-top_n:][::-1]
    cm_sub = cm[np.ix_(confused_idx, confused_idx)]
    labels_sub = [class_names[i] for i in confused_idx]

    fig, ax = plt.subplots(figsize=(14, 12))
    sns.heatmap(
        cm_sub, annot=True, fmt="d", cmap="Blues",
        xticklabels=labels_sub, yticklabels=labels_sub, ax=ax,
    )
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    ax.set_title(f"Confusion Matrix - top {top_n} most confused classes")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(save_path)
    print(f"[evaluate] Confusion matrix saved to {save_path}")


def write_metrics_report(y_true, y_pred, class_names, report_path, overall: dict):
    per_class = classification_report(y_true, y_pred, target_names=class_names, output_dict=True)
    rows = []
    for cls in class_names:
        m = per_class[cls]
        rows.append((cls, m["precision"], m["recall"], m["f1-score"], int(m["support"])))
    rows.sort(key=lambda r: r[3])  # sort by F1 ascending

    with open(report_path, "w") as f:
        f.write("# metrics_report.md — Mealy Evaluation\n\n")
        f.write("## Overall Metrics\n\n")
        f.write(f"| Metric | Value |\n|--------|-------|\n")
        for k, v in overall.items():
            f.write(f"| {k} | {v:.4f} |\n")
        f.write("\n## Per-Class Accuracy (sorted by F1, worst first)\n\n")
        f.write("| Class | Precision | Recall | F1 | Support |\n")
        f.write("|-------|-----------|--------|----|---------|\n")
        for cls, p, r, f1, sup in rows:
            f.write(f"| {cls} | {p:.3f} | {r:.3f} | {f1:.3f} | {sup} |\n")
    print(f"[evaluate] Metrics report written to {report_path}")


def main():
    print("[evaluate] Loading model...")
    model = tf.keras.models.load_model(CONFIG["model_path"])

    print("[evaluate] Loading test data...")
    test_ds = make_dataset("test", augment_train=False, dataset_dir=CONFIG["dataset_dir"])
    class_names = load_class_names(CONFIG["dataset_dir"])

    print("[evaluate] running predictions on test set...")
    y_true, y_pred = collect_predictions(model, test_ds)

    acc  = accuracy_score(y_true, y_pred)
    f1   = f1_score(y_true, y_pred, average="weighted")
    prec = precision_score(y_true, y_pred, average="weighted", zero_division=0)
    rec  = recall_score(y_true, y_pred, average="weighted", zero_division=0)

    overall = {"Accuracy": acc, "Precision (weighted)": prec, "Recall (weighted)": rec, "F1 (weighted)": f1}
    print("\n[evaluate] Results:")
    for k, v in overall.items():
        print(f"  {k}: {v:.4f}")

    plot_confusion_matrix(y_true, y_pred, class_names, CONFIG["cm_path"])
    write_metrics_report(y_true, y_pred, class_names, CONFIG["report_path"], overall)


if __name__ == "__main__":
    main()
