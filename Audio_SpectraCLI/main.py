# Aditya Seth
# Description: This file contains the main code for the Audio-SpectraCLI project.
# It is responsible for creating the AudioSpectrumVisualizer class which is used
# to visualize the audio spectrum in real-time.

import csv
import json
import time
from collections import deque

import numpy as np
import sounddevice as sd
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QKeySequence
from PyQt5.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QShortcut,
    QSizePolicy,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from . import presets as preset_store
from .analysis import (
    BeatDetector,
    compute_rms,
    downsample_max_pool,
    is_clipping,
    magnitude_to_db,
    nearest_musical_note,
    render_sparkline,
)
from .engine import AudioSpectrumEngine
from .midi_out import MidiNoteSender, MidiUnavailableError, frequency_to_midi_note

RENDER_INTERVAL_MS = 33  # ~30fps redraw cap, independent of the audio block rate
GAUSSIAN_SMOOTHING_SIGMA = 2  # matches AudioSpectrumEngine's own default; 0 effectively disables smoothing
PEAK_HOLD_DECAY = 0.92  # per-frame multiplicative decay of the held peak
MIDI_SILENCE_TIMEOUT_S = 0.5  # send a MIDI note-off if no new spectrum frame arrives for this long
PEAK_FREQ_HISTORY_LEN = 50  # sparkline width; ~a few seconds of history at typical block rates
CLIP_THRESHOLD = 0.98  # matches analysis.is_clipping's own default; named here for the status label text
SILENCE_RMS_THRESHOLD = 0.01  # below this RMS, a block counts toward the silence streak
SILENCE_STREAK_FOR_WARNING = 15  # consecutive quiet blocks before the "Silence" warning is shown
WATERFALL_HISTORY_ROWS = 60
WATERFALL_WIDTH = 200  # fixed column count per row, independent of block_size
BARS_COUNT = 64

FREQUENCY_RANGE_PRESETS = {
    "0 - 2,500 Hz": (0, 2500),
    "0 - 5,000 Hz": (0, 5000),
    "0 - 7,500 Hz": (0, 7500),
    "0 - 10,000 Hz": (0, 10000),
    "0 - 20,000 Hz (default)": (0, 20000),
}

WINDOW_TYPE_LABELS = {
    "None": "none",
    "Hann": "hann",
    "Hamming": "hamming",
    "Blackman": "blackman",
}

CHANNEL_MODE_LABELS = {
    "Mono (mix)": "mono_mix",
    "Left": "left",
    "Right": "right",
}

VIEW_MODES = ["Line", "Bars", "Waterfall", "Circular", "Tuner"]


