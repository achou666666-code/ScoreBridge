from fixture_score import fixture_score
from scorebridge.patches import apply_patch
from scorebridge.review import create_review_packet, apply_review
import json
from pathlib import Path

def test_replace_measure_is_atomic():
    score = fixture_score()
    updated, report = apply_patch(score, {"operation":"replace_measure", "part_id":"P1", "staff_id":"P1-S1", "measure":1,
        "events":[{"kind":"note","duration":"quarter","pitch":"G5"},{"kind":"note","duration":"quarter","pitch":"A5"},{"kind":"note","duration":"quarter","pitch":"B5"},{"kind":"note","duration":"quarter","pitch":"C6"}]})
    assert report["status"] == "pass"
    assert updated is not score
    assert updated.parts[0].staves[0].measures[0].events[0].pitch == "G5"
    assert score.parts[0].staves[0].measures[0].events[0].pitch == "C5"

def test_invalid_patch_does_not_mutate():
    score = fixture_score()
    updated, report = apply_patch(score, {"operation":"replace_measure", "part_id":"P1", "staff_id":"P1-S1", "measure":1,
        "events":[{"kind":"note","duration":"half","pitch":"G5"}]})
    assert report["status"] == "error"
    assert updated is score


def test_review_packet_and_decision_roundtrip(tmp_path):
    score_path = tmp_path / "score.json"
    from scorebridge.score_ir import save_score
    save_score(fixture_score(), score_path)
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"pages": [{"page": 1, "rendered": "/tmp/page.png"}]}), encoding="utf-8")
    packet = create_review_packet(str(score_path), str(manifest))
    assert packet["schema"] == "scorebridge.review.v1"
    assert packet["task_count"] == 10
    assert packet["tasks"][0]["evidence"]["rendered"] == "/tmp/page.png"
    decisions = tmp_path / "decisions.json"
    payload = {"tasks": [{"target": {"part_id": "P1", "staff_id": "P1-S1", "measure": 1},
                           "id": "P1:P1-S1:1", "decision": {"confidence": 0.98, "rationale": "Visible quarter notes", "patch": {
                               "events": [{"kind": "note", "duration": "quarter", "pitch": "G5"}] * 4}}}]}
    decisions.write_text(json.dumps(payload), encoding="utf-8")
    result = apply_review(str(score_path), str(decisions), str(tmp_path / "reviewed.json"))
    assert result["status"] == "pass"
    assert result["applied"] == ["P1:P1-S1:1"]
    assert result["decision_log"][0]["confidence"] == 0.98
