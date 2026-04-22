import os

_classes_file = os.path.join(os.path.dirname(__file__), "food-101", "meta", "classes.txt")

with open(_classes_file) as _f:
    CLASS_NAMES = [line.strip() for line in _f if line.strip()]

assert len(CLASS_NAMES) == 101, f"Expected 101 classes, got {len(CLASS_NAMES)}"
