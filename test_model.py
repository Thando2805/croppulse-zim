# test_model.py
import tensorflow as tf
import numpy as np
from tensorflow.keras.preprocessing import image
import os
import json

print("=" * 60)
print("TESTING TRAINED MODEL")
print("=" * 60)

# Load model
model = tf.keras.models.load_model('models/crop_disease_model.h5')
print("Model loaded successfully!")

# Load class names
with open('models/class_names.json', 'r') as f:
    class_names = json.load(f)

print(f"Model ready for {len(class_names)} classes")

def predict_image(img_path):
    """Predict disease from image"""
    img = image.load_img(img_path, target_size=(224, 224))
    img_array = image.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)
    img_array = img_array / 255.0
    
    predictions = model.predict(img_array, verbose=0)
    predicted_class = np.argmax(predictions[0])
    confidence = np.max(predictions[0]) * 100
    
    disease_name = class_names[str(predicted_class)]
    return disease_name, confidence

# Test with a sample image
test_images = []
for root, dirs, files in os.walk('training_data'):
    for file in files:
        if file.endswith(('.jpg', '.png', '.jpeg')):
            test_images.append(os.path.join(root, file))
            if len(test_images) >= 5:
                break
    if len(test_images) >= 5:
        break

if test_images:
    print("\nTesting 5 sample images...")
    print("-" * 60)
    for img_path in test_images:
        actual = os.path.basename(os.path.dirname(img_path))
        predicted, confidence = predict_image(img_path)
        print(f"Image: {os.path.basename(img_path)}")
        print(f"  Actual: {actual}")
        print(f"  Predicted: {predicted}")
        print(f"  Confidence: {confidence:.2f}%")
        print("  Status: PASS" if predicted == actual else "  Status: FAIL")
        print("-" * 40)
else:
    print("No test images found!")

print("\n" + "=" * 60)