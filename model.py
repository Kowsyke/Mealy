# Mealy — neural network definition
# MobileNetV2 base (frozen, pretrained on ImageNet) + custom classification head
# Outputs probabilities across 101 food classes via softmax
import tensorflow as tf
from preprocess import INPUT_SHAPE

NUM_CLASSES = 101
FINE_TUNE_LAYERS = 30  # unfreeze this many layers from the top for phase 2


def build_model(num_classes: int = NUM_CLASSES) -> tf.keras.Model:
    base = tf.keras.applications.MobileNetV2(
        input_shape=INPUT_SHAPE,
        include_top=False,
        weights="imagenet",
    )
    base.trainable = False

    inputs = tf.keras.Input(shape=INPUT_SHAPE)
    x = base(inputs, training=False)
    x = tf.keras.layers.GlobalAveragePooling2D()(x)
    x = tf.keras.layers.Dense(256, activation="relu")(x)
    x = tf.keras.layers.Dropout(0.4)(x)
    outputs = tf.keras.layers.Dense(num_classes, activation="softmax")(x)

    return tf.keras.Model(inputs, outputs)


def unfreeze_top_layers(model: tf.keras.Model, n: int = FINE_TUNE_LAYERS) -> None:
    """Unfreeze top n layers of the base for phase 2 fine-tuning."""
    base = model.layers[1]  # MobileNetV2 is the second layer
    base.trainable = True
    for layer in base.layers[:-n]:
        layer.trainable = False
    print(f"[model] Unfroze top {n} layers of MobileNetV2 base")


if __name__ == "__main__":
    m = build_model()
    m.summary()
    print("Trainable params (phase 1):", sum(tf.size(w).numpy() for w in m.trainable_weights))
    unfreeze_top_layers(m)
    print("Trainable params (phase 2):", sum(tf.size(w).numpy() for w in m.trainable_weights))
