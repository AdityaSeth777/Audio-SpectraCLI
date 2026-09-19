"""Regression tests for bugs found in a targeted code-review pass over the
newly-expanded main.py (view modes, dB scale, presets, recording). Each test
name states the bug it guards against.
"""

import os
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from unittest.mock import MagicMock, patch

import numpy as np
from PyQt5.QtWidgets import QApplication

from Audio_SpectraCLI import AudioSpectrumVisualizer

_app = QApplication.instance() or QApplication([])


def _tone_frame(window, freq_hz=440):
    t = np.arange(window.block_size) / window.fs
    signal = np.sin(2 * np.pi * freq_hz * t)
    freq_bins = np.fft.rfftfreq(window.block_size, 1 / window.fs)
    spectrum = np.abs(np.fft.rfft(signal, n=window.block_size))
    return freq_bins, spectrum, float(np.max(spectrum))


def test_bars_view_uses_the_visible_frequency_range_not_the_full_spectrum():
    """Bug: bars were downsampled from the full 0..Nyquist spectrum while
    the bar width was sized for the (narrower) selected frequency range,
    producing thin, sparse bars instead of a full-width equalizer."""
    window = AudioSpectrumVisualizer()
    window.view_mode_combo.setCurrentText("Bars")
    window.apply_frequency_preset("0 - 2,500 Hz")

    freq_bins, spectrum, max_magnitude = _tone_frame(window, freq_hz=440)
    window.update_plot(freq_bins, spectrum, max_magnitude)

    bar_patches = window.ax.patches
    assert len(bar_patches) > 0
    bar_xs = [p.get_x() for p in bar_patches]
    # Every bar's left edge should fall within (or right at the edge of)
    # the selected 0-2500Hz range, not spread across the full spectrum.
    assert max(bar_xs) <= 2500 + 1e-6, f"bars should stay within the selected range, got max x={max(bar_xs)}"
    window.close()


def test_db_scale_ylim_gives_headroom_above_the_peak_not_below_it():
    """Bug: `visible_max * 1.2` gives a ceiling BELOW a negative dB peak
    (e.g. -10 * 1.2 = -12), clipping the peak off the top of the plot."""
    window = AudioSpectrumVisualizer()
    window.db_scale_checkbox.setChecked(True)

    freq_bins, spectrum, max_magnitude = _tone_frame(window, freq_hz=440)
    window.update_plot(freq_bins, spectrum, max_magnitude)

    _, y_top = window.ax.get_ylim()
    from Audio_SpectraCLI.analysis import magnitude_to_db

    mask = window._visible_mask(freq_bins)
    actual_peak_db = float(np.max(magnitude_to_db(spectrum)[mask]))
    assert y_top >= actual_peak_db, f"y-axis top ({y_top}) must be at or above the actual peak ({actual_peak_db})"
    window.close()


def test_toggling_db_scale_resets_waterfall_history():
    """Bug: switching dB scale mid-session while in Waterfall view left old
    linear-magnitude rows mixed with new dB rows in the same history."""
    window = AudioSpectrumVisualizer()
    window.view_mode_combo.setCurrentText("Waterfall")
    frame = _tone_frame(window)
    window.update_plot(*frame)
    assert len(window.waterfall_history) > 0

    window.db_scale_checkbox.setChecked(True)
    assert window.waterfall_history == []
    window.close()


def test_waterfall_rows_stay_a_fixed_width_even_when_visible_bin_count_changes():
    """Bug: downsample_max_pool returns its input UNCHANGED when already
    shorter than the target width, so changing the frequency range live
    (which changes how many bins are visible) could append rows of
    different lengths, making np.array(history) ragged and crashing imshow
    - and permanently corrupting the history, since the bad row was already
    appended before the crash."""
    window = AudioSpectrumVisualizer()
    window.view_mode_combo.setCurrentText("Waterfall")

    window.apply_frequency_preset("0 - 20,000 Hz (default)")
    window.update_plot(*_tone_frame(window))

    # Narrow the range a lot - drastically changes the visible bin count -
    # while Waterfall history has already accumulated rows from the wider range.
    window.apply_frequency_preset("0 - 2,500 Hz")
    window.update_plot(*_tone_frame(window))  # must not raise

    row_lengths = {len(row) for row in window.waterfall_history}
    assert row_lengths == {200}, f"all waterfall rows must share one fixed width, got lengths {row_lengths}"
    window.close()


