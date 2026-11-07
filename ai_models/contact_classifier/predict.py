import os
import sys
import json
from pathlib import Path

os.environ["PYTHONUTF8"] = "1"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

import tensorflow as tf

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "saved_model" / "contact_classifier.keras"
CLASS_PATH = BASE_DIR / "saved_model" / "class_names.json"


def predict_message(message):
    if not isinstance(message, str) or not message.strip():
        raise ValueError("Message cannot be empty.")

    with open(CLASS_PATH, "r", encoding="utf-8") as file:
        class_names = json.load(file)

    model = tf.keras.models.load_model(
        MODEL_PATH,
        compile=False
    )

    prediction = model.predict(
        tf.constant([message.strip()]),
        verbose=0
    )

    predicted_index = int(prediction[0].argmax())
    category = class_names[predicted_index]
    confidence = float(prediction[0][predicted_index]) * 100

    return {
        "success": True,
        "category": category,
        "confidence": round(confidence, 2)
    }


if __name__ == "__main__":
    try:
        data = json.load(sys.stdin)
        message = data.get("message", "")

        result = predict_message(message)

        print(json.dumps(result, ensure_ascii=False))

    except Exception as error:
        print(
            json.dumps({
                "success": False,
                "error": str(error)
            }, ensure_ascii=False),
            file=sys.stderr
        )
        sys.exit(1)
