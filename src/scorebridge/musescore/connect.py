"""Enable the installed plugin in a running macOS MuseScore instance."""
import subprocess
import sys
import time

from .websocket import MuseScoreWebSocketBackend


def connect_editor() -> dict:
    bridge = MuseScoreWebSocketBackend(timeout=2)
    state = bridge.status()
    if state['available']:
        return {'status': 'connected', 'activation': 'already_running', **state}
    if sys.platform != 'darwin':
        return {'status': 'error', 'error': 'Automatic plugin activation currently supports macOS only.'}
    # Locate the exact plugin item across menus; menu titles depend on locale.
    script = '''tell application "System Events"
tell process "mscore"
set frontmost to true
if exists window "欢迎" then
    click button "确定" of window "欢迎"
    delay 0.5
end if
repeat with topItem in menu bar items of menu bar 1
    try
        set topName to name of topItem
        set itemNames to name of every menu item of menu 1 of menu bar item topName of menu bar 1
        if itemNames contains "musescore-mcp-websocket" then
            return topName
        end if
    end try
end repeat
error "Installed musescore-mcp-websocket menu item was not found"
end tell
end tell'''
    try:
        found = subprocess.run(['osascript', '-e', script], check=True, capture_output=True,
                               text=True, timeout=10)
        menu_name = found.stdout.strip()
        if not menu_name:
            return {'status': 'error', 'error': 'Plugin menu lookup returned no menu name.'}
        activate = '''on run argv
tell application "System Events"
tell process "mscore"
click menu item "musescore-mcp-websocket" of menu 1 of menu bar item (item 1 of argv) of menu bar 1
end tell
end tell
end run'''
        subprocess.run(['osascript', '-e', activate, menu_name], check=True,
                       capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError) as exc:
        detail = getattr(exc, 'stderr', None) or str(exc)
        return {'status': 'error', 'error': detail,
                'hint': 'Open MuseScore with a score; install the bundled plugin and allow Accessibility access.'}
    for _ in range(8):
        state = bridge.status()
        if state['available']:
            return {'status': 'connected', 'activation': 'menu', **state}
        time.sleep(0.25)
    return {'status': 'error', 'error': 'Plugin menu was activated but WebSocket did not connect.', 'editor': state}
