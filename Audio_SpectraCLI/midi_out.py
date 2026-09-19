# Aditya Seth
# Description: MIDI-out support - converts a dominant frequency into a MIDI
# note and sends it to a virtual MIDI port. mido/python-rtmidi are core
# dependencies (see requirements.txt/setup.py), but this module still
# degrades gracefully (RTMIDI_AVAILABLE/MidiUnavailableError) rather than
# hard-crashing on import, since python-rtmidi is a C-extension package that
# could still fail to build in some environment, and Windows has no native
# virtual MIDI port support at all without a third-party loopback driver
# like loopMIDI.

try:
    import rtmidi

    RTMIDI_AVAILABLE = True
except ImportError:
    RTMIDI_AVAILABLE = False


class MidiUnavailableError(Exception):
    pass


class MidiNoteSender:
    """Sends note-on/note-off MIDI messages for a live-changing dominant frequency.

    Opens one virtual MIDI output port on construction. Windows doesn't
    support creating virtual ports natively (rtmidi raises there) - this
    surfaces as MidiUnavailableError with a message pointing at loopMIDI,
    rather than a confusing raw rtmidi traceback.
    """

    def __init__(self, port_name="Audio-SpectraCLI"):
        if not RTMIDI_AVAILABLE:
            raise MidiUnavailableError(
                "python-rtmidi isn't installed. Install it with: pip install python-rtmidi mido"
            )

        # Wraps both MidiOut() construction and open_virtual_port() - not
        # just the latter - since either can raise on a given system (e.g.
        # no MIDI subsystem/driver at all), and any exception type here
        # should surface as a clear MidiUnavailableError, not an arbitrary
        # exception escaping into the GUI's checkbox-toggle slot.
        try:
            self._midiout = rtmidi.MidiOut()
            self._midiout.open_virtual_port(port_name)
        except Exception as exc:
            raise MidiUnavailableError(
                "Couldn't open a virtual MIDI port (Windows has no native virtual MIDI port support - "
                "install a loopback driver like loopMIDI, then pick a real output port instead)."
            ) from exc

        self._current_note = None

    def send_note_for_frequency(self, midi_note_number, velocity=100):
        """Sends note-off for the previous note (if any) and note-on for the new one."""
        midi_note_number = max(0, min(127, int(midi_note_number)))
        if midi_note_number == self._current_note:
            return

        if self._current_note is not None:
            self._midiout.send_message([0x80, self._current_note, 0])  # note off

        self._midiout.send_message([0x90, midi_note_number, velocity])  # note on
        self._current_note = midi_note_number

    def stop(self):
        if self._current_note is not None:
            self._midiout.send_message([0x80, self._current_note, 0])
            self._current_note = None

    def close(self):
        self.stop()
        self._midiout.close_port()
        del self._midiout


def frequency_to_midi_note(frequency_hz):
    """Converts a frequency in Hz to the nearest MIDI note number (69 = A4 = 440Hz)."""
    import numpy as np

    if frequency_hz is None or frequency_hz <= 0:
        return None
    return round(12 * np.log2(frequency_hz / 440.0) + 69)


__all__ = ["MidiNoteSender", "MidiUnavailableError", "RTMIDI_AVAILABLE", "frequency_to_midi_note"]
