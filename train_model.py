# train_model.py - FIXED VERSION
import tensorflow as tf
from tensorflow.keras import layers, models, callbacks
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.applications import MobileNetV2
import os
import json
import numpy as np
from datetime import datetime

print("=" * 60)
print("MAIZE AND TOMATO DISEASE DETECTION")
print("MODEL TRAINING - FIXED VERSION")
print("=" * 60)

# ============================================
# STEP 1: CHECK TRAINING DATA
# ============================================
if not os.path.exists("training_data"):
    print("ERROR: training_data folder not found!")
    exit()

# Count classes
folders = []
total_images = 0
for item in os.listdir("training_data"):
    folder_path = os.path.join("training_data", item)
    if os.path.isdir(folder_path):
        img_count = len([f for f in os.listdir(folder_path) 
                        if f.endswith(('.jpg', '.png', '.jpeg'))])
        if img_count > 0:
            folders.append((item, img_count))
            total_images += img_count

if len(folders) < 2:
    print(f"ERROR: Only {len(folders)} classes found. Need at least 2.")
    exit()

print(f"\nFound {len(folders)} classes with {total_images} total images:")
for name, count in sorted(folders):
    print(f"  - {name}: {count} images")

# ============================================
# STEP 2: CONFIGURATION
# ============================================
IMG_SIZE = (224, 224)
BATCH_SIZE = 32
EPOCHS = 30

# ============================================
# STEP 3: LOAD DATA - FIXED
# ============================================
print("\nLoading data...")

train_datagen = ImageDataGenerator(
    rescale=1./255,
    rotation_range=20,
    width_shift_range=0.2,
    height_shift_range=0.2,
    shear_range=0.2,
    zoom_range=0.2,
    horizontal_flip=True,
    fill_mode='nearest',
    validation_split=0.2
)

train_generator = train_datagen.flow_from_directory(
    'training_data',
    target_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    class_mode='categorical',
    subset='training',
    shuffle=True
)

validation_generator = train_datagen.flow_from_directory(
    'training_data',
    target_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    class_mode='categorical',
    subset='validation',
    shuffle=False
)

class_names = list(train_generator.class_indices.keys())
NUM_CLASSES = len(class_names)

# FIX: Calculate correct steps
train_steps = max(1, train_generator.samples // BATCH_SIZE)
val_steps = max(1, validation_generator.samples // BATCH_SIZE)

print(f"\nTraining samples: {train_generator.samples}")
print(f"Validation samples: {validation_generator.samples}")
print(f"Training steps: {train_steps}")
print(f"Validation steps: {val_steps}")
print(f"Number of classes: {NUM_CLASSES}")

# ============================================
# STEP 4: BUILD MODEL
# ============================================
print("\nBuilding model...")

base_model = MobileNetV2(
    weights='imagenet',
    include_top=False,
    input_shape=(224, 224, 3)
)
base_model.trainable = False

model = models.Sequential([
    base_model,
    layers.GlobalAveragePooling2D(),
    layers.Dense(256, activation='relu'),
    layers.Dropout(0.5),
    layers.Dense(128, activation='relu'),
    layers.Dropout(0.3),
    layers.Dense(NUM_CLASSES, activation='softmax')
])

model.compile(
    optimizer='adam',
    loss='categorical_crossentropy',
    metrics=['accuracy']
)

print(model.summary())

# ============================================
# STEP 5: CALLBACKS
# ============================================
os.makedirs('models', exist_ok=True)

callbacks = [
    callbacks.ModelCheckpoint(
        'models/best_model.h5',
        monitor='val_accuracy',
        save_best_only=True,
        verbose=1
    ),
    callbacks.EarlyStopping(
        monitor='val_loss',
        patience=7,
        restore_best_weights=True,
        verbose=1
    ),
    callbacks.ReduceLROnPlateau(
        monitor='val_loss',
        factor=0.5,
        patience=3,
        verbose=1
    )
]

# ============================================
# STEP 6: TRAIN - FIXED STEPS
# ============================================
print("\n" + "=" * 60)
print("TRAINING STARTED")
print("=" * 60)

start_time = datetime.now()

history = model.fit(
    train_generator,
    steps_per_epoch=train_steps,      # FIXED: using calculated steps
    epochs=EPOCHS,
    validation_data=validation_generator,
    validation_steps=val_steps,       # FIXED: using calculated steps
    callbacks=callbacks,
    verbose=1
)

end_time = datetime.now()

# ============================================
# STEP 7: SAVE MODEL
# ============================================
print("\nSaving model...")

model.save('models/crop_disease_model.h5')
print("Model saved to: models/crop_disease_model.h5")

# Save class names
class_names_dict = {str(i): name for i, name in enumerate(class_names)}
with open('models/class_names.json', 'w') as f:
    json.dump(class_names_dict, f, indent=2)

# ============================================
# STEP 8: EVALUATE
# ============================================
val_loss, val_accuracy = model.evaluate(validation_generator, steps=val_steps, verbose=0)
best_accuracy = max(history.history['val_accuracy'])

print("\n" + "=" * 60)
print("TRAINING COMPLETE!")
print("=" * 60)
print(f"\nBest Validation Accuracy: {best_accuracy:.2%}")
print(f"Final Validation Accuracy: {val_accuracy:.2%}")
print(f"Training Time: {end_time - start_time}")

print("\nNEXT STEPS:")
print("1. Test: python test_model.py")
print("2. Run app: python app.py")
print("=" * 60)