# Mealy - food image classifier
# kaggle training script - combined dataset version
# developed with help from Claude AI

import os
import h5py
import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt

DATASET_BASE = '/kaggle/input/datasets/kmader/food41'
SAVE_DIR     = '/kaggle/working'
IMAGE_SIZE   = 224
BATCH_SIZE   = 64
AUTOTUNE     = tf.data.AUTOTUNE
NUM_CLASSES  = 101
INPUT_SHAPE  = (IMAGE_SIZE, IMAGE_SIZE, 3)

PHASE1_EPOCHS    = 20
PHASE2_EPOCHS    = 20
PHASE1_LR        = 1e-3
PHASE2_LR        = 1e-5
FINE_TUNE_LAYERS = 30

print("TF version:", tf.__version__)
print("GPU:", tf.config.list_physical_devices('GPU'))

def load_h5(filepath):
    print(f"  Loading {os.path.basename(filepath)}...")
    with h5py.File(filepath, 'r') as f:
        X = f['images'][:]
        y_onehot = f['category'][:]
    y = np.argmax(y_onehot, axis=1).astype(np.int32)
    X = X.astype(np.float32) / 255.0
    return X, y

# combine 64x64 (10099 images) and 384x384 (1000 images) for training
# more data beats higher resolution when both are getting resized anyway
print("\nLoading training data...")
X1, y1 = load_h5(os.path.join(DATASET_BASE, 'food_c101_n10099_r64x64x3.h5'))
X2, y2 = load_h5(os.path.join(DATASET_BASE, 'food_c101_n1000_r384x384x3.h5'))

# resize the 384x384 images down to match before combining
# (they get resized to 224 in the pipeline anyway, this saves RAM)
X2_small = tf.image.resize(X2, [64, 64]).numpy()

X_train = np.concatenate([X1, X2_small], axis=0)
y_train = np.concatenate([y1, y2], axis=0)

# shuffle combined dataset
idx = np.random.permutation(len(X_train))
X_train = X_train[idx]
y_train = y_train[idx]

print(f"\nCombined train: {X_train.shape} — {len(np.unique(y_train))} classes")
print(f"Images per class: ~{len(X_train) // NUM_CLASSES}")

# test set
print("\nLoading test data...")
X_test, y_test = load_h5(os.path.join(DATASET_BASE, 'food_test_c101_n1000_r64x64x3.h5'))
print(f"Test: {X_test.shape}")

# sensible augmentation - no vertical flip, food is not upside down
def resize_img(img, label):
    img = tf.image.resize(img, [IMAGE_SIZE, IMAGE_SIZE])
    return img, label

def augment(img, label):
    img = tf.image.random_flip_left_right(img)
    img = tf.image.random_brightness(img, 0.15)
    img = tf.image.random_contrast(img, 0.85, 1.15)
    img = tf.image.random_saturation(img, 0.85, 1.15)
    # small random crop for positional variety
    img = tf.image.resize_with_crop_or_pad(img, IMAGE_SIZE + 16, IMAGE_SIZE + 16)
    img = tf.image.random_crop(img, [IMAGE_SIZE, IMAGE_SIZE, 3])
    img = tf.clip_by_value(img, 0.0, 1.0)
    return img, label

train_ds = tf.data.Dataset.from_tensor_slices((X_train, y_train))
train_ds = train_ds.map(resize_img, num_parallel_calls=AUTOTUNE)
train_ds = train_ds.map(augment, num_parallel_calls=AUTOTUNE)
train_ds = train_ds.shuffle(5000).batch(BATCH_SIZE).prefetch(AUTOTUNE)

test_ds = tf.data.Dataset.from_tensor_slices((X_test, y_test))
test_ds = test_ds.map(resize_img, num_parallel_calls=AUTOTUNE)
test_ds = test_ds.batch(BATCH_SIZE).prefetch(AUTOTUNE)

print(f"\nTrain batches: {len(train_ds)}, Test batches: {len(test_ds)}")

