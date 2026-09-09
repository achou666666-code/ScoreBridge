import pytest
from scorebridge.musescore import MuseScoreAdapter, MuseScoreError

def test_convert_checks_input_before_launch(tmp_path):
    adapter = MuseScoreAdapter(executable="/bin/true")
    with pytest.raises(MuseScoreError, match="Input does not exist"):
        adapter.convert(str(tmp_path / "missing.musicxml"), str(tmp_path / "out.mscz"))
