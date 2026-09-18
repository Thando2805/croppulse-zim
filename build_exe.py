import subprocess
import sys

subprocess.check_call([
    sys.executable, "-m", "PyInstaller",
    "--noconfirm",
    "--onedir",
    "--windowed",
    "--add-data", "models;models",
    "--add-data", "disease_data.py;.",
    "--add-data", "diagnostic_engine.py;.",
    "--add-data", "image_analyzer.py;.",
    "--hidden-import", "tensorflow",
    "--hidden-import", "PIL",
    "--hidden-import", "cv2",
    "--name", "CropPulse",
    "app.py"
])