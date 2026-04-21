# Mealy - food classifier
# shared preprocessing - same function used in training, flask api, and demo
# developed with help from Claude AI
import tensorflow as tf

IMAGE_SIZE = 224
INPUT_SHAPE = (IMAGE_SIZE, IMAGE_SIZE, 3)


def preprocess_image(image: tf.Tensor) -> tf.Tensor:
    """Resize to 224x224 and normalise to [0, 1]."""
    image = tf.image.resize(image, [IMAGE_SIZE, IMAGE_SIZE])
    image = tf.cast(image, tf.float32) / 255.0
    return image


def preprocess_path(path: str) -> tf.Tensor:
    """Load a JPEG from disk and preprocess."""
    raw = tf.io.read_file(path)
    image = tf.image.decode_jpeg(raw, channels=3)
    return preprocess_image(image)


def preprocess_pil(pil_image) -> tf.Tensor:
    """Convert a PIL Image to a preprocessed tensor."""
    import numpy as np
    arr = np.array(pil_image.convert("RGB"), dtype=np.float32)
    image = tf.constant(arr)
    return preprocess_image(image)
