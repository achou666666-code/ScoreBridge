"""Enable the installed plugin in a running macOS MuseScore instance."""
from pathlib import Path
import subprocess
import sys
import time

from .adapter import MuseScoreAdapter, MuseScoreError
from .websocket import MuseScoreWebSocketBackend


def _process_selector(pid=None):
    if pid is None:
        return 'set targetProcess to first process whose name is "mscore"'
    return f'set targetProcess to first process whose unix id is {int(pid)}'


def connect_editor(pid=None, timeout=12) -> dict:
    bridge = MuseScoreWebSocketBackend(timeout=2)
    state = bridge.status()
    if state['available']:
        return {'status': 'connected', 'activation': 'already_running', **state}
    if sys.platform != 'darwin':
        return {'status': 'error', 'error': 'Automatic plugin activation currently supports macOS only.'}
    # Locate the plugin across menus; MuseScore may expose either the extension
    # filename or its QML menuPath label depending on whether plugins were
    # reloaded in the current process.
    selector = _process_selector(pid)
    script = f'''tell application "System Events"
{selector}
tell targetProcess
set frontmost to true
if exists window "欢迎" then
    click button "确定" of window "欢迎"
    delay 0.5
end if
set pluginNames to {{"musescore-mcp-websocket", "MuseScore API Server"}}
repeat with topItem in menu bar items of menu bar 1
    try
        set topName to name of topItem
        set itemNames to name of every menu item of menu 1 of menu bar item topName of menu bar 1
        repeat with pluginName in pluginNames
            if itemNames contains pluginName then return topName & linefeed & pluginName
        end repeat
    end try
end repeat
error "Installed musescore-mcp-websocket menu item was not found"
end tell
end tell'''
    attempts = max(1, int(timeout / 0.25))
    menu_name = ""
    lookup_error = ""
    for _ in range(attempts):
        if menu_name:
            break
        try:
            found = subprocess.run(['osascript', '-e', script], check=True, capture_output=True,
                                   text=True, timeout=10)
            menu_name = found.stdout.strip()
        except (OSError, subprocess.SubprocessError) as exc:
            lookup_error = getattr(exc, 'stderr', None) or str(exc)
        if not menu_name:
            time.sleep(0.25)
    if not menu_name:
        return {'status': 'error', 'error': lookup_error or 'Plugin menu lookup returned no menu name.',
                'hint': 'Open MuseScore with a score; install the bundled plugin and allow Accessibility access.'}
    try:
        menu_name, plugin_name = menu_name.splitlines()[:2]
        activate = f'''on run argv
tell application "System Events"
{selector}
tell targetProcess
click menu item (item 2 of argv) of menu 1 of menu bar item (item 1 of argv) of menu bar 1
end tell
end tell
end run'''
        subprocess.run(['osascript', '-e', activate, menu_name, plugin_name], check=True,
                       capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError) as exc:
        detail = getattr(exc, 'stderr', None) or str(exc)
        return {'status': 'error', 'error': detail,
                'hint': 'Open MuseScore with a score; install the bundled plugin and allow Accessibility access.'}
    for _ in range(attempts):
        state = bridge.status()
        if state['available']:
            return {'status': 'connected', 'activation': 'menu', **state}
        time.sleep(0.25)
    return {'status': 'error', 'error': 'Plugin menu was activated but WebSocket did not connect.', 'editor': state}


def _identity_result(response):
    value = response.get("result", response) if isinstance(response, dict) else {}
    return value if isinstance(value, dict) else {}


def identity_mismatches(expected, actual):
    required = ("targetId", "scoreName", "title", "numMeasures", "numStaves")
    missing = [key for key in required if key not in expected]
    if missing:
        return {"target": "missing expected fields: " + ", ".join(missing)}
    invalid = []
    for key in ("targetId", "scoreName", "title"):
        if not isinstance(expected[key], str) or not expected[key]:
            invalid.append(key)
    for key in ("numMeasures", "numStaves"):
        if not isinstance(expected[key], int) or isinstance(expected[key], bool) or expected[key] < 1:
            invalid.append(key)
    if invalid:
        return {"target": "invalid expected fields: " + ", ".join(invalid)}
    return {key: {"expected": expected[key], "actual": actual.get(key)}
            for key in required if actual.get(key) != expected[key]}


def bind_editor_score(input_path, target, adapter=None, bridge=None, timeout=20) -> dict:
    """Open a score in the WebSocket-owning process and prove its exact identity."""
    source = Path(input_path)
    if not source.is_file():
        raise MuseScoreError(f"Input does not exist: {source}")
    backend = adapter or MuseScoreAdapter()
    socket = bridge or MuseScoreWebSocketBackend(timeout=2)
    state = socket.status()
    opened = None
    if state.get("available"):
        try:
            current = _identity_result(socket.command("getScoreIdentity"))
        except Exception:
            current = {}
        if not identity_mismatches(target, current):
            return {"status": "bound", "input_path": str(source.resolve()),
                    "target": target, "actual": current, "activation": "already_target"}
        return {"status": "wrong_target",
                "error": "The active MuseScore MCP listener belongs to another score; no file was opened and no edit was sent",
                "target": target, "actual": current,
                "mismatches": identity_mismatches(target, current),
                "next": "Stop the current MuseScore MCP listener, then bind this score again."}
    else:
        opened = backend.launch_score_process(str(source))
        pid = opened["pid"]
        activation = connect_editor(pid=pid, timeout=timeout)
        if not activation or activation.get("status") != "connected":
            return {"status": "error", "error": "MuseScore opened but its MCP plugin could not be activated",
                    "target": target, "open": opened, "activation": activation}

    deadline = time.monotonic() + timeout
    actual = {}
    last_error = None
    while time.monotonic() < deadline:
        try:
            actual = _identity_result(socket.command("getScoreIdentity"))
            if not identity_mismatches(target, actual):
                return {"status": "bound", "input_path": str(source.resolve()),
                        "target": target, "actual": actual, "open": opened}
        except Exception as exc:
            last_error = str(exc)
        time.sleep(0.25)
    return {"status": "error", "error": "MuseScore opened but the connected score identity did not match",
            "target": target, "actual": actual, "open": opened, "last_error": last_error,
            "mismatches": identity_mismatches(target, actual)}
