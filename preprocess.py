import io
import numpy as np
import tensorflow as tf
from PIL import Image

IMAGE_SIZE = 224
INPUT_SHAPE = (IMAGE_SIZE, IMAGE_SIZE, 3)


def _resize_norm(image: tf.Tensor) -> tf.Tensor:
    image = tf.image.resize(image, [IMAGE_SIZE, IMAGE_SIZE])
    return tf.cast(image, tf.float32) / 255.0


def preprocess_path(path: str) -> tf.Tensor:
    raw = tf.io.read_file(path)
    image = tf.image.decode_jpeg(raw, channels=3)
    return _resize_norm(image)


def preprocess_array(img_array: np.ndarray) -> np.ndarray:
    img = Image.fromarray(img_array.astype(np.uint8)).convert("RGB")
    img = img.resize((IMAGE_SIZE, IMAGE_SIZE))
    return np.array(img, dtype=np.float32) / 255.0


def preprocess_pil(pil_image) -> np.ndarray:
    img = pil_image.convert("RGB").resize((IMAGE_SIZE, IMAGE_SIZE))
    return np.array(img, dtype=np.float32) / 255.0


def preprocess_bytes(image_bytes: bytes) -> np.ndarray:
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img = img.resize((IMAGE_SIZE, IMAGE_SIZE))
    arr = np.array(img, dtype=np.float32) / 255.0
    return arr[np.newaxis]  # (1, 224, 224, 3)
