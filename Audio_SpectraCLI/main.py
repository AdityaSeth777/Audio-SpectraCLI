# Aditya Seth
# Description: This file contains the main code for the Audio-SpectraCLI project.
# It is responsible for creating the AudioSpectrumVisualizer class which is used
# to visualize the audio spectrum in real-time.

import numpy as np
import matplotlib.pyplot as plt
import sounddevice as sd
import queue
import threading
from scipy.ndimage import gaussian_filter1d
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget, QSlider
from PyQt5.QtCore import Qt, QTimer
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class AudioSpectrumVisualizer(QMainWindow):
    def __init__(self, duration=10, fs=44100, block_size=4096, frequency_range=(20, 20000), color='blue'):
        super().__init__()
        self.setWindowTitle('Audio Spectrum Visualizer')
        self.setGeometry(100, 100, 800, 600)

        self.duration = duration  # Duration in seconds
        self.fs = fs  # Sampling rate
        self.block_size = block_size  # Block size
        self.frequency_range = frequency_range  # Frequency range
        self.color = color  # Color

        self.audio_queue = queue.Queue()
        self.spectrum = np.zeros(self.block_size)

        self.noise_threshold = 0.05  # Adjusted for lower noise level
        self.running = False
        self.stream = None

        self.setup_ui()

    def setup_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()

        self.canvas = FigureCanvas(Figure(figsize=(5, 3)))
        self.ax = self.canvas.figure.add_subplot(111)
        self.layout.addWidget(self.canvas)

        self.duration_slider = QSlider(Qt.Horizontal)
        self.duration_slider.setMinimum(1)
        self.duration_slider.setMaximum(10)
        self.duration_slider.setValue(self.duration)
        self.duration_slider.setTickInterval(1)
        self.duration_slider.setTickPosition(QSlider.TicksBelow)
        self.duration_slider.valueChanged.connect(self.set_duration)
        self.layout.addWidget(QLabel('Duration (seconds):'))
        self.layout.addWidget(self.duration_slider)

        self.fs_slider = QSlider(Qt.Horizontal)
        self.fs_slider.setMinimum(22050)
        self.fs_slider.setMaximum(44100)
        self.fs_slider.setValue(self.fs)
        self.fs_slider.setTickInterval(11025)
        self.fs_slider.setTickPosition(QSlider.TicksBelow)
        self.fs_slider.valueChanged.connect(self.set_sampling_rate)
        self.layout.addWidget(QLabel('Sampling Rate (Hz):'))
        self.layout.addWidget(self.fs_slider)

        self.block_size_slider = QSlider(Qt.Horizontal)
        self.block_size_slider.setMinimum(256)
        self.block_size_slider.setMaximum(8192)
        self.block_size_slider.setValue(self.block_size)
        self.block_size_slider.setTickInterval(512)
        self.block_size_slider.setTickPosition(QSlider.TicksBelow)
        self.block_size_slider.valueChanged.connect(self.set_block_size)
        self.layout.addWidget(QLabel('Block Size:'))
        self.layout.addWidget(self.block_size_slider)

        self.start_button = QPushButton('Start Visualization')
        self.start_button.clicked.connect(self.toggle_visualization)
        self.layout.addWidget(self.start_button)

        self.central_widget.setLayout(self.layout)

    def audio_callback(self, indata, frames, time, status):
        if status:
            print(status)
        self.audio_queue.put(indata.copy())

    def process_audio(self):
        while self.running:
            if not self.audio_queue.empty():
                audio_block = self.audio_queue.get()
                spectrum = np.abs(np.fft.rfft(
                    audio_block[:, 0], n=self.block_size))
                spectrum = gaussian_filter1d(
                    spectrum, sigma=2)  # Apply smoothing filter
                max_magnitude = np.max(spectrum)
                print(f'Max magnitude: {max_magnitude}')  # Debugging print
                if max_magnitude > self.noise_threshold:
                    self.update_plot(spectrum, max_magnitude)

    def update_plot(self, spectrum, max_magnitude):
        freq_bins = np.fft.rfftfreq(self.block_size, 1 / self.fs)
        self.ax.clear()
        self.ax.plot(freq_bins, spectrum, color=self.color)
        self.ax.set_xlim(self.frequency_range)
        self.ax.set_ylim(0, max_magnitude * 0.5)
        self.ax.set_xlabel('Frequency (Hz)')
        self.ax.set_ylabel('Magnitude')
        self.ax.set_title('Audio Spectrum Visualization')
        self.canvas.draw()

    def set_duration(self, value):
        self.duration = value

    def set_sampling_rate(self, value):
        self.fs = value

    def set_block_size(self, value):
        self.block_size = value

    def toggle_visualization(self):
        if self.running:
            self.running = False
            if self.stream is not None:
                self.stream.stop()
                self.stream.close()
            self.start_button.setText('Start Visualization')
        else:
            self.running = True
            sd.default.samplerate = self.fs
            sd.default.channels = 1
            self.stream = sd.InputStream(callback=self.audio_callback)
            self.stream.start()
            audio_thread = threading.Thread(
                target=self.process_audio, daemon=True)
            audio_thread.start()
            self.start_button.setText('Stop Visualization')

    def closeEvent(self, event):
        self.running = False
        if self.stream is not None:
            self.stream.stop()
            self.stream.close()
        event.accept()


__all__ = ['AudioSpectrumVisualizer']
