import json
import os

with open(os.path.join(os.path.dirname(__file__), "fruit_classes.json")) as _f:
    FRUIT_CLASSES = json.load(_f)
