import json
from pathlib import Path
import wave

import pytest

from scorebridge.audio import evaluate_audio_events, prepare_audio


def write_events(path, events):
    path.write_text(json.dumps({"schema_version": 1, "recognizer": "calling_agent", "events": events}))
    return str(path)


def note(pitch=60, start=0, end=1):
    return {"kind": "note", "midi_pitch": pitch, "start_seconds": start, "end_seconds": end}


def test_scoring_separates_notes_durations_and_extra_events(tmp_path):
    reference = write_events(tmp_path / "reference.json", [note(), note(64)])
    prediction = write_events(tmp_path / "prediction.json", [note(end=.5), note(64), note(64)])
    score = evaluate_audio_events(reference, prediction)
    assert score["status"] == "measured"
    assert score["note"]["matched"] == 2
    assert score["note"]["extra"] == 1
    assert score["note"]["precision"] == pytest.approx(2 / 3)
    assert score["note"]["with_offset"]["matched"] == 1
    assert score["drum"]["f1"] is None


def test_scoring_maximum_matching_not_greedy(tmp_path):
    reference = write_events(tmp_path / "r.json", [note(start=.04), note(start=0)])
    prediction = write_events(tmp_path / "p.json", [note(start=.02), note(start=.08)])
    assert evaluate_audio_events(reference, prediction)["note"]["matched"] == 2


def test_wrong_pitch_and_drum_category_are_not_matches(tmp_path):
    reference = write_events(tmp_path / "r.json", [note(), {"kind": "drum", "drum": "snare", "start_seconds": 0, "end_seconds": .1}])
    prediction = write_events(tmp_path / "p.json", [note(61), {"kind": "drum", "drum": "kick", "start_seconds": 0, "end_seconds": .1}])
    result = evaluate_audio_events(reference, prediction)
    assert result["note"]["matched"] == result["drum"]["matched"] == 0


@pytest.mark.parametrize("bad", [note(end=-1), note(start=float("nan")), note(pitch=True), note(pitch=128)])
def test_invalid_predictions_rejected(tmp_path, bad):
    reference = write_events(tmp_path / "r.json", [note()])
    prediction = write_events(tmp_path / "p.json", [bad])
    with pytest.raises(ValueError):
        evaluate_audio_events(reference, prediction)


def test_unassigned_instrument_is_not_counted_as_correct(tmp_path):
    reference = write_events(tmp_path / "r.json", [{**note(), "instrument_id": "flute"}])
    prediction = write_events(tmp_path / "p.json", [note()])
    result = evaluate_audio_events(reference, prediction)["note"]
    assert result["instrument_comparisons"] == 1
    assert result["instrument_matches"] == 0


def test_prepare_stereo_evidence_preserves_source_and_overlap(tmp_path, monkeypatch):
    np = pytest.importorskip("numpy")
    pytest.importorskip("matplotlib")
    monkeypatch.delenv("SCOREBRIDGE_FFMPEG", raising=False)
    monkeypatch.setattr("scorebridge.audio.prepare.shutil.which", lambda name: None)
    rate = 8000
    tone = .4 * np.sin(2 * np.pi * 440 * np.arange(rate * 3) / rate)
    # Opposite phase stereo must not disappear in the spectral evidence.
    samples = np.stack((tone, -tone), axis=1)
    original = tmp_path / "original.wav"
    with wave.open(str(original), "wb") as stream:
        stream.setparams((2, 2, rate, 0, "NONE", "not compressed"))
        stream.writeframes((samples * 32767).astype("<i2").tobytes())
    before = original.read_bytes()
    report = prepare_audio(str(original), str(tmp_path / "prepared"), 2, .5)
    assert report["status"] == "awaiting_agent"
    assert report["channels"] == 2
    assert len(report["segments"]) == 2
    assert report["segments"][1]["start_seconds"] == 1.5
    assert report["segments"][-1]["end_seconds"] == 3
    assert original.read_bytes() == before
    assert Path(report["original_audio"]).read_bytes() == before
    assert all(Path(s["spectrum"]).stat().st_size > 1000 for s in report["segments"])
    from scorebridge.audio.prepare import _spectrum
    bins, _, spectrum = _spectrum(samples, rate, .37)
    assert abs(bins[spectrum.mean(axis=1).argmax()] - 440) < 5


def test_prepare_missing_input_returns_error(tmp_path):
    assert prepare_audio(str(tmp_path / "missing.wav"), str(tmp_path / "out"))["status"] == "error"


@pytest.mark.parametrize("length,overlap", [(0, 0), (8, 8), (8, -1), (float("nan"), 1)])
def test_prepare_invalid_segments_return_error(tmp_path, length, overlap):
    assert prepare_audio(str(tmp_path / "unused.wav"), str(tmp_path / "out"), length, overlap)["status"] == "error"
