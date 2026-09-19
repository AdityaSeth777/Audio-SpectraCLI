"""Smoke test: confirms the native PyQt5 GUI still works end-to-end after the
engine.py extraction - construct the window, start visualization (with
sounddevice mocked out, since this sandbox has no audio hardware), inject a
synthetic spectrum through the engine's callback path, and confirm it reaches
the plot via the Qt signal, then stop cleanly.

Run with: QT_QPA_PLATFORM=offscreen python -m pytest tests/test_gui_smoke.py
"""

import os
import time
from unittest.mock import MagicMock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np
from PyQt5.QtWidgets import QApplication

from Audio_SpectraCLI import AudioSpectrumVisualizer

_app = QApplication.instance() or QApplication([])


def test_visualizer_starts_stops_and_receives_spectrum_via_engine():
    window = AudioSpectrumVisualizer(duration=5, fs=22050, block_size=1024, color="red")

    fake_stream = MagicMock()
    with patch("Audio_SpectraCLI.engine.sd.InputStream", return_value=fake_stream) as mock_stream_cls:
        window.toggle_visualization()  # Start
        assert window.engine is not None
        assert window.engine.running is True
        mock_stream_cls.assert_called_once()
        fake_stream.start.assert_called_once()

        # Drive one real block through the engine's actual FFT/smoothing path
        # (not mocked) to confirm the Qt signal wiring still delivers frames
        # to update_plot, exactly as the original single-file version did.
        t = np.linspace(0, 1, window.engine.block_size, endpoint=False)
        loud_block = np.sin(2 * np.pi * 440 * t).astype(np.float32).reshape(-1, 1)
        window.engine.audio_queue.put(loud_block)

        deadline = time.time() + 2
        while len(window.ax.lines) == 0 and time.time() < deadline:
            _app.processEvents()
            time.sleep(0.01)

        assert len(window.ax.lines) == 1, "engine's spectrum callback never reached update_plot"

        window.toggle_visualization()  # Stop
        assert window.engine is None
        fake_stream.stop.assert_called_once()
        fake_stream.close.assert_called_once()

    window.close()
