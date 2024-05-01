import numpy as np
import matplotlib.pyplot as plt
import sounddevice as sd
import queue
import threading
import time
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
from PyQt5.QtCore import QTimer, QObject, pyqtSignal, pyqtSlot


class AudioWorker(QObject):
    finished = pyqtSignal()

    def __init__(self, duration, fs, block_size, frequency_range, color):
        super().__init__()
        self.duration = duration
        self.fs = fs
        self.block_size = block_size
        self.num_blocks = int(duration * fs / block_size)
        self.frequency_range = frequency_range
        self.color = color
        self.audio_queue = queue.Queue()

    @pyqtSlot()
    def process_audio(self):
        freq_bins = np.fft.fftfreq(self.block_size, 1 / self.fs)
        spectrum = np.zeros(self.block_size)

        plt.ion()
        self.fig, self.ax = plt.subplots()
        self.x = np.arange(0, self.block_size)
        self.line, = self.ax.plot(freq_bins, spectrum, color=self.color)
        self.ax.set_xlim(self.frequency_range)
        self.ax.set_ylim(0, 0.1)
        self.ax.set_title('Audio-SpectraCLI Visualization')
        self.ax.set_xlabel('Frequency (Hz)')
        self.ax.set_ylabel('Magnitude')

        while True:
            audio_block = self.audio_queue.get()
            spectrum = np.abs(np.fft.fft(audio_block[:, 0], n=self.block_size))
            max_magnitude = np.max(spectrum)
            if max_magnitude > self.ax.get_ylim()[1]:
                self.ax.set_ylim(0, max_magnitude * 1.1)
            self.line.set_ydata(spectrum)
            self.fig.canvas.draw()
            self.fig.canvas.flush_events()

    def start(self):
        self.thread = threading.Thread(target=self.process_audio, daemon=True)
        self.thread.start()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Audio-SpectraCLI')
        self.setGeometry(100, 100, 600, 400)

        self.start_button = QPushButton('Start Visualization')
        self.start_button.clicked.connect(self.start_visualization)

        layout = QVBoxLayout()
        layout.addWidget(self.start_button)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self.audio_worker = AudioWorker(
            duration=10, fs=44100, block_size=2048, frequency_range=(20, 20000), color='blue')

    def start_visualization(self):
        self.audio_worker.start()


if __name__ == '__main__':
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()
