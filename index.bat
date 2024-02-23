@echo off

REM Function to install requirements
:install_requirements
echo Installing requirements...
pip install -r requirements.txt
echo.

REM Function to detect microphone
:detect_microphone
cls
echo Detecting Microphone...
echo.
python -c "import sounddevice as sd; from tabulate import tabulate; devices = sd.query_devices(); print(tabulate(devices, headers='keys', tablefmt='fancy_grid')) if devices else print('Microphone not detected. Please check your connections.')"
echo.

REM Function to display menu options
:display_menu
echo ====================================================
echo            Welcome to Audio-SpectraCLI
echo ====================================================
echo.
echo [1] Start Audio Spectrum Visualization
echo [2] Exit
echo.
set /p choice=Enter your choice: 

if "%choice%"=="1" (
    echo.
    echo Starting Audio Spectrum Visualization...
    cd audio_spectrum
    python spectrum.py
    goto :EOF
)

if "%choice%"=="2" (
    exit /b
)

echo Invalid choice. Please enter 1 or 2.
goto display_menu