def test_loading_a_preset_applies_a_non_overlapping_frequency_range_correctly():
    """Bug: apply_settings_dict set freq_max before freq_min; if the
    window's CURRENT range doesn't overlap the preset's new range (e.g.
    current (15000, 20000), preset wants (0, 2500)), the max-update was
    silently rejected mid-way and the final range ended up wrong."""
    window = AudioSpectrumVisualizer()
    window.freq_min_spinbox.setValue(15000)
    window.freq_max_spinbox.setValue(20000)
    assert window.frequency_range == (15000, 20000)

    window.apply_settings_dict({"frequency_range": [0, 2500]})

    assert window.frequency_range == (0, 2500)
    assert window.freq_min_spinbox.value() == 0
    assert window.freq_max_spinbox.value() == 2500
    window.close()


def test_load_preset_with_malformed_json_shows_warning_instead_of_crashing(tmp_path):
    """Bug: load_preset's json.load()/apply_settings_dict() call ran
    unguarded inside a button-click Qt slot - a non-JSON file raised
    json.JSONDecodeError straight out of the slot uncaught."""
    window = AudioSpectrumVisualizer()
    bad_file = tmp_path / "not_json.json"
    bad_file.write_text("this is not valid json {{{")

    with patch("Audio_SpectraCLI.main.QFileDialog.getOpenFileName", return_value=(str(bad_file), "")):
        with patch("Audio_SpectraCLI.main.QMessageBox.warning") as mock_warn:
            window.load_preset()  # must not raise
            mock_warn.assert_called_once()
    window.close()


def test_load_preset_with_wrong_shape_shows_warning_instead_of_crashing(tmp_path):
    """A syntactically valid JSON file whose frequency_range isn't a
    2-element list must not crash the button-click slot either."""
    import json as json_module

    window = AudioSpectrumVisualizer()
    bad_file = tmp_path / "wrong_shape.json"
    bad_file.write_text(json_module.dumps({"frequency_range": [1, 2, 3]}))

    with patch("Audio_SpectraCLI.main.QFileDialog.getOpenFileName", return_value=(str(bad_file), "")):
        with patch("Audio_SpectraCLI.main.QMessageBox.warning") as mock_warn:
            window.load_preset()  # must not raise
            mock_warn.assert_called_once()
    window.close()


def test_export_png_to_an_unwritable_path_shows_warning_instead_of_crashing():
    window = AudioSpectrumVisualizer()
    window._latest_frame = _tone_frame(window)
    window.update_plot(*window._latest_frame)

    with patch("Audio_SpectraCLI.main.QFileDialog.getSaveFileName", return_value=("/nonexistent_dir/out.png", "")):
        with patch("Audio_SpectraCLI.main.QMessageBox.warning") as mock_warn:
            window.export_png()  # must not raise
            mock_warn.assert_called_once()
    window.close()


def test_engine_start_failure_shows_warning_instead_of_crashing():
    """Bug: sd.InputStream(...)/.start() raise on ordinary conditions
    (device unplugged, unsupported fs/channels) and ran completely
    unguarded inside the Start button's click slot."""
    window = AudioSpectrumVisualizer()

    with patch("Audio_SpectraCLI.engine.sd.InputStream", side_effect=RuntimeError("device unavailable")):
        with patch("Audio_SpectraCLI.main.QMessageBox.warning") as mock_warn:
            window.toggle_visualization()  # must not raise
            mock_warn.assert_called_once()

    assert window.engine is None, "a failed start must not leave a half-started engine assigned"
    assert window.start_button.text() == "Start Visualization"
    assert window.device_combo.isEnabled() is True
    window.close()


def test_midi_note_off_sent_when_stopping_while_a_note_is_sounding():
    """Bug: Stop Visualization never touched self.midi_sender, so a note
    started before Stop was clicked stayed on indefinitely."""
    window = AudioSpectrumVisualizer()
    fake_sender = MagicMock()
    window.midi_enabled = True
    window.midi_sender = fake_sender

    with patch("Audio_SpectraCLI.engine.sd.InputStream", return_value=MagicMock()):
        window.toggle_visualization()  # start
        window.toggle_visualization()  # stop

    fake_sender.stop.assert_called_once()
    window.close()


