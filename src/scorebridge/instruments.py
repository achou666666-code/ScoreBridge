"""Canonical instrument metadata for MusicXML and MIDI export."""

INSTRUMENTS = {
    "wind.flutes.flute": {"name": "Flute", "midi_program": 74, "instrument_sound": "wind.flutes.flute"},
    "wind.reed.clarinet.bflat": {"name": "Clarinet in B-flat", "midi_program": 72, "instrument_sound": "wind.reed.clarinet.clarinet", "transpose_diatonic": -1, "transpose_chromatic": -2},
    "brass.french-horn": {"name": "Horn in F", "midi_program": 61, "instrument_sound": "brass.horns.french-horn", "transpose_diatonic": -4, "transpose_chromatic": -7},
    "strings.violin": {"name": "Violin", "midi_program": 41, "instrument_sound": "strings.violin"},
    "keyboard.piano": {"name": "Piano", "midi_program": 1, "instrument_sound": "keyboard.piano"},
}

def instrument_spec(instrument_id: str) -> dict:
    from .instrument_names import resolve_instrument_name
    instrument_id = resolve_instrument_name(instrument_id, INSTRUMENTS)
    return INSTRUMENTS.get(instrument_id, {})
