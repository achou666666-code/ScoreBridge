import subprocess
from pathlib import Path

from scorebridge.musescore import connect


def setup_bridge(monkeypatch, states):
    class Bridge:
        def status(self):
            return states.pop(0) if len(states) > 1 else states[0]
    monkeypatch.setattr(connect, 'MuseScoreWebSocketBackend', lambda **kw: Bridge())
    monkeypatch.setattr(connect.sys, 'platform', 'darwin')
    monkeypatch.setattr(connect.time, 'sleep', lambda _: None)


def test_connected_editor_is_not_clicked_again(monkeypatch):
    setup_bridge(monkeypatch, [{'available': True}])
    def forbidden(*args, **kwargs):
        raise AssertionError('Already connected: no menu click expected')
    monkeypatch.setattr(connect.subprocess, 'run', forbidden)
    assert connect.connect_editor()['activation'] == 'already_running'


def test_menu_discovery_and_activation_are_separate(monkeypatch):
    setup_bridge(monkeypatch, [{'available': False}, {'available': True}])
    calls = []
    def run(args, **kwargs):
        calls.append(args)
        return subprocess.CompletedProcess(args, 0, '插件 (P)\nMuseScore API Server\n', '')
    monkeypatch.setattr(connect.subprocess, 'run', run)
    assert connect.connect_editor()['activation'] == 'menu'
    assert len(calls) == 2
    assert calls[1][-2:] == ['插件 (P)', 'MuseScore API Server']


def test_click_without_connection_is_not_success(monkeypatch):
    setup_bridge(monkeypatch, [{'available': False}])
    monkeypatch.setattr(connect.subprocess, 'run', lambda *a, **k: subprocess.CompletedProcess(a, 0, 'Plugins\nmusescore-mcp-websocket\n', ''))
    assert connect.connect_editor()['status'] == 'error'


def test_accessibility_failure_is_reported(monkeypatch):
    setup_bridge(monkeypatch, [{'available': False}])
    def fail(*args, **kwargs):
        raise subprocess.CalledProcessError(1, 'osascript', stderr='Accessibility denied')
    monkeypatch.setattr(connect.subprocess, 'run', fail)
    assert connect.connect_editor()['error'] == 'Accessibility denied'


TARGET = {'targetId': 'sb-1', 'scoreName': 'target', 'title': 'Target',
          'numMeasures': 5, 'numStaves': 2}


class IdentityBridge:
    url = 'ws://localhost:8765'
    def __init__(self, available, identities):
        self.available = available
        self.identities = list(identities)
        self.calls = []
    def status(self):
        return {'available': self.available}
    def command(self, action, params=None):
        self.calls.append(action)
        value = self.identities.pop(0) if len(self.identities) > 1 else self.identities[0]
        return {'result': value}


def score_file(tmp_path):
    path = tmp_path / 'target.mscz'
    path.write_bytes(b'score')
    return path


def test_bind_accepts_only_exact_current_target(tmp_path):
    bridge = IdentityBridge(True, [TARGET])
    result = connect.bind_editor_score(str(score_file(tmp_path)), TARGET, bridge=bridge)
    assert result['status'] == 'bound'
    assert result['activation'] == 'already_target'
    assert bridge.calls == ['getScoreIdentity']


def test_bind_refuses_to_switch_an_existing_wrong_listener(monkeypatch, tmp_path):
    wrong = {**TARGET, 'scoreName': 'wrong'}
    bridge = IdentityBridge(True, [wrong])
    result = connect.bind_editor_score(str(score_file(tmp_path)), TARGET, bridge=bridge, timeout=1)
    assert result['status'] == 'wrong_target'
    assert result['mismatches']['scoreName'] == {'expected': 'target', 'actual': 'wrong'}
    assert bridge.calls == ['getScoreIdentity']


def test_bind_launches_dedicated_process_and_activates_plugin(monkeypatch, tmp_path):
    bridge = IdentityBridge(False, [TARGET])
    class Adapter:
        def launch_score_process(self, path):
            return {'status': 'pass', 'pid': 5151, 'input_path': path}
    activations = []
    monkeypatch.setattr(connect, 'connect_editor',
                        lambda pid=None, **kwargs: activations.append(pid) or {'status': 'connected'})
    result = connect.bind_editor_score(str(score_file(tmp_path)), TARGET,
                                       adapter=Adapter(), bridge=bridge, timeout=1)
    assert result['status'] == 'bound'
    assert result['open']['pid'] == 5151
    assert activations == [5151]


def test_identity_mismatch_report_is_explicit():
    mismatches = connect.identity_mismatches(TARGET, {**TARGET, 'numStaves': 3})
    assert mismatches == {'numStaves': {'expected': 2, 'actual': 3}}


def test_identity_rejects_empty_or_invalid_target_fields():
    invalid = {**TARGET, 'targetId': '', 'numMeasures': True}
    assert connect.identity_mismatches(invalid, {}) == {
        'target': 'invalid expected fields: targetId, numMeasures'
    }
