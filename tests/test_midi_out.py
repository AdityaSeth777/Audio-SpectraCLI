from Audio_SpectraCLI.midi_out import frequency_to_midi_note


def test_frequency_to_midi_note_a4():
    assert frequency_to_midi_note(440.0) == 69


def test_frequency_to_midi_note_c4():
    assert frequency_to_midi_note(261.63) == 60


def test_frequency_to_midi_note_rejects_invalid():
    assert frequency_to_midi_note(0) is None
    assert frequency_to_midi_note(-1) is None
    assert frequency_to_midi_note(None) is None
