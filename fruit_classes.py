# Mealy — fruit and vegetable class names
# Loads the 36 fruit/veg category names from fruit_classes.json
# and exposes them as FRUIT_CLASSES — used by the fruit model and detector

import json
import os

with open(os.path.join(os.path.dirname(__file__), "fruit_classes.json")) as _f:
    FRUIT_CLASSES = json.load(_f)
