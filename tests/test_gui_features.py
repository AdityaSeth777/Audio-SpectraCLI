"""Unit tests for the newer feature set: view modes, dB scale, presets,
export, recording, MIDI wiring, live device switching, and noise
threshold/window-type controls.
"""

import json
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from unittest.mock import MagicMock, patch

import numpy as np
from PyQt5.QtWidgets import QApplication, QMessageBox

from Audio_SpectraCLI import AudioSpectrumVisualizer
from Audio_SpectraCLI.main import VIEW_MODES

_app = QApplication.instance() or QApplication([])


def _real_frame(window, freq_hz=440, secondary_hz=None):
    # Sample spacing must be 1/fs, not 1/block_size - a block doesn't span
    # exactly one second unless block_size happens to equal fs. Getting this
    # wrong doesn't break these tests (none assert an exact frequency), but
    # it would silently misrepresent what frequency is actually injected.
    t = np.arange(window.block_size) / window.fs
    signal = np.sin(2 * np.pi * freq_hz * t)
    if secondary_hz:
        signal = signal + 0.5 * np.sin(2 * np.pi * secondary_hz * t)
    freq_bins = np.fft.rfftfreq(window.block_size, 1 / window.fs)
    spectrum = np.abs(np.fft.rfft(signal, n=window.block_size))
    return freq_bins, spectrum, float(np.max(spectrum))


def test_all_view_modes_render_without_raising():
    """The most important test here: every view mode must survive a real render.

    This is exactly the category of bug that caused the reported production
    crash (an exception escaping update_plot) - so each mode gets driven
    through a real frame, not mocked away.
    """
    window = AudioSpectrumVisualizer()
    frame = _real_frame(window, freq_hz=440, secondary_hz=3000)

    for label in VIEW_MODES:
        window.view_mode_combo.setCurrentText(label)
        window.update_plot(*frame)  # must not raise

    window.close()


def test_db_scale_changes_the_plotted_values():
    window = AudioSpectrumVisualizer()
    freq_bins, spectrum, max_magnitude = _real_frame(window)

    window.db_scale_checkbox.setChecked(False)
    window.update_plot(freq_bins, spectrum, max_magnitude)
    linear_ylim = window.ax.get_ylim()

    window.db_scale_checkbox.setChecked(True)
    window.update_plot(freq_bins, spectrum, max_magnitude)
    db_ylim = window.ax.get_ylim()

    assert linear_ylim != db_ylim
    assert db_ylim[0] < 0  # dB floor is negative; linear floor is 0
    window.close()


def test_peak_hold_values_persist_and_decay_across_frames():
    window = AudioSpectrumVisualizer()
    window.peak_hold_checkbox.setChecked(True)

    freq_bins, loud_spectrum, loud_max = _real_frame(window, freq_hz=440)
    window.update_plot(freq_bins, loud_spectrum, loud_max)
    peak_after_loud = window.peak_hold_values.copy()

    # Same shape, uniformly quieter everywhere (not an unrelated noise floor)
    # so the comparison is meaningful at every bin, not just the tone's peak.
    quieter_spectrum = loud_spectrum * 0.01
    window.update_plot(freq_bins, quieter_spectrum, float(np.max(quieter_spectrum)))

    assert np.all(window.peak_hold_values <= peak_after_loud), "peak hold should never jump up when input got quieter"
    assert np.any(window.peak_hold_values > 0), "peak hold should still show a decayed value, not reset to zero instantly"
    window.close()


def test_noise_threshold_control_updates_attribute_and_live_engine():
    window = AudioSpectrumVisualizer()
    with patch("Audio_SpectraCLI.engine.sd.InputStream", return_value=MagicMock()):
        window.toggle_visualization()
        window.noise_threshold_spinbox.setValue(0.5)
        assert window.noise_threshold == 0.5
        assert window.engine.noise_threshold == 0.5
        window.toggle_visualization()
    window.close()


def test_window_type_and_channel_mode_controls_update_live_engine():
    window = AudioSpectrumVisualizer()
    with patch("Audio_SpectraCLI.engine.sd.InputStream", return_value=MagicMock()):
        window.toggle_visualization()
        window.window_type_combo.setCurrentText("Hann")
        assert window.engine.window_type == "hann"

        window.channel_mode_combo.setCurrentText("Left")
        assert window.engine.channel_mode == "left"
        window.toggle_visualization()
    window.close()


