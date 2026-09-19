"""Unit tests for AudioSpectrumEngine's pure processing logic.

These do not touch real audio hardware: `_audio_callback`/`_process_audio`
are exercised directly with synthetic blocks, since sounddevice.InputStream
is never constructed unless `.start()` is called.
"""

import threading
import time
from unittest.mock import MagicMock, patch

import numpy as np

from Audio_SpectraCLI.engine import AudioSpectrumEngine


def make_engine(**overrides):
    captured = []
    defaults = dict(fs=44100, block_size=1024, noise_threshold=0.05, smoothing_sigma=2)
    defaults.update(overrides)
    engine = AudioSpectrumEngine(on_spectrum=lambda *args: captured.append(args), **defaults)
    return engine, captured


def test_quiet_block_below_noise_threshold_is_dropped():
    engine, captured = make_engine(noise_threshold=1.0)
    quiet_block = np.zeros((engine.block_size, 1), dtype=np.float32)
    engine.audio_queue.put(quiet_block)
    engine.running = True

    # Run one iteration of the processing loop body directly.
    audio_block = engine.audio_queue.get(timeout=0.1)
    spectrum = np.abs(np.fft.rfft(audio_block[:, 0], n=engine.block_size))
    assert np.max(spectrum) <= engine.noise_threshold


def test_loud_block_triggers_callback_with_expected_shapes():
    engine, captured = make_engine(noise_threshold=0.01)
    t = np.linspace(0, 1, engine.block_size, endpoint=False)
    loud_block = (np.sin(2 * np.pi * 440 * t).astype(np.float32)).reshape(-1, 1)

    engine.running = True
    engine.audio_queue.put(loud_block)

    # Drain exactly one item the way `_process_audio` would.
    audio_block = engine.audio_queue.get(timeout=0.1)
    spectrum = np.abs(np.fft.rfft(audio_block[:, 0], n=engine.block_size))
    max_magnitude = np.max(spectrum)
    assert max_magnitude > engine.noise_threshold

    freq_bins = np.fft.rfftfreq(engine.block_size, 1 / engine.fs)
    engine.on_spectrum(freq_bins, spectrum, max_magnitude)

    assert len(captured) == 1
    got_freq_bins, got_spectrum, got_max = captured[0]
    assert got_freq_bins.shape == got_spectrum.shape
    assert got_max == max_magnitude


def test_raising_callback_does_not_kill_the_processing_thread():
    """A callback that raises must not silently kill the background thread.

    Regression test for the reported crash: the whole point of engine.py
    catching exceptions around on_spectrum is that a bug in the caller (a
    GUI redraw, a headless JSON serializer, anything) shouldn't take down
    audio processing entirely with no further updates and no visible error.
    """
    call_count = {"n": 0}

    def flaky_on_spectrum(*_args):
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise RuntimeError("boom")

    engine = AudioSpectrumEngine(on_spectrum=flaky_on_spectrum, block_size=1024, noise_threshold=0.01)
    engine.running = True

    t = np.linspace(0, 1, engine.block_size, endpoint=False)
    loud_block = (np.sin(2 * np.pi * 440 * t).astype(np.float32)).reshape(-1, 1)
    engine.audio_queue.put(loud_block.copy())
    engine.audio_queue.put(loud_block.copy())

    worker = threading.Thread(target=engine._process_audio, daemon=True)
    worker.start()

    deadline = time.time() + 2
    while call_count["n"] < 2 and time.time() < deadline:
        time.sleep(0.01)

    engine.running = False
    worker.join(timeout=1)

    assert call_count["n"] == 2, "thread died after the first callback raised instead of processing the second block"


def test_stop_is_safe_when_never_started():
    engine, _ = make_engine()
    engine.stop()  # must not raise even though .start() was never called
    assert engine.running is False
    assert engine.stream is None


def test_start_passes_selected_device_to_input_stream():
    engine, _ = make_engine(device=5)
    fake_stream = MagicMock()
    with patch("Audio_SpectraCLI.engine.sd.InputStream", return_value=fake_stream) as mock_stream_cls:
        engine.start()
        mock_stream_cls.assert_called_once_with(device=5, blocksize=engine.block_size, callback=engine._audio_callback)
    engine.stop()


def test_start_defaults_to_none_device_when_unspecified():
    engine, _ = make_engine()
    fake_stream = MagicMock()
    with patch("Audio_SpectraCLI.engine.sd.InputStream", return_value=fake_stream) as mock_stream_cls:
        engine.start()
        mock_stream_cls.assert_called_once_with(device=None, blocksize=engine.block_size, callback=engine._audio_callback)
    engine.stop()
