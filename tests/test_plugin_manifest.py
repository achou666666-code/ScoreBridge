from pathlib import Path


def test_bundled_plugin_exposes_save_command():
    plugin = Path(__file__).parents[1] / "plugins" / "musescore-mcp-websocket.qml"
    text = plugin.read_text(encoding="utf-8")
    assert 'case "save":' in text
    assert 'cmd("file-save")' in text
    assert 'case "getCapabilities":' in text
    assert 'case "getScoreIdentity":' in text
    assert 'curScore.metaTag("scorebridgeTargetId")' in text
    assert '"getCapabilities", "getScore"' in text
    assert 'case "createScore":' in text
    assert 'case "openScore":' in text
    assert 'case "saveAs":' in text
    assert 'createScore is not verified for MuseScore 4.7.4' in text
    assert 'openScore is not verified for MuseScore 4.7.4' in text
    assert 'saveAs is not verified for MuseScore 4.7.4' in text
    assert 'setStaffMute is not implemented' in text
    assert 'setMidiPatch does not control MuseScore 4 audio resources' in text
    assert 'setInstrumentSound is not implemented' in text
    assert 'case "setStaffVisible":' in text
    assert 'case "getMidiChannels":' in text
    assert 'case "setPartInstrument":' in text
    assert 'curScore.replaceInstrument(curScore.parts[partIndex], instrumentId)' in text
    assert 'case "setKeySignature":' in text
    assert 'case "addDynamic":' in text
    assert 'case "addChord":' in text
    assert 'case "addTie":' in text
    assert 'case "addRest":' in text
    assert 'case "addTuplet":' in text
    assert 'case "addGraceNote":' in text
    assert 'case "addArticulation":' in text
    assert 'case "addSlur":' in text
    assert 'staccato: "add-staccato"' in text
    assert 'cmd("add-slur")' in text
    assert 'case "addTechniqueText":' in text
    assert 'newElement(Element.STAFF_TEXT)' in text
    assert 'reserved_commands: ["createScore", "openScore", "saveAs",' in text
    sequence_block = text.split('function processSequence(params)', 1)[1].split('try {', 1)[0]
    assert '"createScore"' not in sequence_block
    assert '"openScore"' not in sequence_block
    assert '"saveAs"' not in sequence_block
    assert '"setKeySignature"' in sequence_block
    assert '"addDynamic"' in sequence_block
    assert '"addArticulation"' in sequence_block
    assert '"addSlur"' in sequence_block
    assert '"addTechniqueText"' in sequence_block
    assert '"setPartInstrument"' in sequence_block
    assert '"setMidiPatch"' not in sequence_block
    assert '"addChord"' in sequence_block
    assert '"addTie"' in sequence_block
    assert '"addRest"' in sequence_block
    assert '"addTuplet"' in sequence_block
    assert '"addGraceNote"' in sequence_block
