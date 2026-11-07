
import os
import json
import random
import numpy as np
import pandas as pd
import tensorflow as tf

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix

# Reproducibility
SEED = 42
random.seed(SEED)
np.random.seed(SEED)
tf.random.set_seed(SEED)

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "training_data_300.csv")
MODEL_DIR = os.path.join(BASE_DIR, "saved_model")
MODEL_PATH = os.path.join(MODEL_DIR, "contact_classifier.keras")
os.environ["PYTHONUTF8"] = "1"

os.makedirs(MODEL_DIR, exist_ok=True)

# Load dataset
df = pd.read_csv(DATA_PATH)
df = df.dropna(subset=["text", "label"])

texts = df["text"].astype(str).values
labels = df["label"].astype(str).values

# Encode categories
encoder = LabelEncoder()
encoded_labels = encoder.fit_transform(labels)

class_names = encoder.classes_.tolist()
num_classes = len(class_names)

# Split dataset: 80% training, 20% testing
X_train, X_test, y_train, y_test = train_test_split(
    texts,
    encoded_labels,
    test_size=0.20,
    random_state=SEED,
    stratify=encoded_labels
)
# Convert text data to TensorFlow string tensors
X_train = tf.constant(X_train.astype(str), dtype=tf.string)
X_test = tf.constant(X_test.astype(str), dtype=tf.string)

# Text preprocessing layer
vectorizer = tf.keras.layers.TextVectorization(
    max_tokens=10000,
    output_mode="int",
    output_sequence_length=60
)

vectorizer.adapt(X_train)

# Build TensorFlow model
model = tf.keras.Sequential([
    tf.keras.Input(shape=(), dtype=tf.string),
    vectorizer,
    tf.keras.layers.Embedding(
        input_dim=10000,
        output_dim=64,
        mask_zero=True
    ),
    tf.keras.layers.GlobalAveragePooling1D(),
    tf.keras.layers.Dense(64, activation="relu"),
    tf.keras.layers.Dropout(0.3),
    tf.keras.layers.Dense(num_classes, activation="softmax")
])

model.compile(
    optimizer="adam",
    loss="sparse_categorical_crossentropy",
    metrics=["accuracy"]
)

# Train model
early_stopping = tf.keras.callbacks.EarlyStopping(
    monitor="val_loss",
    patience=5,
    restore_best_weights=True
)

history = model.fit(
    X_train,
    y_train,
    validation_split=0.20,
    epochs=40,
    batch_size=16,
    callbacks=[early_stopping],
    verbose=1
)

# Evaluate model
loss, accuracy = model.evaluate(X_test, y_test, verbose=0)

predictions = model.predict(X_test, verbose=0)
predicted_labels = np.argmax(predictions, axis=1)

print("\n========== TEST RESULTS ==========")
print(f"Test Loss: {loss:.4f}")
print(f"Test Accuracy: {accuracy * 100:.2f}%")

print("\n========== CLASSIFICATION REPORT ==========")
print(classification_report(
    y_test,
    predicted_labels,
    labels=np.arange(num_classes),
    target_names=class_names,
    zero_division=0
))

print("\n========== CONFUSION MATRIX ==========")
print(confusion_matrix(y_test, predicted_labels))

# Save model and category names
model.save(MODEL_PATH)

with open(
    os.path.join(MODEL_DIR, "class_names.json"),
    "w",
    encoding="utf-8"
) as file:
    json.dump(class_names, file, ensure_ascii=False, indent=4)

print("\nModel saved:", MODEL_PATH)
print("Category names saved successfully.")
