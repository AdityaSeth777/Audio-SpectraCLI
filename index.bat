@echo off

REM Function to install requirements
:install_requirements
echo Installing requirements...
pip install -r requirements.txt

REM Function to display menu options
:display_menu
cls
echo Welcome to Audio Spectrum Visualization
echo 1. Start
echo 2. Exit
set /p choice=Enter your choice: 
if "%choice%"=="1" goto start
if "%choice%"=="2" exit /b

:start
echo Starting Audio Spectrum Visualization...
cd audio_spectrum
python spectrum.py