from pathlib import Path

from scorebridge.musicxml import compile_musicxml
from scorebridge.score_ir import load_score
from scorebridge.validation import validate_score


def test_public_vertical_slice_roundtrip(tmp_path):
    source = Path(__file__).parents[1] / "examples/vertical-slice.score.json"
    score = load_score(source)
    assert validate_score(score)["status"] == "pass"
    output = compile_musicxml(score, tmp_path / "smoke.musicxml")
    assert output.exists() and output.stat().st_size > 0