class AudioSpectrumVisualizer(QMainWindow):
    def __init__(self, duration=10, fs=44100, block_size=4096, frequency_range=(20, 20000), color='blue', device=None):
        super().__init__()
        self.setWindowTitle('Audio Spectrum Visualizer')
        self.setGeometry(100, 100, 900, 750)

        self.duration = duration  # Duration in seconds
        self.fs = fs  # Sampling rate
        self.block_size = block_size  # Block size
        self.frequency_range = frequency_range  # Frequency range
        self.color = color  # Color
        self.device = device  # sounddevice input device index, or None for the system default
        self.smoothing_sigma = GAUSSIAN_SMOOTHING_SIGMA  # 0 when the Gaussian-smoothing checkbox is unchecked

        # Feature additions: DSP options
        self.window_type = "none"
        self.noise_threshold = 0.05
        self.channel_mode = "mono_mix"
        self.db_scale = False

        # Feature additions: view/overlay state
        self.view_mode = "line"
        self.peak_hold_enabled = False
        self.peak_hold_values = None
        self.waterfall_history = []

        # Feature additions: analysis/output state
        self.beat_detector = None
        self.bpm_estimate = None
        self.midi_enabled = False
        self.midi_sender = None
        self._last_spectrum_frame_time = None

        # RMS/clipping/silence come from on_audio_block (every captured
        # block, unfiltered by noise_threshold); peak-frequency history
        # comes from _update_status_labels, which already computes the
        # dominant frequency for the note label. Plain attribute
        # assignment/deque.append from the engine's background thread is
        # safe here for the same reason _latest_frame's is (see above).
        self._latest_rms = 0.0
        self._latest_clipping = False
        self._silence_block_streak = 0
        self._peak_freq_history = deque(maxlen=PEAK_FREQ_HISTORY_LEN)

        self.engine = None
        # The engine's background thread calls _on_engine_spectrum for every
        # qualifying audio block (potentially dozens per second with real
        # mic input) - far faster than a matplotlib redraw can keep up with.
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

        QShortcut(QKeySequence('Ctrl+S'), self, activated=self.export_png)

    def setup_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        outer_layout = QVBoxLayout()

        # constrained_layout keeps axis labels/titles from being clipped as
        # the canvas is resized (e.g. maximizing the window), instead of
        # only laying out correctly at the initial figsize.
        self.canvas = FigureCanvas(Figure(figsize=(5, 3), constrained_layout=True))
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.ax = self.canvas.figure.add_subplot(111)
        outer_layout.addWidget(self.canvas, stretch=1)

        status_row = QHBoxLayout()
        self.bpm_label = QLabel('BPM: --')
        self.note_label = QLabel('Note: --')
        status_row.addWidget(self.bpm_label)
        status_row.addWidget(self.note_label)
        status_row.addStretch(1)
        outer_layout.addLayout(status_row)

        stats_row = QHBoxLayout()
        self.rms_label = QLabel('RMS: --')
        self.clip_silence_label = QLabel('')
        self.peak_freq_sparkline_label = QLabel('Peak Hz:')
        self.peak_freq_sparkline_label.setStyleSheet('font-family: monospace;')
        stats_row.addWidget(self.rms_label)
        stats_row.addWidget(self.clip_silence_label)
        stats_row.addWidget(self.peak_freq_sparkline_label)
        stats_row.addStretch(1)
        outer_layout.addLayout(stats_row)

        # Controls live in a scroll area - there are now enough of them that
        # a fixed-height panel would either shrink the canvas badly or run
        # off the bottom of the screen on smaller displays.
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        controls_widget = QWidget()
        self.layout = QVBoxLayout()
        controls_widget.setLayout(self.layout)
        scroll.setWidget(controls_widget)
        outer_layout.addWidget(scroll)

        self.duration_slider, self.duration_spinbox = self._add_slider_row(
            'Duration (seconds):', minimum=1, maximum=10, value=self.duration, on_change=self.set_duration,
        )
        self.fs_slider, self.fs_spinbox = self._add_slider_row(
            'Sampling Rate (Hz):', minimum=22050, maximum=44100, value=self.fs, on_change=self.set_sampling_rate,
        )
        self.block_size_slider, self.block_size_spinbox = self._add_slider_row(
            'Block Size:', minimum=256, maximum=8192, value=self.block_size, on_change=self.set_block_size,
        )

        self._add_frequency_range_row()
        self._add_color_row()
        self._add_smoothing_row()
        self._add_noise_threshold_row()
        self._add_window_type_row()
        self._add_channel_mode_row()
        self._add_db_scale_checkbox()
        self._add_view_mode_row()
        self._add_peak_hold_checkbox()
        self._add_device_row()
        self._add_export_row()
        self._add_preset_row()
        self._add_named_preset_row()
        self._add_midi_checkbox()

        self.start_button = QPushButton('Start Visualization')
        self.start_button.clicked.connect(self.toggle_visualization)
        outer_layout.addWidget(self.start_button)

        self.central_widget.setLayout(outer_layout)

    def _add_slider_row(self, label_text, minimum, maximum, value, on_change):
        """Adds a labeled slider + spinbox pair, kept in sync with each other.

        The spinbox shows the exact current value (not just a dot's position
        on the slider) and can be typed into directly, rather than only
        being draggable.
        """
        self.layout.addWidget(QLabel(label_text))

        row = QHBoxLayout()

        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(minimum)
        slider.setMaximum(maximum)
        slider.setValue(value)
        slider.setTickPosition(QSlider.TicksBelow)

        spinbox = QSpinBox()
        spinbox.setMinimum(minimum)
        spinbox.setMaximum(maximum)
        spinbox.setValue(value)

        slider.valueChanged.connect(spinbox.setValue)
        spinbox.valueChanged.connect(slider.setValue)
        slider.valueChanged.connect(on_change)

        row.addWidget(slider, stretch=1)
        row.addWidget(spinbox)
        self.layout.addLayout(row)

        return slider, spinbox

    def _add_frequency_range_row(self):
        self.layout.addWidget(QLabel('Frequency Range (Hz):'))

        row = QHBoxLayout()

        self.freq_min_spinbox = QSpinBox()
        self.freq_min_spinbox.setRange(0, 20000)
        self.freq_min_spinbox.setValue(self.frequency_range[0])
        self.freq_min_spinbox.valueChanged.connect(self.set_frequency_min)

        self.freq_max_spinbox = QSpinBox()
        self.freq_max_spinbox.setRange(0, 20000)
        self.freq_max_spinbox.setValue(self.frequency_range[1])
        self.freq_max_spinbox.valueChanged.connect(self.set_frequency_max)

        self.freq_preset_combo = QComboBox()
        self.freq_preset_combo.addItems(FREQUENCY_RANGE_PRESETS.keys())
        self.freq_preset_combo.currentTextChanged.connect(self.apply_frequency_preset)

        row.addWidget(self.freq_min_spinbox)
        row.addWidget(QLabel('to'))
        row.addWidget(self.freq_max_spinbox)
        row.addWidget(self.freq_preset_combo, stretch=1)
        self.layout.addLayout(row)

    def _add_color_row(self):
        row = QHBoxLayout()
        row.addWidget(QLabel('Plot Color:'))

        self.color_button = QPushButton()
        self.color_button.setFixedWidth(60)
        self._update_color_button_swatch()
        self.color_button.clicked.connect(self.choose_color)

        row.addWidget(self.color_button)
        row.addStretch(1)
        self.layout.addLayout(row)

    def _update_color_button_swatch(self):
        self.color_button.setStyleSheet(f'background-color: {self.color};')

    def _add_smoothing_row(self):
        row = QHBoxLayout()

        self.smoothing_checkbox = QCheckBox('Smooth spectrum (Gaussian filter)')
        self.smoothing_checkbox.setChecked(True)
        self.smoothing_checkbox.toggled.connect(self.set_smoothing_enabled)

        self.smoothing_strength_spinbox = QSpinBox()
        self.smoothing_strength_spinbox.setRange(1, 10)
        self.smoothing_strength_spinbox.setValue(GAUSSIAN_SMOOTHING_SIGMA)
        self.smoothing_strength_spinbox.valueChanged.connect(self.set_smoothing_strength)

        row.addWidget(self.smoothing_checkbox)
        row.addWidget(QLabel('Strength:'))
        row.addWidget(self.smoothing_strength_spinbox)
        row.addStretch(1)
        self.layout.addLayout(row)

    def _add_noise_threshold_row(self):
        self.layout.addWidget(QLabel('Noise Threshold:'))
        row = QHBoxLayout()

        self.noise_threshold_slider = QSlider(Qt.Horizontal)
        self.noise_threshold_slider.setRange(0, 100)  # represents 0.00-1.00
        self.noise_threshold_slider.setValue(int(self.noise_threshold * 100))

        self.noise_threshold_spinbox = QDoubleSpinBox()
        self.noise_threshold_spinbox.setRange(0.0, 1.0)
        self.noise_threshold_spinbox.setSingleStep(0.01)
        self.noise_threshold_spinbox.setValue(self.noise_threshold)

        self.noise_threshold_slider.valueChanged.connect(lambda v: self.noise_threshold_spinbox.setValue(v / 100))
        self.noise_threshold_spinbox.valueChanged.connect(
            lambda v: self.noise_threshold_slider.setValue(int(round(v * 100)))
        )
        self.noise_threshold_spinbox.valueChanged.connect(self.set_noise_threshold)

        row.addWidget(self.noise_threshold_slider, stretch=1)
        row.addWidget(self.noise_threshold_spinbox)
        self.layout.addLayout(row)

    def _add_window_type_row(self):
        row = QHBoxLayout()
        row.addWidget(QLabel('Window Function:'))
        self.window_type_combo = QComboBox()
        self.window_type_combo.addItems(WINDOW_TYPE_LABELS.keys())
        self.window_type_combo.currentTextChanged.connect(self.set_window_type)
        row.addWidget(self.window_type_combo, stretch=1)
        self.layout.addLayout(row)

    def _add_channel_mode_row(self):
        row = QHBoxLayout()
        row.addWidget(QLabel('Channel:'))
        self.channel_mode_combo = QComboBox()
        self.channel_mode_combo.addItems(CHANNEL_MODE_LABELS.keys())
        self.channel_mode_combo.currentTextChanged.connect(self.set_channel_mode)
        row.addWidget(self.channel_mode_combo, stretch=1)
        self.layout.addLayout(row)

    def _add_db_scale_checkbox(self):
        self.db_scale_checkbox = QCheckBox('Use dB (logarithmic) scale')
        self.db_scale_checkbox.toggled.connect(self.set_db_scale)
        self.layout.addWidget(self.db_scale_checkbox)

    def _add_view_mode_row(self):
        row = QHBoxLayout()
        row.addWidget(QLabel('View Mode:'))
        self.view_mode_combo = QComboBox()
        self.view_mode_combo.addItems(VIEW_MODES)
        self.view_mode_combo.currentTextChanged.connect(self.set_view_mode)
        row.addWidget(self.view_mode_combo, stretch=1)
        self.layout.addLayout(row)

    def _add_peak_hold_checkbox(self):
        self.peak_hold_checkbox = QCheckBox('Show peak-hold markers (Line/Bars views)')
        self.peak_hold_checkbox.toggled.connect(self.set_peak_hold_enabled)
        self.layout.addWidget(self.peak_hold_checkbox)

    def _add_device_row(self):
        row = QHBoxLayout()
        row.addWidget(QLabel('Input Device:'))

        self.device_combo = QComboBox()
        self._device_indices = []
        try:
            devices = sd.query_devices()
        except Exception:
            devices = []
        for i, d in enumerate(devices):
            if d.get('max_input_channels', 0) > 0:
                self._device_indices.append(i)
                marker = ' (default)' if self.device is None and i == sd.default.device[0] else ''
                self.device_combo.addItem(f"[{i}] {d['name']}{marker}")

        if self.device is not None and self.device in self._device_indices:
            self.device_combo.setCurrentIndex(self._device_indices.index(self.device))

        self.device_combo.currentIndexChanged.connect(self.set_device_by_combo_index)
        row.addWidget(self.device_combo, stretch=1)
        self.layout.addLayout(row)

    def _add_export_row(self):
        row = QHBoxLayout()

        export_png_button = QPushButton('Export PNG (Ctrl+S)')
        export_png_button.clicked.connect(self.export_png)

        export_csv_button = QPushButton('Export CSV')
        export_csv_button.clicked.connect(self.export_csv)

        self.record_button = QPushButton('Start Recording (WAV)')
        self.record_button.clicked.connect(self.toggle_recording)

        row.addWidget(export_png_button)
        row.addWidget(export_csv_button)
        row.addWidget(self.record_button)
        self.layout.addLayout(row)

    def _add_preset_row(self):
        row = QHBoxLayout()

        save_button = QPushButton('Save Preset')
        save_button.clicked.connect(self.save_preset)

        load_button = QPushButton('Load Preset')
        load_button.clicked.connect(self.load_preset)

        row.addWidget(save_button)
        row.addWidget(load_button)
        self.layout.addLayout(row)

    def _add_named_preset_row(self):
        """A named-preset manager (list/save-as/load/rename/delete against
        the fixed presets directory), distinct from the file-picker based
        save/load above which round-trips through an arbitrary path.
        """
        row = QHBoxLayout()

        self.named_preset_combo = QComboBox()
        self._refresh_named_preset_combo()

        save_as_button = QPushButton('Save As...')
        save_as_button.clicked.connect(self.save_named_preset)

        load_named_button = QPushButton('Load')
        load_named_button.clicked.connect(self.load_named_preset)

        rename_button = QPushButton('Rename')
        rename_button.clicked.connect(self.rename_named_preset)

        delete_button = QPushButton('Delete')
        delete_button.clicked.connect(self.delete_named_preset)

        row.addWidget(QLabel('Presets:'))
        row.addWidget(self.named_preset_combo, stretch=1)
        row.addWidget(save_as_button)
        row.addWidget(load_named_button)
        row.addWidget(rename_button)
        row.addWidget(delete_button)
        self.layout.addLayout(row)

    def _add_midi_checkbox(self):
        self.midi_checkbox = QCheckBox('Send dominant frequency as MIDI (virtual port)')
        self.midi_checkbox.toggled.connect(self.set_midi_enabled)
        self.layout.addWidget(self.midi_checkbox)

    # ---- rendering ----------------------------------------------------

    def _on_engine_spectrum(self, freq_bins, spectrum, max_magnitude):
        # Called from the engine's background thread - must stay cheap and
        # must never touch Qt widgets directly from here.
        self._latest_frame = (freq_bins, spectrum, max_magnitude)
        self._last_spectrum_frame_time = time.monotonic()

    def _on_audio_block(self, samples):
        # Also called from the engine's background thread, for EVERY
        # captured block - unlike _on_engine_spectrum, this isn't gated by
        # noise_threshold, which is what lets it actually detect silence.
        self._latest_rms = compute_rms(samples)
        self._latest_clipping = is_clipping(samples, threshold=CLIP_THRESHOLD)
        if self._latest_rms < SILENCE_RMS_THRESHOLD:
            self._silence_block_streak += 1
        else:
            self._silence_block_streak = 0

    def _render_latest_frame(self):
        self._check_midi_silence_timeout()

        frame = self._latest_frame
        if frame is None:
            return
        try:
            self.update_plot(*frame)
        except Exception as exc:
            # A GUI update slot's exceptions can otherwise crash the whole
            # process (some PyQt5/sip builds treat an unhandled exception
            # escaping a slot as fatal) - never let that happen. Skip this
            # frame and keep the visualizer running instead of aborting.
            print(f'Audio-SpectraCLI: skipped a frame due to an error: {exc}')

    def _visible_mask(self, freq_bins):
        return (freq_bins >= self.frequency_range[0]) & (freq_bins <= self.frequency_range[1])

    def update_plot(self, freq_bins, spectrum, max_magnitude):
        display_spectrum = magnitude_to_db(spectrum) if self.db_scale else spectrum

        mask = self._visible_mask(freq_bins)
        visible_freqs = freq_bins[mask]
        visible_values = display_spectrum[mask]
        if visible_values.size == 0:
            visible_freqs, visible_values = freq_bins, display_spectrum
        visible_max = float(np.max(visible_values)) if visible_values.size else 1.0

        if self.peak_hold_enabled:
            if self.peak_hold_values is None or len(self.peak_hold_values) != len(display_spectrum):
                self.peak_hold_values = display_spectrum.copy()
            else:
                self.peak_hold_values = np.maximum(display_spectrum, self.peak_hold_values * PEAK_HOLD_DECAY)

        self._update_status_labels(freq_bins, spectrum, visible_freqs, visible_values)
        self._maybe_send_midi(visible_freqs, visible_values)

        self.ax.clear()

        if self.view_mode == "waterfall":
            self._render_waterfall(visible_freqs, visible_values)
        elif self.view_mode == "circular":
            self._render_circular(visible_values, visible_max)
        elif self.view_mode == "tuner":
            self._render_tuner(visible_freqs, visible_values)
        else:
            self._render_line_or_bars(freq_bins, display_spectrum, visible_freqs, visible_values)

        y_floor = -100 if self.db_scale else 0
        self.ax.set_title('Audio Spectrum Visualization')
        if self.view_mode in ("line", "bars"):
            self.ax.set_xlim(self.frequency_range)
            # dB values are typically negative (e.g. -10), so "*1.2 for
            # headroom" makes them MORE negative - a ceiling BELOW the
            # actual peak, clipping it off the top of the plot. Linear
            # magnitudes are always >= 0, where *1.2 headroom is correct.
            y_ceiling = visible_max + 5 if self.db_scale else max(visible_max * 1.2, 0.01)
            self.ax.set_ylim(y_floor, max(y_ceiling, y_floor + 0.01))
            self.ax.set_xlabel('Frequency (Hz)')
            self.ax.set_ylabel('Magnitude (dB)' if self.db_scale else 'Magnitude')
        elif self.view_mode == "waterfall":
            # Deliberately does not call set_ylim here: _render_waterfall
            # already set imshow's extent to (0, num_history_rows), and
            # overwriting it with the linear-magnitude range used by
            # line/bars would squash the whole image into a sliver at the
            # bottom - exactly the bug this comment is here to prevent
            # reintroducing.
            self.ax.set_xlim(self.frequency_range)
            self.ax.set_xlabel('Frequency (Hz)')

        self.canvas.draw()

    def _render_line_or_bars(self, freq_bins, display_spectrum, visible_freqs, visible_values):
        if self.view_mode == "bars":
            # Downsample the VISIBLE (masked-to-frequency-range) bins, not
            # the full spectrum - using the full spectrum here made bar
            # spacing correspond to the whole 0..Nyquist range while `width`
            # was sized for the (usually much narrower) selected frequency
            # range, so bars rendered as thin slivers with large gaps
            # whenever the visible range was narrower than the full FFT range.
            bar_freqs = downsample_max_pool(visible_freqs, BARS_COUNT)
            bar_values = downsample_max_pool(visible_values, BARS_COUNT)
            width = (self.frequency_range[1] - self.frequency_range[0]) / BARS_COUNT
            self.ax.bar(bar_freqs, bar_values, width=width, color=self.color)
        else:
            self.ax.plot(freq_bins, display_spectrum, color=self.color)

        if self.peak_hold_enabled and self.peak_hold_values is not None:
            self.ax.plot(freq_bins, self.peak_hold_values, color='red', linestyle='--', linewidth=1)

    def _render_waterfall(self, visible_freqs, visible_values):
        if visible_values.size < 2:
            return  # not enough bins this frame to build a meaningful row

        # Resampled via interpolation to EXACTLY WATERFALL_WIDTH points,
        # regardless of how many bins are visible right now. That count
        # varies with the (live-changeable) frequency range, and
        # downsample_max_pool only shrinks - it returns its input unchanged
        # when already short, which let rows of different lengths land in
        # the same history and make np.array(...)/imshow blow up on a
        # ragged array (and permanently corrupt the history, since the
        # mismatched row had already been appended before the crash).
        x_original = np.linspace(0, 1, visible_values.size)
        x_target = np.linspace(0, 1, WATERFALL_WIDTH)
        row = np.interp(x_target, x_original, visible_values)

        self.waterfall_history.append(row)
        self.waterfall_history = self.waterfall_history[-WATERFALL_HISTORY_ROWS:]

        history_array = np.array(self.waterfall_history)
        self.ax.imshow(
            history_array,
            aspect='auto',
            origin='lower',
            extent=[self.frequency_range[0], self.frequency_range[1], 0, len(self.waterfall_history)],
            cmap='viridis',
        )
        self.ax.set_ylabel('Frames (most recent at top)')

    def _render_circular(self, visible_values, visible_max):
        n = len(visible_values)
        if n == 0:
            return
        theta = np.linspace(0, 2 * np.pi, n, endpoint=False)
        norm = visible_values / visible_max if visible_max > 0 else np.zeros(n)
        radius = 1 + norm
        x = radius * np.cos(theta)
        y = radius * np.sin(theta)
        self.ax.plot(x, y, color=self.color)
        self.ax.set_aspect('equal')
        self.ax.axis('off')

    def _render_tuner(self, visible_freqs, visible_values):
        self.ax.axis('off')
        if visible_values.size == 0:
            self.ax.text(0.5, 0.5, 'No signal', ha='center', va='center', fontsize=24, transform=self.ax.transAxes)
            return

        dominant_freq = float(visible_freqs[int(np.argmax(visible_values))])
        note = nearest_musical_note(dominant_freq)
        if note is None:
            text = f"{dominant_freq:.1f} Hz"
        else:
            note_name, octave, cents = note
            sign = '+' if cents >= 0 else ''
            text = f"{note_name}{octave}\n{dominant_freq:.1f} Hz\n{sign}{cents:.0f} cents"

        self.ax.text(
            0.5, 0.5, text, ha='center', va='center', fontsize=32, color=self.color, transform=self.ax.transAxes,
        )

    def _update_status_labels(self, freq_bins, spectrum, visible_freqs, visible_values):
        if self.beat_detector is not None:
            self.bpm_estimate = self.beat_detector.process(spectrum)
            self.bpm_label.setText(f"BPM: {self.bpm_estimate:.0f}" if self.bpm_estimate else "BPM: --")

        if visible_values.size:
            dominant_freq = float(visible_freqs[int(np.argmax(visible_values))])
            note = nearest_musical_note(dominant_freq)
            if note:
                note_name, octave, _cents = note
                self.note_label.setText(f"Note: {note_name}{octave} ({dominant_freq:.1f} Hz)")
            else:
                self.note_label.setText(f"Note: -- ({dominant_freq:.1f} Hz)")
            self._peak_freq_history.append(dominant_freq)

        self._update_stats_row()

    def _update_stats_row(self):
        self.rms_label.setText(f"RMS: {self._latest_rms:.3f}")

        if self._latest_clipping:
            self.clip_silence_label.setText('⚠ Clipping')
            self.clip_silence_label.setStyleSheet('color: red; font-weight: bold;')
        elif self._silence_block_streak >= SILENCE_STREAK_FOR_WARNING:
            self.clip_silence_label.setText('⚠ Silence')
            self.clip_silence_label.setStyleSheet('color: gray;')
        else:
            self.clip_silence_label.setText('')
            self.clip_silence_label.setStyleSheet('')

        if self._peak_freq_history:
            sparkline = render_sparkline(
                self._peak_freq_history, low=self.frequency_range[0], high=self.frequency_range[1],
            )
            latest = self._peak_freq_history[-1]
            self.peak_freq_sparkline_label.setText(f"Peak Hz: {sparkline} {latest:.0f}")
        else:
            self.peak_freq_sparkline_label.setText('Peak Hz:')

    def _maybe_send_midi(self, visible_freqs, visible_values):
        if not self.midi_enabled or self.midi_sender is None or visible_values.size == 0:
            return
        dominant_freq = float(visible_freqs[int(np.argmax(visible_values))])
        midi_note = frequency_to_midi_note(dominant_freq)
        if midi_note is not None:
            self.midi_sender.send_note_for_frequency(midi_note)

    def _check_midi_silence_timeout(self):
        """Sends a MIDI note-off once input has been quiet for a while.

        send_note_for_frequency only emits a note-off when a DIFFERENT note
        comes in - but engine.py's callback stops firing entirely once the
        signal drops below noise_threshold, so without this, the last note
        sent before things went quiet would sustain forever (a stuck note
        on whatever's listening to the virtual MIDI port) instead of ever
        being released.
        """
        if not self.midi_enabled or self.midi_sender is None:
            return
        if self._last_spectrum_frame_time is None:
            return
        if time.monotonic() - self._last_spectrum_frame_time > MIDI_SILENCE_TIMEOUT_S:
            self.midi_sender.stop()
            self._last_spectrum_frame_time = None  # don't call stop() again every tick until a new frame arrives

    # ---- setters wired to controls -------------------------------------

    def set_duration(self, value):
        self.duration = value

    def set_sampling_rate(self, value):
        # Takes effect the next time Start is clicked - a running
        # sounddevice stream can't have its sample rate changed in place;
        # that requires stopping and reopening it.
        self.fs = value

    def set_block_size(self, value):
        # Same as set_sampling_rate: applies to the next Start, not the
        # currently running stream.
        self.block_size = value

    def set_frequency_min(self, value):
        if value >= self.frequency_range[1]:
            self.freq_min_spinbox.setValue(self.frequency_range[0])  # reject, restore previous
            return
        self.frequency_range = (value, self.frequency_range[1])

    def set_frequency_max(self, value):
        if value <= self.frequency_range[0]:
            self.freq_max_spinbox.setValue(self.frequency_range[1])  # reject, restore previous
            return
        self.frequency_range = (self.frequency_range[0], value)

    def apply_frequency_preset(self, preset_label):
        preset = FREQUENCY_RANGE_PRESETS.get(preset_label)
        if preset is None:
            return
        self.freq_min_spinbox.setValue(preset[0])
        self.freq_max_spinbox.setValue(preset[1])

    def choose_color(self):
        chosen = QColorDialog.getColor(initial=QColor(self.color), parent=self)
        if not chosen.isValid():
            return
        self.color = chosen.name()
        self._update_color_button_swatch()

    def set_smoothing_enabled(self, enabled):
        self.smoothing_sigma = self.smoothing_strength_spinbox.value() if enabled else 0
        self._push_live_engine_attr('smoothing_sigma', self.smoothing_sigma)

    def set_smoothing_strength(self, value):
        if self.smoothing_checkbox.isChecked():
            self.smoothing_sigma = value
            self._push_live_engine_attr('smoothing_sigma', self.smoothing_sigma)

    def set_noise_threshold(self, value):
        self.noise_threshold = value
        self._push_live_engine_attr('noise_threshold', value)

    def set_window_type(self, label):
        self.window_type = WINDOW_TYPE_LABELS.get(label, "none")
        self._push_live_engine_attr('window_type', self.window_type)

    def set_channel_mode(self, label):
        self.channel_mode = CHANNEL_MODE_LABELS.get(label, "mono_mix")
        self._push_live_engine_attr('channel_mode', self.channel_mode)

    def set_db_scale(self, enabled):
        self.db_scale = enabled
        self.peak_hold_values = None  # stale values were on the other scale
        self.waterfall_history = []  # stale rows would mix dB and linear values in one imshow

    def set_view_mode(self, label):
        self.view_mode = label.lower()
        self.waterfall_history = []
        self.peak_hold_values = None

    def set_peak_hold_enabled(self, enabled):
        self.peak_hold_enabled = enabled
        self.peak_hold_values = None

    def set_device_by_combo_index(self, combo_index):
        if self.engine is not None:
            # Changing the device on a running stream isn't supported -
            # same constraint as sampling rate/block size. Restore the
            # combo to the device actually in use instead of silently
            # ignoring the click.
            if self.device in self._device_indices:
                self.device_combo.setCurrentIndex(self._device_indices.index(self.device))
            return
        if 0 <= combo_index < len(self._device_indices):
            self.device = self._device_indices[combo_index]

    def set_midi_enabled(self, enabled):
        if enabled:
            try:
                self.midi_sender = MidiNoteSender()
                self.midi_enabled = True
            except MidiUnavailableError as exc:
                self.midi_checkbox.setChecked(False)
                QMessageBox.warning(self, 'MIDI unavailable', str(exc))
            except Exception as exc:
                # Defense in depth: midi_out.py already converts its own
                # failures to MidiUnavailableError, but a checkbox-toggle
                # slot is exactly the kind of place an unhandled exception
                # can abort the whole process on some PyQt5/sip builds - an
                # unexpected error here must still fail safely, not crash.
                self.midi_checkbox.setChecked(False)
                QMessageBox.warning(self, 'MIDI unavailable', f'Unexpected error enabling MIDI: {exc}')
        else:
            self.midi_enabled = False
            if self.midi_sender is not None:
                self.midi_sender.close()
                self.midi_sender = None

    def _push_live_engine_attr(self, attr_name, value):
        """Applies a setting to the currently running engine, if any.

        engine.py reads these attributes fresh on every processed block, so
        this takes effect on the very next block - no restart needed, unlike
        fs/block_size/channels/device which require reopening the stream.
        """
        if self.engine is not None:
            setattr(self.engine, attr_name, value)

    # ---- export / presets / recording ----------------------------------

    def export_png(self):
        path, _ = QFileDialog.getSaveFileName(self, 'Export current view as PNG', 'spectrum.png', 'PNG Files (*.png)')
        if not path:
            return
        try:
            self.canvas.figure.savefig(path)
        except Exception as exc:
            # File I/O (permission denied, disk full, bad path, ...) run
            # directly inside a button-click Qt slot must not be allowed to
            # raise uncaught - same crash class as the render-path fixes.
            QMessageBox.warning(self, 'Export failed', f'Could not save PNG: {exc}')

    def export_csv(self):
        if self._latest_frame is None:
            QMessageBox.information(self, 'No data yet', 'Start visualizing before exporting data.')
            return
        path, _ = QFileDialog.getSaveFileName(self, 'Export current frame as CSV', 'spectrum.csv', 'CSV Files (*.csv)')
        if not path:
            return
        freq_bins, spectrum, _max_magnitude = self._latest_frame
        try:
            with open(path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['frequency_hz', 'magnitude'])
                writer.writerows(zip(freq_bins.tolist(), spectrum.tolist()))
        except Exception as exc:
            QMessageBox.warning(self, 'Export failed', f'Could not save CSV: {exc}')

    def toggle_recording(self):
        if self.engine is None:
            QMessageBox.information(self, 'Not running', 'Start visualization before recording.')
            return

        if self.engine.recording:
            self._finish_recording()
        else:
            self.engine.start_recording()
            self.record_button.setText('Stop Recording (WAV)')

    def _finish_recording(self):
        """Stops recording (if active) and offers to save it. Safe to call
        whether or not a recording is actually in progress, and used both by
        the Record button and by toggle_visualization's stop path - clicking
        "Stop Visualization" while recording used to silently discard the
        buffered audio and leave the Record button reading "Stop Recording"
        with no engine behind it."""
        if self.engine is None or not self.engine.recording:
            return

        samples = self.engine.stop_recording()
        self.record_button.setText('Start Recording (WAV)')
        if samples.size == 0:
            QMessageBox.information(self, 'Nothing recorded', 'No audio was captured.')
            return
        path, _ = QFileDialog.getSaveFileName(self, 'Save recording', 'recording.wav', 'WAV Files (*.wav)')
        if path:
            try:
                self._write_wav(path, samples, self.fs)
            except Exception as exc:
                QMessageBox.warning(self, 'Save failed', f'Could not save recording: {exc}')

    @staticmethod
    def _write_wav(path, samples, sample_rate):
        from scipy.io import wavfile

        clipped = np.clip(samples, -1.0, 1.0)
        int16_samples = (clipped * 32767).astype(np.int16)
        wavfile.write(path, sample_rate, int16_samples)

    def _current_settings_dict(self):
        return {
            'duration': self.duration,
            'fs': self.fs,
            'block_size': self.block_size,
            'frequency_range': list(self.frequency_range),
            'color': self.color,
            'window_type': self.window_type,
            'noise_threshold': self.noise_threshold,
            'channel_mode': self.channel_mode,
            'db_scale': self.db_scale,
            'view_mode': self.view_mode,
            'peak_hold_enabled': self.peak_hold_enabled,
            'smoothing_enabled': self.smoothing_checkbox.isChecked(),
            'smoothing_sigma': self.smoothing_strength_spinbox.value(),
        }

    def save_preset(self):
        path, _ = QFileDialog.getSaveFileName(self, 'Save preset', 'preset.json', 'JSON Files (*.json)')
        if not path:
            return
        try:
            with open(path, 'w') as f:
                json.dump(self._current_settings_dict(), f, indent=2)
        except Exception as exc:
            QMessageBox.warning(self, 'Save failed', f'Could not save preset: {exc}')

    def load_preset(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Load preset', '', 'JSON Files (*.json)')
        if not path:
            return
        try:
            with open(path) as f:
                settings = json.load(f)
            self.apply_settings_dict(settings)
        except Exception as exc:
            # A malformed/non-JSON file, or one with an unexpected shape
            # (e.g. frequency_range not a 2-element list), previously raised
            # straight out of this button-click slot uncaught.
            QMessageBox.warning(self, 'Load failed', f'Could not load preset: {exc}')

    def _refresh_named_preset_combo(self, select=None):
        self.named_preset_combo.blockSignals(True)
        self.named_preset_combo.clear()
        try:
            names = preset_store.list_presets()
        except OSError as exc:
            QMessageBox.warning(self, 'Presets unavailable', f'Could not read the presets directory: {exc}')
            names = []
        self.named_preset_combo.addItems(names)
        if select is not None:
            index = self.named_preset_combo.findText(select)
            if index >= 0:
                self.named_preset_combo.setCurrentIndex(index)
        self.named_preset_combo.blockSignals(False)

    def save_named_preset(self):
        name, ok = QInputDialog.getText(self, 'Save Preset As', 'Preset name:')
        if not ok or not name.strip():
            return
        try:
            preset_store.save_preset(None, name.strip(), self._current_settings_dict())
        except (OSError, ValueError) as exc:
            QMessageBox.warning(self, 'Save failed', f'Could not save preset: {exc}')
            return
        self._refresh_named_preset_combo(select=name.strip())

    def load_named_preset(self):
        name = self.named_preset_combo.currentText()
        if not name:
            return
        try:
            settings = preset_store.load_preset(None, name)
        except (OSError, ValueError) as exc:
            QMessageBox.warning(self, 'Load failed', f'Could not load preset: {exc}')
            return
        self.apply_settings_dict(settings)

    def rename_named_preset(self):
        old_name = self.named_preset_combo.currentText()
        if not old_name:
            return
        new_name, ok = QInputDialog.getText(self, 'Rename Preset', 'New name:', text=old_name)
        if not ok or not new_name.strip() or new_name.strip() == old_name:
            return
        try:
            preset_store.rename_preset(None, old_name, new_name.strip())
        except (OSError, ValueError) as exc:
            QMessageBox.warning(self, 'Rename failed', f'Could not rename preset: {exc}')
            return
        self._refresh_named_preset_combo(select=new_name.strip())

    def delete_named_preset(self):
        name = self.named_preset_combo.currentText()
        if not name:
            return
        confirm = QMessageBox.question(
            self, 'Delete Preset', f"Delete preset '{name}'? This can't be undone.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if confirm != QMessageBox.Yes:
            return
        try:
            preset_store.delete_preset(None, name)
        except OSError as exc:
            QMessageBox.warning(self, 'Delete failed', f'Could not delete preset: {exc}')
            return
        self._refresh_named_preset_combo()

    def apply_settings_dict(self, settings):
        """Applies a settings dict (from load_preset, or a test) to the UI controls.

        Going through the widgets (not just the attributes) keeps sliders/
        spinboxes/checkboxes visually in sync with whatever was loaded.
        """
        if 'duration' in settings:
            self.duration_spinbox.setValue(settings['duration'])
        if 'fs' in settings:
            self.fs_spinbox.setValue(settings['fs'])
        if 'block_size' in settings:
            self.block_size_spinbox.setValue(settings['block_size'])
        if 'frequency_range' in settings:
            fmin, fmax = settings['frequency_range']
            # set_frequency_min/max each validate against the CURRENT
            # self.frequency_range, not the other new value - so setting
            # either spinbox first can get silently rejected if the
            # currently-loaded range doesn't overlap the new one (e.g.
            # current is (15000, 20000), preset wants (0, 2500): setting
            # max=2500 first is rejected since 2500 <= current min 15000).
            # Setting self.frequency_range directly sidesteps that
            # ordering hazard entirely; the spinboxes are then just updated
            # to reflect it, with signals blocked so that update can't
            # itself trigger the same validation again.
            if fmin < fmax:
                self.frequency_range = (fmin, fmax)
                self.freq_min_spinbox.blockSignals(True)
                self.freq_max_spinbox.blockSignals(True)
                self.freq_min_spinbox.setValue(fmin)
                self.freq_max_spinbox.setValue(fmax)
                self.freq_min_spinbox.blockSignals(False)
                self.freq_max_spinbox.blockSignals(False)
        if 'color' in settings:
            self.color = settings['color']
            self._update_color_button_swatch()
        if 'window_type' in settings:
            inverse = {v: k for k, v in WINDOW_TYPE_LABELS.items()}
            self.window_type_combo.setCurrentText(inverse.get(settings['window_type'], 'None'))
        if 'noise_threshold' in settings:
            self.noise_threshold_spinbox.setValue(settings['noise_threshold'])
        if 'channel_mode' in settings:
            inverse = {v: k for k, v in CHANNEL_MODE_LABELS.items()}
            self.channel_mode_combo.setCurrentText(inverse.get(settings['channel_mode'], 'Mono (mix)'))
        if 'db_scale' in settings:
            self.db_scale_checkbox.setChecked(settings['db_scale'])
        if 'view_mode' in settings:
            self.view_mode_combo.setCurrentText(settings['view_mode'].capitalize())
        if 'peak_hold_enabled' in settings:
            self.peak_hold_checkbox.setChecked(settings['peak_hold_enabled'])
        if 'smoothing_sigma' in settings:
            self.smoothing_strength_spinbox.setValue(settings['smoothing_sigma'])
        if 'smoothing_enabled' in settings:
            self.smoothing_checkbox.setChecked(settings['smoothing_enabled'])

    # ---- lifecycle -------------------------------------------------------

    def toggle_visualization(self):
        if self.engine is not None:
            self._finish_recording()  # otherwise stopping mid-recording silently discards it
            self.engine.stop()
            self.engine = None
            self._latest_frame = None
            self.beat_detector = None
            self._last_spectrum_frame_time = None
            self._latest_rms = 0.0
            self._latest_clipping = False
            self._silence_block_streak = 0
            self._peak_freq_history.clear()
            self._update_stats_row()
            if self.midi_sender is not None:
                # Otherwise a note started before Stop was clicked has no
                # more frames coming (the silence-timeout check above only
                # runs while the render timer still has a reason to care) -
                # it would stay stuck on until a different pitch is next
                # detected in some future session.
                self.midi_sender.stop()
            self.device_combo.setEnabled(True)
            self.start_button.setText('Start Visualization')
        else:
            channels = self._resolve_channel_count()
            new_engine = AudioSpectrumEngine(
                on_spectrum=self._on_engine_spectrum,
                on_audio_block=self._on_audio_block,
                fs=self.fs,
                block_size=self.block_size,
                device=self.device,
                smoothing_sigma=self.smoothing_sigma,
                noise_threshold=self.noise_threshold,
                channels=channels,
                channel_mode=self.channel_mode,
                window_type=self.window_type,
            )
            try:
                new_engine.start()
            except Exception as exc:
                # sd.InputStream(...)/.start() raise on ordinary, easily-hit
                # conditions (device unplugged, unsupported fs/channels for
                # that device, device now busy) - completely uncaught here
                # would crash the Start button's click slot outright on this
                # PyQt5/sip build, the same way every other fix in this file
                # exists to prevent.
                QMessageBox.warning(self, 'Could not start', f'Could not start audio capture: {exc}')
                return

            self.engine = new_engine
            self.beat_detector = BeatDetector()
            self.device_combo.setEnabled(False)
            self.start_button.setText('Stop Visualization')

    def _resolve_channel_count(self):
        """Picks how many channels to actually open on the input stream.

        "Mono (mix)" is supposed to average L+R down to mono, but that
        requires opening 2 channels to have anything to average - opening
        only 1 (as this used to do unconditionally) meant `_select_channel`
        always hit its "already mono" fast path first and the averaging
        branch was unreachable. This asks the device what it actually
        supports first, so a genuinely mono-only device still gets
        channels=1 instead of a request InputStream would reject.
        """
        try:
            device_index = self.device if self.device is not None else sd.default.device[0]
            max_input_channels = sd.query_devices(device_index)['max_input_channels']
        except Exception:
            max_input_channels = 1
        return max(1, min(2, max_input_channels))

    def closeEvent(self, event):
        if self.engine is not None:
            self._finish_recording()  # otherwise closing the window mid-recording silently discards it, same as Stop used to
            self.engine.stop()
            self.engine = None
        if self.midi_sender is not None:
            self.midi_sender.close()
            self.midi_sender = None
        event.accept()


__all__ = ['AudioSpectrumVisualizer']


def main():
    """Entry point for `python -m Audio_SpectraCLI.main` (e.g. the Dockerfile's
    default CMD) - previously missing, so that command silently imported and
    exited without ever showing a window."""
    import sys

    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = AudioSpectrumVisualizer()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
