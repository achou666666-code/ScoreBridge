from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

from scorebridge.musescore.seed import build_seed_musicxml, create_seed_score


def orchestral_spec():
    return {
        "title": "Agent Orchestra",
        "measures": 5,
        "time": {"beats": 12, "beat_type": 8},
        "key_fifths": -2,
        "tempo_bpm": 124,
        "parts": [
            {"name": "Flute", "instrument_id": "flute"},
            {"name": "Clarinet in B-flat", "instrument_id": "clarinet in bb"},
            {"name": "Piano", "instrument_id": "piano", "clefs": ["treble", "bass"]},
        ],
    }


def test_seed_musicxml_contains_parts_meter_transposition_and_measure_rests(tmp_path):
    output = build_seed_musicxml(orchestral_spec(), str(tmp_path / "seed.musicxml"), target_id="sb-test")
    root = ET.parse(output).getroot()
    assert root.findtext("./identification/miscellaneous/miscellaneous-field") == "sb-test"
    score_parts = root.findall("./part-list/score-part")
    assert [part.findtext("part-name") for part in score_parts] == [
        "Flute", "Clarinet in B-flat", "Piano"
    ]
    assert [part.findtext("score-instrument/instrument-sound") for part in score_parts] == [
        "wind.flutes.flute", "wind.reed.clarinet.clarinet", "keyboard.piano"
    ]
    parts = root.findall("./part")
    assert [len(part.findall("measure")) for part in parts] == [5, 5, 5]
    first = parts[0].find("measure")
    assert first.findtext("attributes/divisions") == "24"
    assert first.findtext("attributes/time/beats") == "12"
    assert first.findtext("attributes/time/beat-type") == "8"
    assert first.findtext("attributes/key/fifths") == "-2"
    assert first.findtext("note/duration") == "144"
    assert first.find("note/rest").get("measure") == "yes"
    clarinet = parts[1].find("measure")
    assert clarinet.findtext("attributes/transpose/chromatic") == "-2"
    piano = parts[2].find("measure")
    assert piano.findtext("attributes/staves") == "2"
    assert [clef.findtext("sign") for clef in piano.findall("attributes/clef")] == ["G", "F"]
    assert len(piano.findall("note")) == 2
    assert piano.findtext("backup/duration") == "144"
    assert first.findtext("direction/direction-type/metronome/per-minute") == "124"


class FakeAdapter:
    def __init__(self):
        self.converted = None
        self.opened = None

    def convert(self, input_path, output_path):
        self.converted = (input_path, output_path)
        with ZipFile(output_path, "w") as archive:
            archive.writestr("score.mscx", "<museScore/>")
        return {"output_path": str(Path(output_path).resolve()), "output_valid": True}

    def open_score(self, input_path):
        self.opened = input_path
        return {"status": "pass", "input_path": str(Path(input_path).resolve()), "pid": 42}


def test_create_seed_score_converts_opens_and_returns_instrument_plan(tmp_path):
    adapter = FakeAdapter()
    output = tmp_path / "agent.mscz"
    bound = []
    def binder(input_path, target, adapter):
        bound.append((input_path, target, adapter))
        return {"status": "bound", "actual": target}
    result = create_seed_score(orchestral_spec(), str(output), open_editor=True,
                               adapter=adapter, binder=binder)
    assert result["status"] == "pass"
    assert result["mscz_path"] == str(output.resolve())
    assert output.is_file()
    assert adapter.opened is None
    assert bound[0][0] == str(output)
    assert bound[0][2] is adapter
    assert result["target"]["targetId"].startswith("scorebridge-")
    assert result["target"]["scoreName"] == "agent"
    assert result["target"]["numMeasures"] == 5
    assert result["target"]["numStaves"] == 4
    assert [part["instrument_id"] for part in result["parts"]] == ["flute", "bb-clarinet", "piano"]
    assert [step["action"] for step in result["instrument_steps"]] == [
        "setPartInstrument", "setPartInstrument", "setPartInstrument"
    ]
    assert result["instrument_steps"][1]["params"] == {"part": 1, "instrumentId": "bb-clarinet"}
    assert result["instrument_steps"][2]["params"] == {"part": 2, "instrumentId": "piano"}
    assert Path(result["internal_musicxml"]).is_file()


def test_create_seed_score_rejects_unresolved_instrument_and_wrong_suffix(tmp_path):
    bad = orchestral_spec()
    bad["parts"] = [{"name": "Mystery", "instrument_id": "mystery"}]
    unresolved = create_seed_score(bad, str(tmp_path / "bad.mscz"), adapter=FakeAdapter())
    assert unresolved["status"] == "error"
    assert unresolved["stage"] == "specification"
    assert "unresolved" in unresolved["error"]
    wrong = create_seed_score(orchestral_spec(), str(tmp_path / "bad.musicxml"), adapter=FakeAdapter())
    assert wrong == {"status": "error", "error": "output_path must end in .mscz"}


def test_explicit_sound_allows_catalog_extension(tmp_path):
    spec = orchestral_spec()
    spec["parts"] = [{"name": "Custom Wind", "instrument_id": "custom-wind", "musescore_id": "flute",
                      "instrument_sound": "wind.custom", "midi_program": 75}]
    output = build_seed_musicxml(spec, str(tmp_path / "custom.musicxml"))
    root = ET.parse(output).getroot()
    assert root.findtext("./part-list/score-part/score-instrument/instrument-sound") == "wind.custom"
    assert root.findtext("./part-list/score-part/midi-instrument/midi-program") == "75"
