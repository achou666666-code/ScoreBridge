from pathlib import Path


def test_bundled_plugin_exposes_save_command():
    plugin = Path(__file__).parents[1] / "plugins" / "musescore-mcp-websocket.qml"
    text = plugin.read_text(encoding="utf-8")
    assert 'case "save":' in text
    assert 'cmd("file-save")' in text
    assert 'case "getCapabilities":' in text
    assert '"getCapabilities", "getScore"' in text
    assert 'case "createScore":' in text
    assert 'case "openScore":' in text
    assert 'case "saveAs":' in text
    assert 'createScore is not verified for MuseScore 4.7.4' in text
    assert 'openScore is not verified for MuseScore 4.7.4' in text
    assert 'saveAs is not verified for MuseScore 4.7.4' in text
    assert 'setStaffMute is not implemented' in text
    assert 'setInstrumentSound is not implemented' in text
    assert 'case "setStaffVisible":' in text
    assert 'reserved_commands: ["createScore", "openScore", "saveAs",' in text
