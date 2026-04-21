# Mealy - food classifier
# tf.data pipeline for Food-101, reads train/test splits from meta/
# developed with help from Claude AI
import os
import tensorflow as tf
from preprocess import preprocess_path, IMAGE_SIZE

CONFIG = {
    "dataset_dir": os.path.join(os.path.dirname(__file__), "food-101"),
    "batch_size": 32,
    "autotune": tf.data.AUTOTUNE,
}


def load_class_names(dataset_dir: str) -> list[str]:
    classes_file = os.path.join(dataset_dir, "meta", "classes.txt")
    with open(classes_file) as f:
        return [line.strip() for line in f if line.strip()]


def parse_split_file(dataset_dir: str, split: str) -> tuple[list[str], list[int]]:
    """Return (image_paths, labels) for a given split."""
    class_names = load_class_names(dataset_dir)
    class_to_idx = {name: i for i, name in enumerate(class_names)}

    split_file = os.path.join(dataset_dir, "meta", f"{split}.txt")
    paths, labels = [], []
    with open(split_file) as f:
        for line in f:
            entry = line.strip()
            if not entry:
                continue
            class_name = entry.split("/")[0]
            img_path = os.path.join(dataset_dir, "images", entry + ".jpg")
            paths.append(img_path)
            labels.append(class_to_idx[class_name])
    return paths, labels


def augment(image: tf.Tensor) -> tf.Tensor:
    image = tf.image.random_flip_left_right(image)
    image = tf.image.random_brightness(image, max_delta=0.15)
    image = tf.image.random_contrast(image, lower=0.85, upper=1.15)
    image = tf.image.random_saturation(image, lower=0.85, upper=1.15)
    # Random rotation via crop-and-resize
    image = tf.keras.layers.RandomRotation(0.1)(tf.expand_dims(image, 0))[0]
    image = tf.keras.layers.RandomZoom(0.1)(tf.expand_dims(image, 0))[0]
    image = tf.clip_by_value(image, 0.0, 1.0)
    return image


def make_dataset(split: str, augment_train: bool = True, dataset_dir: str = None) -> tf.data.Dataset:
    if dataset_dir is None:
        dataset_dir = CONFIG["dataset_dir"]

    paths, labels = parse_split_file(dataset_dir, split)
    num_classes = len(load_class_names(dataset_dir))
    print(f"[load_data] {split}: {len(paths)} images, {num_classes} classes")

    path_ds = tf.data.Dataset.from_tensor_slices(paths)
    label_ds = tf.data.Dataset.from_tensor_slices(labels)

    def load_and_preprocess(path):
        return preprocess_path(path)

    image_ds = path_ds.map(load_and_preprocess, num_parallel_calls=CONFIG["autotune"])
    ds = tf.data.Dataset.zip((image_ds, label_ds))

    if split == "train" and augment_train:
        ds = ds.map(lambda img, lbl: (augment(img), lbl), num_parallel_calls=CONFIG["autotune"])

    ds = ds.cache() if split == "test" else ds
    ds = ds.shuffle(1000) if split == "train" else ds
    ds = ds.batch(CONFIG["batch_size"]).prefetch(CONFIG["autotune"])
    return ds


if __name__ == "__main__":
    train_ds = make_dataset("train")
    test_ds = make_dataset("test")
    for images, labels in train_ds.take(1):
        print("train batch - images:", images.shape, "labels:", labels.shape)
    for images, labels in test_ds.take(1):
        print("test batch  - images:", images.shape, "labels:", labels.shape)
