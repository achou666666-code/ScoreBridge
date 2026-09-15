import json

from scorebridge.instruments import instrument_spec


def test_common_instrument_aliases_resolve_to_playback_metadata():
    assert instrument_spec("Flute")["instrument_sound"] == "wind.flutes.flute"
    assert instrument_spec("Horn in F")["midi_program"] == 61
    assert instrument_spec("Violin 1")["instrument_sound"] == "strings.violin"


def test_unknown_instrument_does_not_silently_fallback_to_piano():
    assert instrument_spec("celesta-like mystery") == {}


def test_audit_deduplicates_unresolved_ids():
    from scorebridge.instrument_audit import audit_instruments
    from scorebridge.score_ir import Score, Part, Staff
    score = Score(title="Audit", pitch_mode="written", parts=[
        Part(id="p1", name="Mystery 1", instrument_id="unknown", staves=[Staff(id="s1")]),
        Part(id="p2", name="Mystery 2", instrument_id="unknown", staves=[Staff(id="s2")]),
    ])
    report = audit_instruments(score)
    assert report["status"] == "needs_review"
    assert report["unresolved_instrument_ids"] == ["unknown"]


def test_cli_instrument_audit(tmp_path, monkeypatch, capsys):
    from scorebridge.score_ir import Score, Part, Staff, Measure, save_score
    from scorebridge.cli import main
    score_path = tmp_path / "score.json"
    score = Score(title="Audit", pitch_mode="written", parts=[
        Part(id="p1", name="Flute", instrument_id="Flute", staves=[Staff(id="s1", measures=[Measure(number=1)])])
    ])
    save_score(score, score_path)
    monkeypatch.setattr("sys.argv", ["scorebridge", "instrument-audit", str(score_path)])
    try:
        main()
    except SystemExit as exc:
        assert exc.code == 0
    report = __import__("json").loads(capsys.readouterr().out)
    assert report["status"] == "pass"
    assert report["parts"][0]["midi_program"] == 74


def test_canonical_names_flat_spellings_and_desk_numbers():
    from scorebridge.instrument_names import resolve_instrument_name
    from scorebridge.instruments import INSTRUMENTS
    for name in ["Clarinet in Bb", "Clarinet in B♭", "  clarinet in b-flat  "]:
        assert instrument_spec(name)["midi_program"] == 72
        assert instrument_spec(name)["transpose_chromatic"] == -2
    assert instrument_spec("Violin II")["midi_program"] == 41
    assert instrument_spec("Flute 2")["midi_program"] == 74
    for name in ["Flute-like mystery", "Alto Flute", "Violin electric unknown"]:
        assert resolve_instrument_name(name, INSTRUMENTS) == name


def test_piano_name_is_not_reported_as_accidental_fallback():
    from scorebridge.instrument_audit import audit_instruments
    from scorebridge.score_ir import Score, Part, Staff
    score = Score(title="Piano", pitch_mode="written", parts=[
        Part(id="p1", name="Piano", instrument_id="Piano", staves=[Staff(id="s1")])
    ])
    report = audit_instruments(score)
    assert report["status"] == "pass"
    assert report["piano_fallback_detected"] is False


def test_aliases_compile_to_real_playback_metadata(tmp_path):
    from xml.etree import ElementTree as ET
    from scorebridge.musicxml import compile_musicxml
    from scorebridge.score_ir import Score, Part, Staff, Measure
    score = Score(title="Named instruments", pitch_mode="written", parts=[
        Part(id="p1", name="Flute", instrument_id="Flute", staves=[Staff(id="s1", measures=[Measure(number=1)])]),
        Part(id="p2", name="Violin II", instrument_id="Violin II", staves=[Staff(id="s2", measures=[Measure(number=1)])])
    ])
    root = ET.parse(compile_musicxml(score, tmp_path / "names.musicxml"))
    assert root.findall("./part-list/score-part/midi-instrument/midi-program")[0].text == "74"
    assert root.findall("./part-list/score-part/midi-instrument/midi-program")[1].text == "41"
    assert [node.text for node in root.findall("./part-list/score-part/score-instrument/instrument-sound")] == ["wind.flutes.flute", "strings.violin"]
