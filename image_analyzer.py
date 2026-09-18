# image_analyzer.py - COMPLETE VERSION WITH TRAINED MODEL
import cv2
import numpy as np
from PIL import Image, ImageTk
import os
import json
import tensorflow as tf
from tensorflow.keras.preprocessing import image

class ImageAnalyzer:
    def __init__(self):
        self.model = None
        self.class_names = {}
        self.is_model_loaded = False
        self.load_model()
    
    def load_model(self):
        """Load the trained model and class names"""
        try:
            # Load the trained model
            model_path = "models/crop_disease_model.h5"
            if os.path.exists(model_path):
                self.model = tf.keras.models.load_model(model_path)
                print("Model loaded successfully!")
                
                # Load class names
                class_path = "models/class_names.json"
                if os.path.exists(class_path):
                    with open(class_path, 'r') as f:
                        self.class_names = json.load(f)
                    print(f"Loaded {len(self.class_names)} classes")
                
                self.is_model_loaded = True
                return True
            else:
                print("Model not found! Train first with train_model.py")
                return False
        except Exception as e:
            print(f"Error loading model: {e}")
            return False
    
    def preprocess_image(self, image_path, target_size=(224, 224)):
        """Preprocess image for model prediction"""
        try:
            # Load and preprocess image
            img = image.load_img(image_path, target_size=target_size)
            img_array = image.img_to_array(img)
            img_array = np.expand_dims(img_array, axis=0)
            img_array = img_array / 255.0
            return img_array
        except Exception as e:
            print(f"Error preprocessing image: {e}")
            return None
    
    def analyze_image(self, image_path, crop_type=None):
        """Analyze image and return diagnosis"""
        if not self.is_model_loaded or self.model is None:
            return {
                "status": "warning",
                "message": "Model not loaded. Train first with train_model.py"
            }
        
        try:
            # Preprocess image
            img_array = self.preprocess_image(image_path)
            if img_array is None:
                return {"status": "error", "message": "Failed to process image"}
            
            # Make prediction
            predictions = self.model.predict(img_array, verbose=0)
            predicted_class = np.argmax(predictions[0])
            confidence = np.max(predictions[0]) * 100
            
            # Get disease name
            disease_name = self.class_names.get(str(predicted_class), "Unknown")
            
            # Get recommendations from database
            recommendations = self.get_recommendations(disease_name)
            
            # Get top 3 predictions
            top_indices = np.argsort(predictions[0])[-3:][::-1]
            top_predictions = []
            for idx in top_indices:
                name = self.class_names.get(str(idx), "Unknown")
                conf = predictions[0][idx] * 100
                top_predictions.append({"disease": name, "confidence": conf})
            
            return {
                "status": "success",
                "disease": disease_name,
                "confidence": confidence,
                "predictions": predictions[0].tolist(),
                "top_predictions": top_predictions,
                "recommendations": recommendations
            }
            
        except Exception as e:
            return {"status": "error", "message": f"Analysis failed: {str(e)}"}
    
    def get_recommendations(self, disease_name):
        """Get treatment recommendations from disease database"""
        from disease_data import DISEASE_DB
        
        # Try to find matching disease in database
        for crop, diseases in DISEASE_DB.items():
            for key, info in diseases.items():
                # Check if disease name matches
                if disease_name.lower() in key.replace('_', ' ').lower():
                    return {
                        "cause": info.get('cause', 'Unknown'),
                        "treatment": info.get('treatment', 'Consult local expert'),
                        "severity": info.get('severity', 'Medium')
                    }
        
        # Try to match by keywords
        for crop, diseases in DISEASE_DB.items():
            for key, info in diseases.items():
                # Check if any symptom matches
                for symptom in info.get('symptoms', []):
                    if symptom.lower() in disease_name.lower():
                        return {
                            "cause": info.get('cause', 'Unknown'),
                            "treatment": info.get('treatment', 'Consult local expert'),
                            "severity": info.get('severity', 'Medium')
                        }
        
        return {
            "cause": "Could not determine",
            "treatment": "Consult local agricultural expert",
            "severity": "Unknown"
        }
    
    def capture_from_camera(self):
        """Capture image from webcam"""
        try:
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                return None
            
            cv2.namedWindow("Press SPACE to capture, ESC to cancel")
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                cv2.imshow("Press SPACE to capture, ESC to cancel", frame)
                
                key = cv2.waitKey(1)
                if key == 32:  # SPACE key
                    temp_path = "temp_capture.jpg"
                    cv2.imwrite(temp_path, frame)
                    cap.release()
                    cv2.destroyAllWindows()
                    return temp_path
                elif key == 27:  # ESC key
                    cap.release()
                    cv2.destroyAllWindows()
                    return None
            
            cap.release()
            cv2.destroyAllWindows()
            return None
        except Exception as e:
            print(f"Camera error: {e}")
            return None