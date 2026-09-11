from pathlib import Path


def test_bundled_plugin_exposes_save_command():
    plugin = Path(__file__).parents[1] / "plugins" / "musescore-mcp-websocket.qml"
    text = plugin.read_text(encoding="utf-8")
    assert 'case "save":' in text
    assert 'cmd("file-save")' in text
    assert 'case "getCapabilities":' in text
