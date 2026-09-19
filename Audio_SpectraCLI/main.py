# Aditya Seth
# Description: This file contains the main code for the Audio-SpectraCLI project.
# It is responsible for creating the AudioSpectrumVisualizer class which is used
# to visualize the audio spectrum in real-time.

from PyQt5.QtWidgets import QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget, QSlider
from PyQt5.QtCore import Qt, QTimer
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from .engine import AudioSpectrumEngine

RENDER_INTERVAL_MS = 33  # ~30fps redraw cap, independent of the audio block rate


class AudioSpectrumVisualizer(QMainWindow):
    def __init__(self, duration=10, fs=44100, block_size=4096, frequency_range=(20, 20000), color='blue', device=None):
        super().__init__()
        self.setWindowTitle('Audio Spectrum Visualizer')
        self.setGeometry(100, 100, 800, 600)

        self.duration = duration  # Duration in seconds
        self.fs = fs  # Sampling rate
        self.block_size = block_size  # Block size
        self.frequency_range = frequency_range  # Frequency range
        self.color = color  # Color
        self.device = device  # sounddevice input device index, or None for the system default

        self.engine = None
        # The engine's background thread calls _on_engine_spectrum for every
        # qualifying audio block (potentially dozens per second with real
        # mic input) — far faster than a matplotlib redraw can keep up with.
        # Rather than redrawing on every single block (which backs up Qt's
        # event queue under sustained real audio and was the actual cause of
        # freezing/crashing), it just stashes the latest frame; a fixed-rate
        # QTimer on the GUI thread picks it up. Plain attribute assignment
        # is atomic under the GIL, so no lock is needed here.
        self._latest_frame = None

        self.render_timer = QTimer(self)
        self.render_timer.setInterval(RENDER_INTERVAL_MS)
        self.render_timer.timeout.connect(self._render_latest_frame)
        self.render_timer.start()

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

    def _on_engine_spectrum(self, freq_bins, spectrum, max_magnitude):
        # Called from the engine's background thread — must stay cheap and
        # must never touch Qt widgets directly from here.
        self._latest_frame = (freq_bins, spectrum, max_magnitude)

    def _render_latest_frame(self):
        frame = self._latest_frame
        if frame is None:
            return
        try:
            self.update_plot(*frame)
        except Exception as exc:
            # A GUI update slot's exceptions can otherwise crash the whole
            # process (some PyQt5/sip builds treat an unhandled exception
            # escaping a slot as fatal) — never let that happen. Skip this
            # frame and keep the visualizer running instead of aborting.
            print(f'Audio-SpectraCLI: skipped a frame due to an error: {exc}')

    def update_plot(self, freq_bins, spectrum, max_magnitude):
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
        if self.engine is not None:
            self.engine.stop()
            self.engine = None
            self._latest_frame = None
            self.start_button.setText('Start Visualization')
        else:
            self.engine = AudioSpectrumEngine(
                on_spectrum=self._on_engine_spectrum,
                fs=self.fs,
                block_size=self.block_size,
                device=self.device,
            )
            self.engine.start()
            self.start_button.setText('Stop Visualization')

    def closeEvent(self, event):
        if self.engine is not None:
            self.engine.stop()
            self.engine = None
        event.accept()


__all__ = ['AudioSpectrumVisualizer']
