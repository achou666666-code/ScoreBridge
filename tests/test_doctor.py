from scorebridge.doctor import diagnose


def test_doctor_returns_machine_readable_checks(monkeypatch):
    monkeypatch.setenv("AUDIVERIS_BIN", "/missing/audiveris")
    monkeypatch.setenv("MUSESCORE_BIN", "/missing/musescore")
    report = diagnose()
    assert report["status"] in {"pass", "needs_setup"}
    assert {item["name"] for item in report["checks"]} >= {"python", "audiveris", "musescore"}
