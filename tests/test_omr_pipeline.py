from zipfile import ZipFile

from scorebridge.omr import run_omr
from scorebridge.omr.pipeline import _find_musicxml
from scorebridge.workflow import transcribe_score

def test_omr_run_reports_missing_engine(tmp_path):
    source = tmp_path / "score.png"
    from PIL import Image
    Image.new("RGB", (20, 20), "white").save(source)
    result = run_omr(str(source), str(tmp_path / "out"), executable=str(tmp_path / "missing-audiveris"))
    assert result["status"] == "error"
    assert result["stage"] == "omr"
    assert "Install Audiveris" in result["hint"]


def test_find_musicxml_extracts_audiveris_mxl(tmp_path):
    container = tmp_path / "recognized.mxl"
    score_xml = b'<?xml version="1.0"?><score-partwise version="4.0"/>'
    with ZipFile(container, "w") as archive:
        archive.writestr("META-INF/container.xml", "<container/>")
        archive.writestr("recognized.xml", score_xml)

    result = _find_musicxml(tmp_path)

    assert result == tmp_path / "recognized.musicxml"
    assert result.read_bytes() == score_xml


def test_transcribe_prepares_input_before_engine_error(tmp_path):
    from PIL import Image
    source = tmp_path / "pages"; source.mkdir()
    Image.new("RGB", (20, 20), "white").save(source / "page-1.png")
    result = transcribe_score(str(source), str(tmp_path / "job"), audiveris=str(tmp_path / "missing"))
    assert result["status"] == "error"
    assert result["stage"] == "omr"
    assert (tmp_path / "job/evidence/manifest.json").exists()
