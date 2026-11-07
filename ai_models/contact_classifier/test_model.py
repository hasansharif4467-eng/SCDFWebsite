import os
import json
import tensorflow as tf

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "saved_model", "contact_classifier.keras")
CLASS_PATH = os.path.join(BASE_DIR, "saved_model", "class_names.json")

# Load trained model
model = tf.keras.models.load_model(MODEL_PATH)

# Load category names
with open(CLASS_PATH, "r", encoding="utf-8") as file:
    class_names = json.load(file)

# Test messages
test_messages = [
    "I want to become a volunteer for your organization.",
    "আমি আপনাদের সাথে পার্টনারশিপ করতে চাই।",
    "Training er jonno apply korte chai.",
    "Your organization did not respond to my complaint."
]

print("\n========== AI PREDICTION RESULTS ==========\n")

for message in test_messages:
    prediction = model.predict(
        tf.constant([message]),
        verbose=0
    )

    predicted_index = prediction[0].argmax()
    category = class_names[predicted_index]
    confidence = prediction[0][predicted_index] * 100

    print("Message:", message)
    print("Predicted Category:", category)
    print(f"Confidence: {confidence:.2f}%")
    print("-" * 50)