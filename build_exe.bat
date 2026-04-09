@echo off
echo Installing PyInstaller...
pip install pyinstaller

echo Building executable...
pyinstaller --onefile --windowed main.py

echo Build complete. Check the 'dist' folder for the exe file.