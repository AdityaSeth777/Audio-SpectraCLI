#!/bin/bash

# Function to install requirements
install_requirements() {
    echo "Installing requirements..."
    pip install -r requirements.txt
    echo ""
}

# Function to detect microphone
detect_microphone() {
    echo "Detecting Microphone..."
    echo ""
    python -c "import sounddevice as sd; from tabulate import tabulate; devices = sd.query_devices(); print(tabulate(devices, headers='keys', tablefmt='fancy_grid')) if devices else print('Microphone not detected. Please check your connections.')"
    echo ""
}

# Function to display menu options
display_menu() {
    echo "===================================================="
    echo "            Welcome to Audio-SpectraCLI            "
    echo "===================================================="
    echo ""
    echo "[1] Start Audio Spectrum Visualization"
    echo "[2] Exit"
    echo ""
    read -p "Enter your choice: " choice

    if [ "$choice" = "1" ]; then
        echo ""
        echo "Starting Audio Spectrum Visualization..."
        cd audio_spectrum
        python spectrum.py
        exit
    elif [ "$choice" = "2" ]; then
        exit
    else
        echo "Invalid choice. Please enter 1 or 2."
        display_menu
    fi
}

# Main program
install_requirements
detect_microphone
display_menu