from scorebridge.musescore import MuseScoreWebSocketBackend


def test_websocket_backend_uses_configured_url(monkeypatch):
    monkeypatch.setenv("SCOREBRIDGE_MUSESCORE_WS", "ws://127.0.0.1:9876")
    backend = MuseScoreWebSocketBackend()
    assert backend.url == "ws://127.0.0.1:9876"