# simpler head - single dense layer works better with small data
def build_model():
    base = tf.keras.applications.MobileNetV2(
        input_shape=INPUT_SHAPE, include_top=False, weights='imagenet'
    )
    base.trainable = False
    inputs  = tf.keras.Input(shape=INPUT_SHAPE)
    x       = base(inputs, training=False)
    x       = tf.keras.layers.GlobalAveragePooling2D()(x)
    x       = tf.keras.layers.Dense(256, activation='relu')(x)
    x       = tf.keras.layers.Dropout(0.4)(x)
    outputs = tf.keras.layers.Dense(NUM_CLASSES, activation='softmax')(x)
    return tf.keras.Model(inputs, outputs)

model = build_model()
model.summary()

# phase 1 - train head, all 20 epochs, no early stopping
model.compile(
    optimizer=tf.keras.optimizers.Adam(PHASE1_LR),
    loss='sparse_categorical_crossentropy',
    metrics=['accuracy'],
)

p1_ckpt = os.path.join(SAVE_DIR, 'mealy_checkpoint_p1.keras')
print("\nPhase 1: training head (20 epochs)...")
h1 = model.fit(
    train_ds,
    epochs=PHASE1_EPOCHS,
    validation_data=test_ds,
    callbacks=[
        tf.keras.callbacks.ModelCheckpoint(
            p1_ckpt, save_best_only=True,
            monitor='val_accuracy', verbose=1
        ),
    ]
)

model.load_weights(p1_ckpt)
p1_best = max(h1.history['val_accuracy'])
print(f"\nPhase 1 best val_accuracy: {p1_best:.4f} ({p1_best*100:.1f}%)")

# phase 2 - unfreeze top 30 layers
base_model = model.layers[1]
base_model.trainable = True
for layer in base_model.layers[:-FINE_TUNE_LAYERS]:
    layer.trainable = False

model.compile(
    optimizer=tf.keras.optimizers.Adam(PHASE2_LR),
    loss='sparse_categorical_crossentropy',
    metrics=['accuracy'],
)

p2_ckpt = os.path.join(SAVE_DIR, 'mealy_checkpoint_p2.keras')
print(f"\nPhase 2: fine-tuning top {FINE_TUNE_LAYERS} layers (20 epochs)...")
h2 = model.fit(
    train_ds,
    epochs=PHASE2_EPOCHS,
    validation_data=test_ds,
    callbacks=[
        tf.keras.callbacks.ModelCheckpoint(
            p2_ckpt, save_best_only=True,
            monitor='val_accuracy', verbose=1
        ),
    ]
)

model.load_weights(p2_ckpt)
p2_best = max(h2.history['val_accuracy'])
print(f"\nPhase 2 best val_accuracy: {p2_best:.4f} ({p2_best*100:.1f}%)")

# save
model.save(os.path.join(SAVE_DIR, 'mealy_model.keras'))
print(f"Model saved.")

# training curves
acc      = h1.history['accuracy']     + h2.history['accuracy']
val_acc  = h1.history['val_accuracy'] + h2.history['val_accuracy']
loss     = h1.history['loss']         + h2.history['loss']
val_loss = h1.history['val_loss']     + h2.history['val_loss']
ep       = range(1, len(acc) + 1)
split_ep = len(h1.history['accuracy'])

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
axes[0].plot(ep, acc, label='Train')
axes[0].plot(ep, val_acc, label='Val')
axes[0].axvline(split_ep, color='grey', linestyle='--', label='Fine-tune start')
axes[0].set_title('Accuracy')
axes[0].set_xlabel('Epoch')
axes[0].legend()
axes[1].plot(ep, loss, label='Train')
axes[1].plot(ep, val_loss, label='Val')
axes[1].axvline(split_ep, color='grey', linestyle='--')
axes[1].set_title('Loss')
axes[1].set_xlabel('Epoch')
axes[1].legend()
plt.tight_layout()
plt.savefig(os.path.join(SAVE_DIR, 'training_curves.png'))
plt.show()

# final
print("\nFinal test evaluation:")
test_loss, test_acc = model.evaluate(test_ds, verbose=1)
print(f"\nTest accuracy: {test_acc:.4f}  |  Test loss: {test_loss:.4f}")
print(f"Top-1 accuracy: {test_acc*100:.1f}%")