def test_midi_note_off_sent_after_silence_timeout():
    """Bug: send_note_for_frequency only sends note-off when a DIFFERENT
    note arrives, but engine.py's callback stops firing entirely once
    input goes quiet - so without an explicit silence watchdog, the last
    note before silence would sustain forever."""
    window = AudioSpectrumVisualizer()
    fake_sender = MagicMock()
    window.midi_enabled = True
    window.midi_sender = fake_sender

    window._last_spectrum_frame_time = time.monotonic() - 10  # long past the timeout
    window._check_midi_silence_timeout()

    fake_sender.stop.assert_called_once()
    assert window._last_spectrum_frame_time is None, "must not keep calling stop() every tick after the first"
    window.close()


def test_midi_silence_timeout_does_nothing_when_midi_disabled():
    window = AudioSpectrumVisualizer()
    window._last_spectrum_frame_time = time.monotonic() - 10
    window._check_midi_silence_timeout()  # must not raise even with midi_sender None
    window.close()


def test_stopping_visualization_while_recording_saves_instead_of_discarding():
    """Bug: clicking Stop Visualization while a WAV recording was in
    progress dropped the engine (and its buffered samples) without ever
    stopping/saving the recording, and left the Record button reading
    "Stop Recording" with no engine behind it - so clicking it next
    actually started a new recording instead of doing anything useful."""
    window = AudioSpectrumVisualizer()
    with patch("Audio_SpectraCLI.engine.sd.InputStream", return_value=MagicMock()):
        window.toggle_visualization()  # start
        window.toggle_recording()  # start recording
        assert window.engine.recording is True

        t = np.arange(window.block_size) / window.fs
        block = np.sin(2 * np.pi * 440 * t).astype(np.float32).reshape(-1, 1)
        window.engine.audio_queue.put(block)
        import time

        deadline = time.time() + 2
        while len(window.engine._recorded_chunks) == 0 and time.time() < deadline:
            time.sleep(0.01)
        assert len(window.engine._recorded_chunks) > 0

        with patch("Audio_SpectraCLI.main.QFileDialog.getSaveFileName", return_value=("", "")):
            window.toggle_visualization()  # stop while still recording

        assert window.engine is None
        assert window.record_button.text() == "Start Recording (WAV)", (
            "the Record button must not be left reading 'Stop Recording' once the engine is gone"
        )
    window.close()


def test_closing_the_window_while_recording_saves_instead_of_discarding():
    """Same bug as above, but via the window's close button/[X] (closeEvent)
    instead of the Stop Visualization button — closing the window mid-
    recording used to stop the engine without ever calling
    stop_recording()/offering to save, silently losing the buffered audio.

    QFileDialog.getSaveFileName genuinely hangs forever under the offscreen
    Qt platform used for tests (confirmed directly: a 5s timeout was hit)
    since there's no real UI to dismiss it — so this must mock it, same as
    every other test that exercises _finish_recording.
    """
    window = AudioSpectrumVisualizer()
    with patch("Audio_SpectraCLI.engine.sd.InputStream", return_value=MagicMock()):
        window.toggle_visualization()  # start
        window.toggle_recording()  # start recording
        assert window.engine.recording is True

        t = np.arange(window.block_size) / window.fs
        block = np.sin(2 * np.pi * 440 * t).astype(np.float32).reshape(-1, 1)
        window.engine.audio_queue.put(block)
        import time

        deadline = time.time() + 2
        while len(window.engine._recorded_chunks) == 0 and time.time() < deadline:
            time.sleep(0.01)
        assert len(window.engine._recorded_chunks) > 0

        with patch("Audio_SpectraCLI.main.QFileDialog.getSaveFileName", return_value=("", "")) as mock_dialog:
            window.close()  # must not raise, must not hang
            mock_dialog.assert_called_once()  # confirms _finish_recording actually ran, not skipped

        assert window.engine is None
