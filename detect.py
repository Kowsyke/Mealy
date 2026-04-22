import numpy as np
from preprocess import preprocess_array
from class_names import CLASS_NAMES
from calories import get_calories

CONFIDENCE_THRESHOLD = 0.25
MAX_DETECTIONS = 4


def get_regions(frame_rgb):
    h, w = frame_rgb.shape[:2]
    mh, mw = h // 2, w // 2
    return {
        'full': frame_rgb,
        'top_left': frame_rgb[:mh, :mw],
        'top_right': frame_rgb[:mh, mw:],
        'bottom_left': frame_rgb[mh:, :mw],
        'bottom_right': frame_rgb[mh:, mw:],
    }


def detect_foods(model, frame_rgb):
    regions = get_regions(frame_rgb)
    all_preds = {}

    for region_name, region in regions.items():
        preprocessed = preprocess_array(region)
        batch = np.expand_dims(preprocessed, axis=0)
        probs = model.predict(batch, verbose=0)[0]
        top_idx = int(np.argmax(probs))
        top_conf = float(probs[top_idx])

        if top_conf >= CONFIDENCE_THRESHOLD:
            label = CLASS_NAMES[top_idx]
            if label not in all_preds or all_preds[label]['confidence'] < top_conf:
                all_preds[label] = {
                    'class': label,
                    'confidence': top_conf,
                    'calories': get_calories(label),
                    'region': region_name,
                }

    results = sorted(all_preds.values(), key=lambda x: x['confidence'], reverse=True)
    return results[:MAX_DETECTIONS]


def total_calories(detections):
    return sum(d['calories'] for d in detections)
