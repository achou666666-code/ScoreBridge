import subprocess

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
        return subprocess.CompletedProcess(args, 0, '插件 (P)\n', '')
    monkeypatch.setattr(connect.subprocess, 'run', run)
    assert connect.connect_editor()['activation'] == 'menu'
    assert len(calls) == 2
    assert calls[1][-1] == '插件 (P)'


def test_click_without_connection_is_not_success(monkeypatch):
    setup_bridge(monkeypatch, [{'available': False}])
    monkeypatch.setattr(connect.subprocess, 'run', lambda *a, **k: subprocess.CompletedProcess(a, 0, 'Plugins\n', ''))
    assert connect.connect_editor()['status'] == 'error'


def test_accessibility_failure_is_reported(monkeypatch):
    setup_bridge(monkeypatch, [{'available': False}])
    def fail(*args, **kwargs):
        raise subprocess.CalledProcessError(1, 'osascript', stderr='Accessibility denied')
    monkeypatch.setattr(connect.subprocess, 'run', fail)
    assert connect.connect_editor()['error'] == 'Accessibility denied'
