"""Stress test: floods the engine with far more blocks than real audio ever
would in a short window, to confirm the fixed-rate render timer decouples
audio-thread rate from redraw rate and the GUI survives without backlog,
instead of the queued-signal-per-block approach that caused real freezing.
"""

import os
import time
from unittest.mock import MagicMock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np
from PyQt5.QtWidgets import QApplication

from Audio_SpectraCLI import AudioSpectrumVisualizer

_app = QApplication.instance() or QApplication([])


def test_survives_a_flood_of_blocks_far_faster_than_real_audio():
    window = AudioSpectrumVisualizer(duration=5, fs=22050, block_size=1024, color="red")

    fake_stream = MagicMock()
    with patch("Audio_SpectraCLI.engine.sd.InputStream", return_value=fake_stream):
        window.toggle_visualization()

        t = np.linspace(0, 1, window.engine.block_size, endpoint=False)
        loud_block = np.sin(2 * np.pi * 440 * t).astype(np.float32).reshape(-1, 1)

        # A real mic at this block size/rate delivers roughly one qualifying
        # block every ~46ms at most; 500 blocks in a tight loop is a wildly
        # unrealistic flood specifically to prove there's no unbounded queue
        # building up anymore.
        for _ in range(500):
            window.engine.audio_queue.put(loud_block.copy())

        deadline = time.time() + 3
        while len(window.ax.lines) == 0 and time.time() < deadline:
            _app.processEvents()
            time.sleep(0.01)

        assert len(window.ax.lines) == 1, "flood should still result in exactly one rendered line, not a backlog"

        # Stashing the latest frame (not a growing queue) means only ever
        # one pending frame regardless of how many blocks were flooded in.
        assert window._latest_frame is not None

        window.toggle_visualization()

    window.close()
