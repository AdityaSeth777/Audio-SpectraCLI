# Aditya Seth
# Description: Pure, independently-testable analysis helpers used by both
# the GUI (main.py) and the engine (engine.py) - windowing, magnitude/dB
# conversion, musical note naming, and a lightweight beat/BPM estimator.
# Kept separate from engine.py so each piece can be unit tested without
# spinning up real audio hardware or Qt.

import time

import numpy as np

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

WINDOW_FUNCTIONS = {
    "none": None,
    "hann": np.hanning,
    "hamming": np.hamming,
    "blackman": np.blackman,
}


def apply_window(samples, window_type="none"):
    """Applies a window function to reduce spectral leakage before an FFT.

    `window_type` is one of WINDOW_FUNCTIONS' keys. "none" (the historical
    default) returns `samples` unchanged.
    """
    window_fn = WINDOW_FUNCTIONS.get(window_type)
    if window_fn is None:
        return samples
    return samples * window_fn(len(samples))


def magnitude_to_db(magnitude, reference=1.0, floor_db=-100.0):
    """Converts a linear FFT magnitude to dB, matching the Web Audio convention."""
    with np.errstate(divide="ignore"):
        db = 20 * np.log10(np.maximum(magnitude, 1e-12) / reference)
    return np.maximum(db, floor_db)


def nearest_musical_note(frequency_hz):
    """Maps a frequency in Hz to the nearest musical note name + octave + cents offset.

    Returns (note_name, octave, cents_offset) e.g. ("A", 4, 0.0) for 440Hz,
    or None if frequency_hz isn't a positive, finite number.
    """
    if frequency_hz is None or frequency_hz <= 0 or not np.isfinite(frequency_hz):
        return None

    # MIDI note number 69 = A4 = 440Hz, 12 semitones per octave.
    midi_number = 12 * np.log2(frequency_hz / 440.0) + 69
    rounded_midi = round(midi_number)
    cents_offset = (midi_number - rounded_midi) * 100

    note_name = NOTE_NAMES[rounded_midi % 12]
    octave = rounded_midi // 12 - 1

    return note_name, octave, cents_offset


def downsample_max_pool(values, num_bins):
    """Reduces `values` to `num_bins` points by taking the max within each group.

    Mirrors web/lib/dsp.ts's downsampleMaxPool - used here for the Bars view
    (a few dozen wide bars read far better than one per FFT bin) and for the
    Waterfall view (keeps each history row a fixed width regardless of the
    current block_size).
    """
    values = np.asarray(values)
    if len(values) <= num_bins:
        return values
    edges = np.linspace(0, len(values), num_bins + 1).astype(int)
    return np.array(
        [values[edges[i]:edges[i + 1]].max() if edges[i + 1] > edges[i] else values[edges[i]] for i in range(num_bins)]
    )


class BeatDetector:
    """Lightweight onset-based BPM estimator.

    Not lab-grade beat tracking - it flags an "onset" whenever overall
    energy jumps well above its own recent rolling average (a simple
    spectral-flux-style heuristic), then estimates BPM from the median
    interval between the last several onsets. Good enough for a clearly
    rhythmic signal (music with a beat); noisy/ambient input will just
    produce an unstable or absent reading, which is inherent to how simple
    this heuristic is, not a bug to chase further here.
    """

    def __init__(self, history_size=43, sensitivity=1.5, max_onset_intervals=8, clock=time.monotonic):
        self.history_size = history_size
        self.sensitivity = sensitivity
        self.max_onset_intervals = max_onset_intervals
        self._clock = clock

        self._energy_history = []
        self._onset_times = []

    def process(self, spectrum):
        """Feeds one frame's spectrum in; returns the current BPM estimate (or None)."""
        energy = float(np.sum(spectrum))
        now = self._clock()

        if self._energy_history:
            recent_average = sum(self._energy_history) / len(self._energy_history)
            if recent_average > 0 and energy > recent_average * self.sensitivity:
                if not self._onset_times or (now - self._onset_times[-1]) > 0.2:  # 300 BPM refractory cap
                    self._onset_times.append(now)
                    self._onset_times = self._onset_times[-(self.max_onset_intervals + 1):]

        self._energy_history.append(energy)
        self._energy_history = self._energy_history[-self.history_size:]

        return self._estimate_bpm()

    def _estimate_bpm(self):
        if len(self._onset_times) < 3:
            return None
        intervals = [b - a for a, b in zip(self._onset_times, self._onset_times[1:])]
        median_interval = sorted(intervals)[len(intervals) // 2]
        if median_interval <= 0:
            return None
        return 60.0 / median_interval

    def reset(self):
        self._energy_history = []
        self._onset_times = []


__all__ = [
    "apply_window",
    "magnitude_to_db",
    "nearest_musical_note",
    "downsample_max_pool",
    "BeatDetector",
    "WINDOW_FUNCTIONS",
]
