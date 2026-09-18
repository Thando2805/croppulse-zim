# image_processor.py
import cv2
import numpy as np
import os

class ImageProcessor:
    @staticmethod
    def enhance_image(image_path):
        """Enhance image quality for better analysis"""
        try:
            img = cv2.imread(image_path)
            if img is None:
                return image_path
            
            # Adjust contrast and brightness
            alpha = 1.2  # Contrast
            beta = 20    # Brightness
            adjusted = cv2.convertScaleAbs(img, alpha=alpha, beta=beta)
            
            # Sharpen
            kernel = np.array([[-1,-1,-1],
                              [-1, 9,-1],
                              [-1,-1,-1]])
            sharpened = cv2.filter2D(adjusted, -1, kernel)
            
            # Save enhanced image
            enhanced_path = "enhanced_temp.jpg"
            cv2.imwrite(enhanced_path, sharpened)
            return enhanced_path
        except Exception as e:
            print(f"Enhancement error: {e}")
            return image_path
    
    @staticmethod
    def crop_leaf(image_path):
        """Auto-crop leaf from background"""
        try:
            img = cv2.imread(image_path)
            if img is None:
                return image_path
            
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Threshold
            _, thresh = cv2.threshold(gray, 40, 255, cv2.THRESH_BINARY)
            
            # Find contours
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if contours:
                # Get bounding box of largest contour
                cnt = max(contours, key=cv2.contourArea)
                x, y, w, h = cv2.boundingRect(cnt)
                
                # Crop image
                cropped = img[y:y+h, x:x+w]
                cropped_path = "cropped_temp.jpg"
                cv2.imwrite(cropped_path, cropped)
                return cropped_path
            
            return image_path
        except Exception as e:
            print(f"Crop error: {e}")
            return image_path
    
    @staticmethod
    def cleanup_temp():
        """Remove temporary files"""
        temp_files = ["enhanced_temp.jpg", "cropped_temp.jpg"]
        for file in temp_files:
            if os.path.exists(file):
                try:
                    os.remove(file)
                except:
                    pass