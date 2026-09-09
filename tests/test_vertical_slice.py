from xml.etree import ElementTree as ET
from fixture_score import fixture_score
from scorebridge.musicxml import compile_musicxml
from scorebridge.validation import validate_score
from scorebridge.finalize import finalize_score

def test_fixture_validates(): assert validate_score(fixture_score())["status"] == "pass"
def test_compiles_musicxml(tmp_path):
    out=compile_musicxml(fixture_score(),tmp_path/"fixture.musicxml"); root=ET.parse(out).getroot()
    assert len(root.findall("./part")) == 4
    assert [len(p.findall("measure")) for p in root.findall("./part")] == [2,2,2,2]
    piano=root.findall("./part")[3]
    assert piano.findtext("./measure/attributes/staves") == "2"
    assert len(piano.findall("./measure/backup")) == 2
    parts=root.findall("./part")
    assert parts[1].findtext("./measure/attributes/transpose/chromatic") == "-2"
    assert parts[2].findtext("./measure/attributes/transpose/chromatic") == "-7"
    programs = [p.findtext("midi-instrument/midi-program") for p in root.findall("./part-list/score-part")]
    assert programs == ["74", "72", "61", "1"]


def test_finalize_without_musescore_keeps_musicxml(tmp_path):
    score_path = tmp_path / "score.json"
    from scorebridge.score_ir import save_score
    save_score(fixture_score(), score_path)
    result = finalize_score(str(score_path), str(tmp_path / "exports"), executable=str(tmp_path / "missing"))
    assert result["musicxml_path"]
    assert (tmp_path / "exports/score.musicxml").exists()
