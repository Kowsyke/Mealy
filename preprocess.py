import io
import numpy as np
import tensorflow as tf
from PIL import Image

IMAGE_SIZE = 224
INPUT_SHAPE = (IMAGE_SIZE, IMAGE_SIZE, 3)


def preprocess_array(img_array):
    img = tf.image.resize(img_array, [IMAGE_SIZE, IMAGE_SIZE])
    img = tf.cast(img, tf.float32) / 255.0
    return img.numpy()


def preprocess_pil(pil_image):
    arr = np.array(pil_image.convert("RGB"))
    return preprocess_array(arr)


def preprocess_bytes(image_bytes):
    img = tf.image.decode_image(image_bytes, channels=3, expand_animations=False)
    img = tf.image.resize(img, [IMAGE_SIZE, IMAGE_SIZE])
    img = tf.cast(img, tf.float32) / 255.0
    return np.expand_dims(img.numpy(), axis=0)


def preprocess_cv2_frame(frame_bgr):
    import cv2
    rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    return preprocess_array(rgb)


def preprocess_path(path):
    raw = tf.io.read_file(path)
    image = tf.image.decode_jpeg(raw, channels=3)
    image = tf.image.resize(image, [IMAGE_SIZE, IMAGE_SIZE])
    return (tf.cast(image, tf.float32) / 255.0).numpy()
