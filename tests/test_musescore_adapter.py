import pytest
from scorebridge.musescore import MuseScoreAdapter, MuseScoreError

def test_convert_checks_input_before_launch(tmp_path):
    adapter = MuseScoreAdapter(executable="/bin/true")
    with pytest.raises(MuseScoreError, match="Input does not exist"):
        adapter.convert(str(tmp_path / "missing.musicxml"), str(tmp_path / "out.mscz"))


def test_invalid_explicit_executable_does_not_fall_back(tmp_path):
    assert MuseScoreAdapter(executable=str(tmp_path / 'missing')).resolve() is None


def test_failed_conversion_cannot_reuse_old_output(tmp_path, monkeypatch):
    import subprocess
    from zipfile import ZipFile
    source = tmp_path / 'source.musicxml'; source.write_text('<score-partwise/>')
    target = tmp_path / 'old.mscz'
    with ZipFile(target, 'w') as archive:
        archive.writestr('old.mscx', '<museScore/>')
    original = target.read_bytes()
    monkeypatch.setattr(MuseScoreAdapter, 'resolve', lambda self: source)
    monkeypatch.setattr(subprocess, 'run', lambda *a, **k: subprocess.CompletedProcess([], 1, '', 'failed'))
    with pytest.raises(MuseScoreError, match='failed'):
        MuseScoreAdapter().convert(str(source), str(target))
    assert target.read_bytes() == original
