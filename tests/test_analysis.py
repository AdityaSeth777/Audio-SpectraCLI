import numpy as np

from Audio_SpectraCLI.analysis import (
    BeatDetector,
    apply_window,
    downsample_max_pool,
    magnitude_to_db,
    nearest_musical_note,
)


def test_apply_window_none_is_identity():
    samples = np.array([1.0, 2.0, 3.0, 4.0])
    result = apply_window(samples, "none")
    assert np.array_equal(result, samples)


def test_apply_window_hann_tapers_edges_toward_zero():
    samples = np.ones(8)
    result = apply_window(samples, "hann")
    assert result[0] < 0.01
    assert result[-1] < 0.01
    assert result[4] > 0.9


def test_apply_window_hamming_and_blackman_do_not_raise():
    samples = np.ones(8)
    assert len(apply_window(samples, "hamming")) == 8
    assert len(apply_window(samples, "blackman")) == 8


def test_magnitude_to_db_matches_known_values():
    assert abs(magnitude_to_db(1.0) - 0.0) < 1e-6
    assert abs(magnitude_to_db(0.1) - (-20.0)) < 1e-6


def test_magnitude_to_db_floors_silence():
    assert magnitude_to_db(0.0) == -100.0


def test_nearest_musical_note_identifies_a4():
    note = nearest_musical_note(440.0)
    assert note == ("A", 4, 0.0) or (note[0] == "A" and note[1] == 4 and abs(note[2]) < 0.01)


def test_nearest_musical_note_identifies_slightly_off_pitch():
    note_name, octave, cents = nearest_musical_note(445.0)  # a bit sharp of A4
    assert note_name == "A"
    assert octave == 4
    assert cents > 0


def test_nearest_musical_note_rejects_invalid_input():
    assert nearest_musical_note(0) is None
    assert nearest_musical_note(-100) is None
    assert nearest_musical_note(float("nan")) is None


def test_beat_detector_returns_none_before_enough_onsets():
    detector = BeatDetector()
    assert detector.process(np.array([0.1, 0.1])) is None


def test_beat_detector_estimates_a_steady_tempo():
    clock_time = [0.0]
    detector = BeatDetector(sensitivity=1.5, clock=lambda: clock_time[0])

    quiet = np.full(10, 0.01)
    loud = np.full(10, 1.0)

    # Simulate a steady 120 BPM beat: one loud "hit" every 0.5s, quiet between.
    interval = 0.5
    for _ in range(8):
        detector.process(quiet)
        clock_time[0] += 0.05
        bpm = detector.process(loud)
        clock_time[0] += interval - 0.05

    assert bpm is not None
    assert 100 < bpm < 140  # allow slack for the heuristic, not exact


def test_downsample_max_pool_returns_input_unchanged_when_already_short():
    values = np.array([1.0, 2.0, 3.0])
    assert list(downsample_max_pool(values, 5)) == [1.0, 2.0, 3.0]


def test_downsample_max_pool_reduces_via_max():
    values = np.arange(10, dtype=float)
    result = downsample_max_pool(values, 3)
    assert len(result) == 3
    assert result[-1] == 9


def test_beat_detector_reset_clears_state():
    detector = BeatDetector()
    detector.process(np.array([1.0]))
    detector.reset()
    assert detector._energy_history == []
    assert detector._onset_times == []
