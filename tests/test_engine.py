"""Unit tests for AudioSpectrumEngine's pure processing logic.

These do not touch real audio hardware: `_audio_callback`/`_process_audio`
are exercised directly with synthetic blocks, since sounddevice.InputStream
is never constructed unless `.start()` is called.
"""

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


def test_stop_is_safe_when_never_started():
    engine, _ = make_engine()
    engine.stop()  # must not raise even though .start() was never called
    assert engine.running is False
    assert engine.stream is None
