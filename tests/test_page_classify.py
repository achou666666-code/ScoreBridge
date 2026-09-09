from pathlib import Path

import pytest

from scorebridge.input import classify_page


def test_classify_blank_page_as_non_score(tmp_path):
    image = pytest.importorskip("PIL.Image")
    path = tmp_path / "blank.png"
    image.new("RGB", (300, 200), "white").save(path)
    result = classify_page(str(path))
    assert result["status"] == "pass"
    assert result["page_type"] == "non_score"


def test_classify_real_pirates_pages_conservatively():
    root = Path(__file__).parents[1] / "demos/pirates/output/pirates-regression-rerun/evidence/pages"
    cover = root / "page-0001.png"
    score = root / "page-0002.png"
    if not cover.exists() or not score.exists():
        pytest.skip("local Pirates regression evidence is not available")
    assert classify_page(str(cover))["page_type"] == "non_score"
    assert classify_page(str(score))["page_type"] in {"score", "uncertain"}
