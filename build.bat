@echo off
echo ========================================
echo Building CropPulse Executable
echo ========================================

echo Cleaning previous builds...
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul

echo Building executable...
pyinstaller --noconfirm --onedir --windowed ^
    --add-data "models;models" ^
    --add-data "crop_history.db;." ^
    --hidden-import tensorflow ^
    --hidden-import PIL ^
    --hidden-import cv2 ^
    --hidden-import reportlab ^
    --name "CropPulse" ^
    app.py

echo.
echo ========================================
echo Build Complete!
echo Executable in: dist\CropPulse\CropPulse.exe
echo ========================================
pause