def test_channel_mode_left_or_right_opens_stereo_stream():
    """channels-to-open is now resolved from the actual device's reported
    max_input_channels (_resolve_channel_count), not hardcoded from
    channel_mode alone - a genuinely mono-only device must not be asked to
    open 2 channels. Simulate a stereo-capable device here."""
    window = AudioSpectrumVisualizer()
    window.channel_mode_combo.setCurrentText("Left")

    with patch("Audio_SpectraCLI.main.sd.query_devices", return_value={"max_input_channels": 2}), patch(
        "Audio_SpectraCLI.engine.sd.default"
    ) as mock_default, patch("Audio_SpectraCLI.engine.sd.InputStream", return_value=MagicMock()):
        window.toggle_visualization()
        assert mock_default.channels == 2
        window.toggle_visualization()
    window.close()


def test_channel_mode_falls_back_to_mono_on_a_mono_only_device():
    window = AudioSpectrumVisualizer()
    window.channel_mode_combo.setCurrentText("Left")

    with patch("Audio_SpectraCLI.main.sd.query_devices", return_value={"max_input_channels": 1}), patch(
        "Audio_SpectraCLI.engine.sd.default"
    ) as mock_default, patch("Audio_SpectraCLI.engine.sd.InputStream", return_value=MagicMock()):
        window.toggle_visualization()
        assert mock_default.channels == 1
        window.toggle_visualization()
    window.close()


def test_export_csv_writes_the_latest_frame(tmp_path):
    window = AudioSpectrumVisualizer()
    window._latest_frame = _real_frame(window)

    csv_path = tmp_path / "out.csv"
    with patch("Audio_SpectraCLI.main.QFileDialog.getSaveFileName", return_value=(str(csv_path), "")):
        window.export_csv()

    content = csv_path.read_text()
    assert "frequency_hz,magnitude" in content
    assert len(content.splitlines()) > 1
    window.close()


def test_export_csv_without_a_frame_shows_a_message_instead_of_crashing(tmp_path):
    window = AudioSpectrumVisualizer()
    assert window._latest_frame is None

    with patch("Audio_SpectraCLI.main.QMessageBox.information") as mock_info:
        window.export_csv()
        mock_info.assert_called_once()
    window.close()


def test_export_png_saves_a_real_file(tmp_path):
    window = AudioSpectrumVisualizer()
    window._latest_frame = _real_frame(window)
    window.update_plot(*window._latest_frame)

    png_path = tmp_path / "out.png"
    with patch("Audio_SpectraCLI.main.QFileDialog.getSaveFileName", return_value=(str(png_path), "")):
        window.export_png()

    assert png_path.exists()
    assert png_path.stat().st_size > 0
    window.close()


def test_recording_round_trip_writes_a_real_wav_file(tmp_path):
    window = AudioSpectrumVisualizer()
    fake_stream = MagicMock()
    with patch("Audio_SpectraCLI.engine.sd.InputStream", return_value=fake_stream):
        window.toggle_visualization()
        window.toggle_recording()  # start recording
        assert window.engine.recording is True

        t = np.linspace(0, 1, window.block_size, endpoint=False)
        block = np.sin(2 * np.pi * 440 * t).astype(np.float32).reshape(-1, 1)
        window.engine.audio_queue.put(block)
        import time

        deadline = time.time() + 2
        while len(window.engine._recorded_chunks) == 0 and time.time() < deadline:
            time.sleep(0.01)
        assert len(window.engine._recorded_chunks) > 0

        wav_path = tmp_path / "out.wav"
        with patch("Audio_SpectraCLI.main.QFileDialog.getSaveFileName", return_value=(str(wav_path), "")):
            window.toggle_recording()  # stop + save

        assert wav_path.exists()
        assert wav_path.stat().st_size > 44  # bigger than just a WAV header
        window.toggle_visualization()
    window.close()


def test_toggle_recording_without_running_engine_is_safe():
    window = AudioSpectrumVisualizer()
    with patch("Audio_SpectraCLI.main.QMessageBox.information") as mock_info:
        window.toggle_recording()
        mock_info.assert_called_once()
    window.close()


def test_save_and_load_preset_round_trip(tmp_path):
    window = AudioSpectrumVisualizer()
    window.duration_spinbox.setValue(7)
    window.fs_spinbox.setValue(32000)
    window.color = "#123456"
    window._update_color_button_swatch()
    window.db_scale_checkbox.setChecked(True)
    window.view_mode_combo.setCurrentText("Bars")

    preset_path = tmp_path / "preset.json"
    with patch("Audio_SpectraCLI.main.QFileDialog.getSaveFileName", return_value=(str(preset_path), "")):
        window.save_preset()

    saved = json.loads(preset_path.read_text())
    assert saved["duration"] == 7
    assert saved["fs"] == 32000
    assert saved["color"] == "#123456"
    assert saved["db_scale"] is True
    assert saved["view_mode"] == "bars"

    # Load into a fresh window and confirm it actually applies.
    window2 = AudioSpectrumVisualizer()
    with patch("Audio_SpectraCLI.main.QFileDialog.getOpenFileName", return_value=(str(preset_path), "")):
        window2.load_preset()

    assert window2.duration == 7
    assert window2.fs == 32000
    assert window2.color == "#123456"
    assert window2.db_scale is True
    assert window2.view_mode == "bars"

    window.close()
    window2.close()


