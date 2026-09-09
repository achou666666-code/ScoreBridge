import pytest
from pathlib import Path
from scorebridge.input import inspect_input

def test_inspect_missing_input(tmp_path):
    result = inspect_input(str(tmp_path / "missing.png"))
    assert result["status"] == "error"

def test_inspect_unsupported_input(tmp_path):
    path = tmp_path / "input.txt"
    path.write_text("x")
    assert inspect_input(str(path))["status"] == "error"

def test_prepare_image(tmp_path):
    Image = pytest.importorskip("PIL.Image")
    source = tmp_path / "input.png"
    Image.new("RGB", (10, 8), "white").save(source)
    from scorebridge.input import prepare_image
    result = prepare_image(str(source), str(tmp_path / "prepared.png"))
    assert result["status"] == "pass"
    assert (tmp_path / "prepared.png").exists()


def test_prepare_input_sorts_image_pages_and_builds_manifest(tmp_path):
    Image = pytest.importorskip("PIL.Image")
    source = tmp_path / "pages"
    source.mkdir()
    for name, color in [("page-10.png", "red"), ("page-2.png", "green"), ("page-1.png", "blue")]:
        Image.new("RGB", (20, 12), color).save(source / name)
    from scorebridge.input import prepare_input
    result = prepare_input(str(source), str(tmp_path / "evidence"), dpi=120)
    assert result["status"] == "pass"
    assert result["page_count"] == 3
    assert [Path(item["source"]).name for item in result["pages"]] == ["page-1.png", "page-2.png", "page-10.png"]
    assert Path(result["internal_pdf"]).exists()
    assert Path(result["manifest_path"]).exists()
    assert all(Path(item["original"]).exists() and Path(item["rendered"]).exists() and Path(item["enhanced"]).exists()
               for item in result["pages"])


def test_prepare_input_pdf_renders_pages(tmp_path):
    fitz = pytest.importorskip("fitz")
    pdf = tmp_path / "score.pdf"
    doc = fitz.open()
    doc.new_page(width=100, height=80)
    doc.new_page(width=120, height=90)
    doc.save(pdf)
    doc.close()
    from scorebridge.input import prepare_input
    result = prepare_input(str(pdf), str(tmp_path / "evidence"), dpi=72)
    assert result["status"] == "pass"
    assert result["input_type"] == "pdf"
    assert result["page_count"] == 2
    assert [Path(item["rendered"]).name for item in result["pages"]] == ["page-0001.png", "page-0002.png"]
