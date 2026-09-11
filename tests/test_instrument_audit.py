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
