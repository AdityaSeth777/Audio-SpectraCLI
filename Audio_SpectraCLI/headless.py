# Aditya Seth
# Description: Headless, GUI-free entry point that streams spectrum frames as
# newline-delimited JSON on stdout. No PyQt5/matplotlib dependency — built for
# non-interactive consumers (the VS Code extension's webview, other scripts).
#
# Each line is a JSON object: {"freqBins": [...], "spectrum": [...], "maxMagnitude": <float>}
# `freqBins`/`spectrum` are downsampled to `--bars` points (max-pooled per bin
# group) so the payload stays small enough to stream at interactive rates.

import argparse
import json
import signal
import sys
import threading

import numpy as np

from .engine import AudioSpectrumEngine


def downsample_max_pool(values: np.ndarray, num_bars: int) -> np.ndarray:
    """Reduces `values` to `num_bars` points by taking the max within each group."""
    if len(values) <= num_bars:
        return values
    edges = np.linspace(0, len(values), num_bars + 1, dtype=int)
    return np.array([values[edges[i]:edges[i + 1]].max() for i in range(num_bars)])


def parse_args(argv):
    parser = argparse.ArgumentParser(description="Stream FFT spectrum frames as JSON lines.")
    parser.add_argument("--fs", type=int, default=44100, help="Sampling rate in Hz.")
    parser.add_argument("--block-size", type=int, default=4096, help="FFT block size.")
    parser.add_argument("--bars", type=int, default=64, help="Number of bars to downsample each frame to.")
    parser.add_argument("--noise-threshold", type=float, default=0.05)
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv if argv is not None else sys.argv[1:])

    def on_spectrum(freq_bins, spectrum, max_magnitude):
        payload = {
            "freqBins": downsample_max_pool(freq_bins, args.bars).round(1).tolist(),
            "spectrum": downsample_max_pool(spectrum, args.bars).round(4).tolist(),
            "maxMagnitude": float(max_magnitude),
        }
        sys.stdout.write(json.dumps(payload) + "\n")
        sys.stdout.flush()

    engine = AudioSpectrumEngine(
        on_spectrum=on_spectrum,
        fs=args.fs,
        block_size=args.block_size,
        noise_threshold=args.noise_threshold,
    )

    stop_event = threading.Event()

    def handle_signal(_sig, _frame):
        stop_event.set()

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    engine.start()
    # signal.pause() isn't available on Windows; an Event wait is portable
    # and still wakes immediately when a signal handler sets it.
    stop_event.wait()
    engine.stop()


if __name__ == "__main__":
    main()