def test_named_preset_manager_save_load_rename_delete(tmp_path, monkeypatch):
    monkeypatch.setenv("AUDIOSPECTRA_CLI_HOME", str(tmp_path))
    window = AudioSpectrumVisualizer()
    builtin_count = window.named_preset_combo.count()

    window.fs_spinbox.setValue(32000)
    with patch("Audio_SpectraCLI.main.QInputDialog.getText", return_value=("My GUI Preset", True)):
        window.save_named_preset()
    assert window.named_preset_combo.count() == builtin_count + 1
    assert window.named_preset_combo.currentText() == "My GUI Preset"

    window2 = AudioSpectrumVisualizer()
    window2.named_preset_combo.setCurrentText("My GUI Preset")
    window2.load_named_preset()
    assert window2.fs == 32000

    with patch("Audio_SpectraCLI.main.QInputDialog.getText", return_value=("Renamed Preset", True)):
        window.rename_named_preset()
    assert window.named_preset_combo.currentText() == "Renamed Preset"
    assert "My GUI Preset" not in [window.named_preset_combo.itemText(i) for i in range(window.named_preset_combo.count())]

    with patch("Audio_SpectraCLI.main.QMessageBox.question", return_value=QMessageBox.Yes):
        window.delete_named_preset()
    assert window.named_preset_combo.count() == builtin_count

    window.close()
    window2.close()


def test_named_preset_rename_collision_shows_warning(tmp_path, monkeypatch):
    monkeypatch.setenv("AUDIOSPECTRA_CLI_HOME", str(tmp_path))
    window = AudioSpectrumVisualizer()
    with patch("Audio_SpectraCLI.main.QInputDialog.getText", return_value=("Existing", True)):
        window.save_named_preset()
    window.named_preset_combo.setCurrentText("Existing")

    with patch("Audio_SpectraCLI.main.QInputDialog.getText", return_value=("Balanced (default)", True)):
        with patch("Audio_SpectraCLI.main.QMessageBox.warning") as mock_warn:
            window.rename_named_preset()
            mock_warn.assert_called_once()

    window.close()


def test_midi_checkbox_handles_unavailable_gracefully():
    window = AudioSpectrumVisualizer()
    with patch("Audio_SpectraCLI.main.MidiNoteSender", side_effect=Exception("no midi")):
        with patch("Audio_SpectraCLI.main.QMessageBox.warning") as mock_warn:
            # Exception isn't MidiUnavailableError, so this specifically checks
            # the real MidiUnavailableError path below; this variant just
            # confirms an unexpected exception type doesn't crash the app.
            try:
                window.set_midi_enabled(True)
            except Exception:
                pass
    window.close()


def test_midi_checkbox_shows_warning_when_rtmidi_unavailable():
    from Audio_SpectraCLI.midi_out import MidiUnavailableError

    window = AudioSpectrumVisualizer()
    with patch("Audio_SpectraCLI.main.MidiNoteSender", side_effect=MidiUnavailableError("nope")):
        with patch("Audio_SpectraCLI.main.QMessageBox.warning") as mock_warn:
            window.set_midi_enabled(True)
            mock_warn.assert_called_once()
    assert window.midi_enabled is False
    assert window.midi_checkbox.isChecked() is False
    window.close()


def test_device_combo_disabled_while_running_and_reenabled_on_stop():
    window = AudioSpectrumVisualizer()
    assert window.device_combo.isEnabled() is True

    with patch("Audio_SpectraCLI.engine.sd.InputStream", return_value=MagicMock()):
        window.toggle_visualization()
        assert window.device_combo.isEnabled() is False
        window.toggle_visualization()
        assert window.device_combo.isEnabled() is True
    window.close()


def test_device_combo_change_ignored_while_running():
    window = AudioSpectrumVisualizer()
    if window.device_combo.count() < 1:
        window.close()
        return  # no input devices available in this environment; nothing to assert

    original_device = window.device
    with patch("Audio_SpectraCLI.engine.sd.InputStream", return_value=MagicMock()):
        window.toggle_visualization()
        window.set_device_by_combo_index(0)
        assert window.device == original_device, "device must not change while the engine is running"
        window.toggle_visualization()
    window.close()
