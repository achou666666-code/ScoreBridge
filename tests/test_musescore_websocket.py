from scorebridge.musescore import MuseScoreWebSocketBackend


def test_websocket_backend_uses_configured_url(monkeypatch):
    monkeypatch.setenv("SCOREBRIDGE_MUSESCORE_WS", "ws://127.0.0.1:9876")
    backend = MuseScoreWebSocketBackend()
    assert backend.url == "ws://127.0.0.1:9876"

import json
import threading
import pytest
from websockets.sync.server import serve
from scorebridge.musescore import MuseScoreWebSocketError


@pytest.mark.parametrize('wire_key', ['action', 'command'])
def test_real_socket_negotiates_protocol_and_propagates_error(wire_key):
    writes = []
    def handler(socket):
        for raw in socket:
            message = json.loads(raw)
            if wire_key not in message:
                socket.send(json.dumps({'error': 'missing field'}))
            elif message[wire_key] == 'ping':
                socket.send(json.dumps({'result': 'pong'}))
            else:
                writes.append(message[wire_key])
                socket.send(json.dumps({'status': 'success', 'result': {'error': 'No score open'}}))
    with serve(handler, '127.0.0.1', 0) as server:
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        bridge = MuseScoreWebSocketBackend(url=f'ws://127.0.0.1:{server.socket.getsockname()[1]}', timeout=2)
        assert bridge.status()['protocol'] == wire_key
        with pytest.raises(MuseScoreWebSocketError, match='No score open'):
            bridge.command('addNote', {'pitch': 60})
        assert writes == ['addNote']
        server.shutdown(); thread.join(3)


@pytest.mark.parametrize('reply', [{'error': 'bad'}, {'status': 'error', 'message': 'bad'}, {'result': {'valid': False}}, {'result': {'success': False}}])
def test_plugin_failures_are_not_success(reply):
    with pytest.raises(MuseScoreWebSocketError):
        MuseScoreWebSocketBackend._check_response(reply)
