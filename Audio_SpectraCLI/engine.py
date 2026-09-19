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

from .analysis import apply_window


class AudioSpectrumEngine:
    """Captures microphone input and emits smoothed FFT spectra via a callback.

    `on_spectrum(freq_bins, spectrum, max_magnitude)` is invoked from a
    background thread for every audio block whose peak magnitude clears
    `noise_threshold` - potentially dozens of times per second with real
    audio. Callers that touch UI state from `on_spectrum` are responsible
    for their own thread-safety, and should avoid doing slow work (like a
    GUI redraw) directly in the callback - main.py stashes the latest frame
    and redraws from a fixed-rate timer instead, rather than redrawing on
    every single call.
    """

    def __init__(
        self,
        on_spectrum,
        fs=44100,
        block_size=4096,
        noise_threshold=0.05,
        smoothing_sigma=2,
        device=None,
        channels=1,
        channel_mode="mono_mix",
        window_type="none",
    ):
        self.on_spectrum = on_spectrum
        self.fs = fs
        self.block_size = block_size
        self.noise_threshold = noise_threshold
        self.smoothing_sigma = smoothing_sigma
        self.device = device  # sounddevice input device index, or None for the system default
        self.channels = channels  # number of input channels to actually open on the stream
        self.channel_mode = channel_mode  # "mono_mix" | "left" | "right" - which channel(s) to analyze
        self.window_type = window_type  # one of analysis.WINDOW_FUNCTIONS' keys

        self.audio_queue = queue.Queue()
        self.running = False
        self.stream = None
        self._worker_thread = None

        self.recording = False
        self._recorded_chunks = []

    def start_recording(self):
        """Starts accumulating raw (post channel-select, pre-window) samples for WAV export."""
        self._recorded_chunks = []
        self.recording = True

    def stop_recording(self):
        """Stops recording and returns the accumulated samples as one Float32 array."""
        self.recording = False
        if not self._recorded_chunks:
            return np.array([], dtype=np.float32)
        return np.concatenate(self._recorded_chunks).astype(np.float32)

    def _audio_callback(self, indata, frames, time, status):
        self.audio_queue.put(indata.copy())

    def _select_channel(self, audio_block):
        if audio_block.shape[1] == 1:
            return audio_block[:, 0]
        if self.channel_mode == "left":
            return audio_block[:, 0]
        if self.channel_mode == "right":
            return audio_block[:, min(1, audio_block.shape[1] - 1)]
        return audio_block.mean(axis=1)  # "mono_mix"

    def _process_audio(self):
        while self.running:
            try:
                audio_block = self.audio_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            try:
                samples = self._select_channel(audio_block)

                if self.recording:
                    self._recorded_chunks.append(samples.copy())

                windowed_samples = apply_window(samples, self.window_type)

                spectrum = np.abs(np.fft.rfft(windowed_samples, n=self.block_size))
                # scipy's gaussian_filter1d raises ZeroDivisionError for
                # sigma=0 rather than treating it as "no smoothing" - found
                # by an actual end-to-end run (unmocked, real thread) after
                # unchecking the smoothing checkbox live. sigma<=0 is
                # unambiguously "disabled" here, so skip the call entirely
                # instead of passing 0 through to scipy.
                if self.smoothing_sigma > 0:
                    spectrum = gaussian_filter1d(spectrum, sigma=self.smoothing_sigma)
                max_magnitude = np.max(spectrum)

                if max_magnitude > self.noise_threshold:
                    freq_bins = np.fft.rfftfreq(self.block_size, 1 / self.fs)
                    self.on_spectrum(freq_bins, spectrum, max_magnitude)
            except Exception as exc:
                # Nothing in this block may be allowed to kill the thread
                # silently - Python's default handling for an unhandled
                # exception in a background thread is to print a traceback
                # and let the thread die, with the rest of the app (main
                # thread, GUI) carrying on oblivious that audio processing
                # has permanently stopped. That looks exactly like a
                # freeze, with no visible error, which is what actually
                # happened here before this fix.
                print(f"Audio-SpectraCLI: error while processing an audio block: {exc}")

    def start(self):
        if self.running:
            return
        self.running = True
        sd.default.samplerate = self.fs
        sd.default.channels = self.channels
        # blocksize is deliberately tied to block_size: leaving it at
        # PortAudio's default (None) lets it choose its own, often much
        # smaller, callback chunk size, causing on_spectrum to fire far more
        # often than "once per block_size samples" - under sustained real
        # audio this is what actually overwhelms a per-callback GUI redraw.
        self.stream = sd.InputStream(device=self.device, blocksize=self.block_size, callback=self._audio_callback)
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
