from fixture_score import fixture_score
from scorebridge.musicxml import compile_musicxml, parse_musicxml

def test_musicxml_roundtrip_parser(tmp_path):
    source = tmp_path / "source.musicxml"
    compile_musicxml(fixture_score(), source)
    score = parse_musicxml(source)
    assert len(score.parts) == 4
    assert score.parts[0].name == "Flute"
    assert len(score.parts[3].staves) == 2
    assert score.parts[0].staves[0].measures[0].events[0].pitch == "C5"
