# Aditya Seth
# Description: This file contains the main code for the Audio-SpectraCLI project.
# It is responsible for creating the AudioSpectrumVisualizer class which is used
# to visualize the audio spectrum in real-time.

import numpy as np
import matplotlib.pyplot as plt
import sounddevice as sd
import queue
import threading
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget, QSlider
from PyQt5.QtCore import Qt, QTimer


class AudioSpectrumVisualizer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Audio Spectrum Visualizer')
        self.setGeometry(100, 100, 800, 600)

        self.duration = 5  # Default duration in seconds
        self.fs = 44100  # Default sampling rate
        self.block_size = 2048  # Default block size
        self.frequency_range = (20, 20000)  # Default frequency range
        self.color = 'blue'  # Default color

        self.audio_queue = queue.Queue()
        self.spectrum = np.zeros(self.block_size)

        self.setup_ui()
        self.start_audio_capture()

        self.timer = QTimer()
        self.timer.timeout.connect(self.process_audio)
        self.timer.start(100)

    def setup_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()

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
        self.fs_slider.setTickInterval(22050)
        self.fs_slider.setTickPosition(QSlider.TicksBelow)
        self.fs_slider.valueChanged.connect(self.set_sampling_rate)
        self.layout.addWidget(QLabel('Sampling Rate (Hz):'))
        self.layout.addWidget(self.fs_slider)

        self.block_size_slider = QSlider(Qt.Horizontal)
        self.block_size_slider.setMinimum(256)
        self.block_size_slider.setMaximum(4096)
        self.block_size_slider.setValue(self.block_size)
        self.block_size_slider.setTickInterval(512)
        self.block_size_slider.setTickPosition(QSlider.TicksBelow)
        self.block_size_slider.valueChanged.connect(self.set_block_size)
        self.layout.addWidget(QLabel('Block Size:'))
        self.layout.addWidget(self.block_size_slider)

        self.start_button = QPushButton('Start Visualization')
        self.start_button.clicked.connect(self.start_visualization)
        self.layout.addWidget(self.start_button)

        self.central_widget.setLayout(self.layout)

    def start_audio_capture(self):
        def audio_callback(indata, frames, time, status):
            if status:
                print(status)
            self.audio_queue.put(indata.copy())

        self.stream = sd.InputStream(callback=audio_callback, channels=1, samplerate=self.fs)
        self.stream.start()

    def process_audio(self):
        if not self.audio_queue.empty():
            audio_block = self.audio_queue.get()
            self.spectrum = np.abs(np.fft.fft(audio_block[:, 0], n=self.block_size))
            self.update_plot()

    def update_plot(self):
        freq_bins = np.fft.fftfreq(self.block_size, 1 / self.fs)
        max_magnitude = np.max(self.spectrum)
        plt.clf()
        plt.plot(freq_bins[:self.block_size // 2], self.spectrum[:self.block_size // 2], color=self.color)
        plt.xlim(self.frequency_range)
        plt.ylim(0, max_magnitude * 1.1)
        plt.xlabel('Frequency (Hz)')
        plt.ylabel('Magnitude')
        plt.title('Audio Spectrum Visualization')
        plt.pause(0.001)

    def set_duration(self, value):
        self.duration = value

    def set_sampling_rate(self, value):
        self.fs = value

    def set_block_size(self, value):
        self.block_size = value
        self.spectrum = np.zeros(self.block_size)  # Reset spectrum array size

    def start_visualization(self):
        self.timer.start(100)


if __name__ == '__main__':
    app = QApplication([])
    window = AudioSpectrumVisualizer()
    window.show()
    app.exec_()
