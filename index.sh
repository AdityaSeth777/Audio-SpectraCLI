#!/bin/bash

install_requirements() {
    echo "Installing requirements..."
    pip install -r requirements.txt
}

display_menu() {
    echo "Welcome to Audio Spectrum Visualization"
    echo "1. Start"
    echo "2. Exit"
    read -p "Enter your choice: " choice
    case $choice in
        1) start ;;
        2) exit ;;
        *) echo "Invalid choice. Please enter 1 or 2." ;;
    esac
}

start() {
    echo "Starting Audio Spectrum Visualization..."
    cd audio_spectrum
    python spectrum.py
}

install_requirements
display_menu