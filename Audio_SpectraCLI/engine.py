# Aditya Seth
# Description: Qt-independent audio capture + FFT engine, extracted from the
# PyQt5 GUI so it can be reused by the GUI (main.py) and by headless/streaming
# consumers (headless.py, used by the VS Code extension) without duplicating
# the capture/FFT/smoothing logic in two places.

import queue
import threading

import numpy as np
import sounddevice as sd
from scipy.ndimage import gaussian_filter1d


class AudioSpectrumEngine:
    """Captures microphone input and emits smoothed FFT spectra via a callback.

    `on_spectrum(freq_bins, spectrum, max_magnitude)` is invoked from a
    background thread for every audio block whose peak magnitude clears
    `noise_threshold`. Callers that touch UI state from `on_spectrum` are
    responsible for their own thread-safety (e.g. Qt signals).
    """

    def __init__(
        self,
        on_spectrum,
        fs=44100,
        block_size=4096,
        noise_threshold=0.05,
        smoothing_sigma=2,
    ):
        self.on_spectrum = on_spectrum
        self.fs = fs
        self.block_size = block_size
        self.noise_threshold = noise_threshold
        self.smoothing_sigma = smoothing_sigma

        self.audio_queue = queue.Queue()
        self.running = False
        self.stream = None
        self._worker_thread = None

    def _audio_callback(self, indata, frames, time, status):
        self.audio_queue.put(indata.copy())

    def _process_audio(self):
        while self.running:
            try:
                audio_block = self.audio_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            spectrum = np.abs(np.fft.rfft(audio_block[:, 0], n=self.block_size))
            spectrum = gaussian_filter1d(spectrum, sigma=self.smoothing_sigma)
            max_magnitude = np.max(spectrum)

            if max_magnitude > self.noise_threshold:
                freq_bins = np.fft.rfftfreq(self.block_size, 1 / self.fs)
                self.on_spectrum(freq_bins, spectrum, max_magnitude)

    def start(self):
        if self.running:
            return
        self.running = True
        sd.default.samplerate = self.fs
        sd.default.channels = 1
        self.stream = sd.InputStream(callback=self._audio_callback)
        self.stream.start()
        self._worker_thread = threading.Thread(target=self._process_audio, daemon=True)
        self._worker_thread.start()

    def stop(self):
        self.running = False
        if self.stream is not None:
            self.stream.stop()
            self.stream.close()
            self.stream = None


__all__ = ["AudioSpectrumEngine"]
