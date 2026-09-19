"""Unit tests for the GUI's new interactive controls: frequency range
spinboxes/presets, the color picker, and the Gaussian-smoothing toggle.
"""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from unittest.mock import MagicMock, patch

from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QApplication

from Audio_SpectraCLI import AudioSpectrumVisualizer
from Audio_SpectraCLI.main import FREQUENCY_RANGE_PRESETS, GAUSSIAN_SMOOTHING_SIGMA

_app = QApplication.instance() or QApplication([])


def test_frequency_min_max_stay_editable_independently():
    window = AudioSpectrumVisualizer()
    window.set_frequency_min(500)
    assert window.frequency_range == (500, 20000)

    window.set_frequency_max(7500)
    assert window.frequency_range == (500, 7500)
    window.close()


def test_frequency_min_cannot_cross_above_max():
    window = AudioSpectrumVisualizer()
    original = window.frequency_range
    window.freq_min_spinbox.setValue(original[1] + 1000)  # triggers set_frequency_min via the signal
    assert window.frequency_range == original, "an invalid min should be rejected, not silently break the range"
    window.close()


def test_frequency_max_cannot_cross_below_min():
    window = AudioSpectrumVisualizer()
    original = window.frequency_range
    window.freq_max_spinbox.setValue(max(0, original[0] - 1))
    assert window.frequency_range == original
    window.close()


def test_frequency_presets_update_both_spinboxes():
    window = AudioSpectrumVisualizer()
    label = "0 - 2,500 Hz"
    expected = FREQUENCY_RANGE_PRESETS[label]

    window.apply_frequency_preset(label)

    assert window.frequency_range == expected
    assert window.freq_min_spinbox.value() == expected[0]
    assert window.freq_max_spinbox.value() == expected[1]
    window.close()


def test_choose_color_updates_color_and_swatch():
    window = AudioSpectrumVisualizer(color="blue")
    with patch("Audio_SpectraCLI.main.QColorDialog.getColor", return_value=QColor("#ff0000")):
        window.choose_color()

    assert window.color == "#ff0000"
    assert "#ff0000" in window.color_button.styleSheet()
    window.close()


def test_choose_color_ignores_a_cancelled_dialog():
    window = AudioSpectrumVisualizer(color="blue")
    with patch("Audio_SpectraCLI.main.QColorDialog.getColor", return_value=QColor()):  # invalid = user hit Cancel
        window.choose_color()

    assert window.color == "blue"
    window.close()


def test_smoothing_checkbox_toggles_sigma_and_live_engine():
    window = AudioSpectrumVisualizer()

    with patch("Audio_SpectraCLI.engine.sd.InputStream", return_value=MagicMock()):
        window.toggle_visualization()  # start
        assert window.engine.smoothing_sigma == GAUSSIAN_SMOOTHING_SIGMA

        window.set_smoothing_enabled(False)
        assert window.smoothing_sigma == 0
        assert window.engine.smoothing_sigma == 0, "toggling while running should update the live engine, not just the next one"

        window.set_smoothing_enabled(True)
        assert window.engine.smoothing_sigma == GAUSSIAN_SMOOTHING_SIGMA

        window.toggle_visualization()  # stop

    window.close()


def test_smoothing_disabled_before_start_is_passed_to_new_engine():
    window = AudioSpectrumVisualizer()
    window.set_smoothing_enabled(False)

    with patch("Audio_SpectraCLI.engine.sd.InputStream", return_value=MagicMock()):
        window.toggle_visualization()  # start
        assert window.engine.smoothing_sigma == 0
        window.toggle_visualization()  # stop

    window.close()
