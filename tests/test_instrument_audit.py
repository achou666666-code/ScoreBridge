import json

from scorebridge.instruments import instrument_spec


def test_common_instrument_aliases_resolve_to_playback_metadata():
    assert instrument_spec("Flute")["instrument_sound"] == "wind.flutes.flute"
    assert instrument_spec("Horn in F")["midi_program"] == 61
    assert instrument_spec("Violin 1")["instrument_sound"] == "strings.violin"


def test_unknown_instrument_does_not_silently_fallback_to_piano():
    assert instrument_spec("celesta-like mystery") == {}
