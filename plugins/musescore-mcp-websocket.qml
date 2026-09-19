import QtQuick 2.9
import MuseScore 3.0

MuseScore {
    id: root
    menuPath: "Plugins.MuseScore API Server"
    description: "Exposes MuseScore API via WebSocket (Clean Version)"
    version: "2.7"
    
    property var clientConnections: []
    property var selectionState: ({
        startStaff: 0,
        endStaff: 1,
        startTick: 0,
        elements: []
    })

    // ========================================
    // WEBSOCKET & MESSAGE PROCESSING
    // ========================================

    function processMessage(message, clientId) {
        console.log("Received message: " + message);
        try {
            var command = JSON.parse(message);
            var result = processCommand(command);
            api.websocketserver.send(clientId, JSON.stringify({
                status: "success",
                result: result
            }));
        } catch (e) {
            console.log("Error processing command: " + e.toString());
            api.websocketserver.send(clientId, JSON.stringify({
                status: "error",
                message: e.toString()
            }));
        }
    }

    function processCommand(command) {
        console.log("Processing command: " + command.action);
        
        switch(command.action) {
            // Core operations
            case "getScore":                return getScore(command.params);
            case "getCapabilities":         return getCapabilities();
            case "createScore":             return createScore(command.params);
            case "openScore":               return openScore(command.params);
            case "saveAs":                  return saveScoreAs(command.params);
            case "syncStateToSelection":    return syncStateToSelection();
            case "ping":                    return "pong";
            case "undo":                    return undo();
            case "goToBeginningOfScore":    return goToBeginningOfScore();
            case "processSequence":         return processSequence(command.params);
            case "save":                     return saveScore();

            // Navigation
            case "getCursorInfo":           return getCursorInfo(command.params);
            case "goToMeasure":             return goToMeasure(command.params);
            case "goToFinalMeasure":        return goToFinalMeasure(command.params);
            case "nextElement":             return nextElement(command.params);
            case "prevElement":             return prevElement(command.params);
            case "nextStaff":               return nextStaff(command.params);
            case "prevStaff":               return prevStaff(command.params);

            // Selection
            case "selectCurrentMeasure":    return selectCurrentMeasure(command.params);
            case "selectCustomRange":       return selectCustomRange(command.params);

            // Notes & Music
            case "addNote":                 return addNote(command.params);
            case "addChord":                return addChord(command.params);
            case "addTie":                  return addTie(command.params);
            case "addRest":                 return addRest(command.params);
            case "addTuplet":               return addTuplet(command.params);
            case "addLyrics":               return addLyrics(command.params);
            case "addDynamic":              return addDynamic(command.params);
            case "addArticulation":         return addArticulation(command.params);
            case "addSlur":                 return addSlur(command.params);
            case "addTechniqueText":        return addTechniqueText(command.params);

            // Measures
            case "appendMeasure":           return appendMeasure(command.params);
            case "insertMeasure":           return insertMeasure(command.params);
            case "deleteSelection":         return deleteSelection(command.params);

            // Staff & Instruments
            case "addInstrument":           return addInstrument(command.params);
            case "setStaffMute":            return setStaffMute(command.params);
            case "setStaffVisible":         return setStaffVisible(command.params);
            case "getMidiChannels":         return getMidiChannels(command.params);
            case "setMidiPatch":            return setMidiPatch(command.params);
            case "setPartInstrument":       return setPartInstrument(command.params);
            case "setInstrumentSound":      return setInstrumentSound(command.params);
            case "getPageLayout":           return getPageLayout();
            case "setPageLayout":           return setPageLayout(command.params);
            case "setLayoutBreak":          return setLayoutBreak(command.params);
            case "setKeySignature":         return setKeySignature(command.params);
            case "setTimeSignature":        return setTimeSignature(command.params);
            case "setTempo":                return setTempo(command.params);

            default:
                throw new Error("Unknown command: " + command.action);
        }
    }

    // ========================================
    // UTILITY FUNCTIONS
    // ========================================

    function validateParams(params, required) {
        if (!params) return { error: "Missing required parameters: " + required.join(", ") };
        var missing = [];
        for (var i = 0; i < required.length; i++) {
            if (params[required[i]] === undefined) {
                missing.push(required[i]);
            }
        }
        return missing.length > 0 ? { error: "Missing required parameters: " + missing.join(", ") } : { valid: true };
    }

    function executeWithUndo(operation) {
        if (!curScore) return { error: "No score open" };
        
        curScore.startCmd();
        try {
            var result = operation();
            curScore.endCmd();
            return result;
        } catch (e) {
            curScore.endCmd(true);
            return { error: e.toString() };
        }
    }

    function getNoteName(note) {
        const noteNames = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];
        return noteNames[note % 12];
    }

    function getTpcName(tpc) {
        if (tpc === -1) return "Fbb";
        var tpcNames = [
            "Cbb", "Gbb", "Dbb", "Abb", "Ebb", "Bbb", "Fb",
            "Cb",  "Gb",  "Db",  "Ab",  "Eb",  "Bb",  "F",
            "C",   "G",   "D",   "A",   "E",   "B",   "F#",
            "C#",  "G#",  "D#",  "A#",  "E#",  "B#",  "F##",
            "C##", "G##", "D##", "A##", "E##", "B##", "F###"
        ];
        if (tpc >= 0 && tpc < tpcNames.length) {
            return tpcNames[tpc];
        }
        return "Unknown";
    }

    function getDurationName(duration) {
        const durationNames = ["LONG","BREVE","WHOLE","HALF","QUARTER","EIGHTH","16TH","32ND","64TH","128TH","256TH","512TH","1024TH","ZERO","MEASURE","INVALID"];
        return durationNames[duration] || "UNKNOWN";
    }

    // ========================================
    // CURSOR MANAGEMENT
    // ========================================

    function createCursor(params) {
        if (!curScore) throw new Error("No score open");
        
        if (!params || Object.keys(params).length === 0) {
            params = selectionState;
        }
        
        var cursor = curScore.newCursor();
        cursor.inputStateMode = Cursor.INPUT_STATE_SYNC_WITH_SCORE;
        
        // Set track
        if (params.startStaff !== undefined) cursor.staffIdx = params.startStaff;
        if (params.voice !== undefined) cursor.voice = params.voice;
        
        // Position cursor
        if (params.rewindMode !== undefined) {
            cursor.rewind(params.rewindMode);
        } else if (params.startTick !== undefined) {
            try {
                cursor.rewindToTick(params.startTick);
            } catch (e) {
                console.log("rewindToTick failed, using manual navigation");
                cursor.rewind(0);
                while (cursor.tick < params.startTick && cursor.next()) {}
            }
        } else if (params.measure !== undefined) {
            cursor.rewind(0);
            for (var i = 0; i < params.measure && cursor.nextMeasure(); i++) {}
        } else {
            cursor.rewind(0);
        }
        
        // Set duration
        if (params.duration) {
            cursor.setDuration(params.duration.numerator || 1, params.duration.denominator || 4);
        }
        
        return cursor;
    }

    function initCursorState() {
        if (!curScore) return "No score open";
        
        return executeWithUndo(function() {
            var cursor = curScore.newCursor();
            cursor.rewind(0);

            var startTick = cursor.tick;
            cursor.next();
            var endTick = cursor.tick;
            var element = cursor.element;

            selectionState = {
                startStaff: cursor.staffIdx,
                endStaff: cursor.staffIdx + 1,
                startTick: startTick,
                elements: element ? [processElement(element)] : []
            };
            
            curScore.selection.clear();
            curScore.selection.selectRange(startTick, endTick, 0, 0);
            
            return "Initialized at " + [startTick, endTick, 0, 0].join(',');
        });
    }

    // ========================================
    // ELEMENT PROCESSING
    // ========================================

    function processElement(element) {
        if (!element) return null;
        if (element.name !== "Chord" && element.name !== "Rest") return null;

        var base = {
            name: element.name,
            durationTicks: element.actualDuration ? element.actualDuration.ticks : 0,
            isTie: element.tieForward ? true : false,
            isTuplet: element.tuplet ? true : false
        };

        if (element.lyrics && element.lyrics.length > 0) {
            base.lyrics = [];
            for (var l = 0; l < element.lyrics.length; l++) {
                var lyr = element.lyrics[l];
                if (lyr) {
                    base.lyrics.push({
                        text: lyr.text,
                        no: lyr.no,
                        syllabic: lyr.syllabic
                    });
                }
            }
        }

        if (element.name === "Chord") {
            base.notes = [];
            var notesObj = element.notes || {};
            var keys = Object.keys(notesObj);
            for (var k = 0; k < keys.length; k++) {
                var note = notesObj[keys[k]];
                base.notes.push({
                    pitchMidi: note.pitch,
                    tpc: note.tpc,
                    pitchName: getTpcName(note.tpc)
                });
            }
        }
                
        return base;
    }

    // ========================================
    // CORE OPERATIONS
    // ========================================

    function undo() {
        return executeWithUndo(function() {
            cmd("undo");
            return { success: true, message: "Undo successful" };
        });
    }

    function saveScore() {
        if (!curScore) return { error: "No score open" };
        try {
            cmd("file-save");
            return { success: true, message: "Current score saved" };
        } catch (e) {
            return { error: e.toString() };
        }
    }

    function createScore(params) {
        return { error: "createScore is not verified for MuseScore 4.7.4; open a score first" };
    }

    function openScore(params) {
        var validation = validateParams(params, ["path"]);
        if (!validation.valid) return validation;
        return { error: "openScore is not verified for MuseScore 4.7.4; open the file in MuseScore first" };
    }

    function saveScoreAs(params) {
        var validation = validateParams(params, ["path"]);
        if (!validation.valid) return validation;
        return { error: "saveAs is not verified for MuseScore 4.7.4; use save on the open score" };
    }

    function getCapabilities() {
        return {
            pluginVersion: version,
            commands: [
                "ping", "getCapabilities", "getScore", "save", "undo",
                "goToBeginningOfScore", "getCursorInfo", "goToMeasure",
                "goToFinalMeasure", "nextElement", "prevElement",
                "nextStaff", "prevStaff", "selectCurrentMeasure",
                "selectCustomRange", "processSequence", "addNote", "addChord", "addTie",
                "addRest", "addTuplet", "addLyrics", "appendMeasure",
                "insertMeasure", "deleteSelection", "addInstrument",
                "getMidiChannels", "setPartInstrument",
                "getPageLayout", "setPageLayout", "setLayoutBreak",
                "setKeySignature", "setTimeSignature", "setTempo", "setStaffVisible",
                "addDynamic", "addTechniqueText", "addArticulation", "addSlur"
            ],
            reserved_commands: ["createScore", "openScore", "saveAs",
                                "setStaffMute", "setMidiPatch", "setInstrumentSound"]
        };
    }

    function goToBeginningOfScore() {
        var response = initCursorState();
        return { 
            success: true, 
            message: response, 
            currentSelection: selectionState,
            currentScore: getScoreSummary()
        };
    }

    function processSequence(params) {
        if (!curScore) return { error: "No score open" };
        if (!params || !Array.isArray(params.sequence)) return { error: "Sequence must be an array" };

        var validCommands = [
            "getCapabilities", "getScore",
            "addNote", "addChord", "addTie", "addRest", "addTuplet", "appendMeasure", "deleteSelection",
            "getCursorInfo", "goToMeasure", "nextElement", "prevElement", "nextStaff", "prevStaff", "save",
            "selectCurrentMeasure", "processSequence", "insertMeasure", "goToFinalMeasure",
            "getMidiChannels", "setPartInstrument",
            "getPageLayout", "setPageLayout", "setLayoutBreak",
            "goToBeginningOfScore", "setKeySignature", "setTimeSignature", "addLyrics", "addInstrument",
            "setStaffVisible", "setTempo", "selectCustomRange", "addDynamic", "addTechniqueText", "addArticulation", "addSlur"
        ];

        var completed = [];
        var i = 0;
        try {
            for (i = 0; i < params.sequence.length; i++) {
                var command = params.sequence[i];
                if (!command || !validCommands.includes(command.action)) {
                    throw new Error("Invalid command at index " + i);
                }
                var result = processCommand(command);
                if (result && (result.error || result.success === false || result.valid === false)) {
                    return { error: result.error || "Command failed", failedIndex: i,
                             completedIndices: completed, result: result };
                }
                completed.push(i);
            }
            return { success: true, completedIndices: completed, message: "Sequence processed", currentSelection: selectionState };
        } catch (e) {
            return { error: e.toString(), failedIndex: i, completedIndices: completed };
        }
    }

    // ========================================
    // NAVIGATION FUNCTIONS
    // ========================================

    function syncStateToSelection() {
        if (!curScore) return { error: "No score open" };

        try {
            var selection = curScore.selection;
            var startSegment = selection.startSegment;
            var endSegment = selection.endSegment;

            if (startSegment && endSegment) {
                var cursor = createCursor({
                    startTick: startSegment.tick,
                    startStaff: selection.startStaff    
                });

                var elementsMap = {};
                for (var st = selection.startStaff; st < selection.endStaff; st++) {
                    elementsMap[`staff${st}`] = [];
                }

                var currentSegment = startSegment;
                while (currentSegment && currentSegment.tick < endSegment.tick) {
                    for (var s = selection.startStaff; s < selection.endStaff; s++) {
                        for (var v = 0; v < 4; v++) {
                            var track = s * 4 + v;
                            var el = currentSegment.elementAt(track);
                            if (el) {
                                var processed = processElement(el);
                                if (processed) {
                                    processed.voice = v;
                                    processed.startTick = currentSegment.tick;
                                    elementsMap[`staff${s}`].push(processed);
                                }
                            }
                        }
                    }
                    currentSegment = currentSegment.next;
                }

                selectionState = {
                    startStaff: selection.startStaff,
                    endStaff: selection.endStaff,
                    startTick: startSegment.tick,
                    elements: elementsMap,
                    totalDuration: endSegment.tick - startSegment.tick
                };
            } else {
                var c = createCursor();
                if (c && c.element) {
                    var elElement = processElement(c.element);
                    elElement.startTick = c.tick;
                    var sStart = selection.startStaff || 0;
                    var singleMap = {};
                    singleMap[`staff${sStart}`] = [elElement];
                    
                    selectionState = {
                        startStaff: sStart,
                        endStaff: sStart + 1,
                        startTick: c.tick,
                        elements: singleMap,
                        totalDuration: elElement.durationTicks
                    };
                } else {
                    return { error: "No valid selection or cursor elements found" };
                }
            }

            return { success: true, currentSelection: selectionState };
        } catch (e) {
            return { success: false, error: e.toString() };
        }
    }

    function getCursorInfo(params) {
        if (!curScore) return { error: "No score open" };
        
        syncStateToSelection();
        return { 
            success: true, 
            currentSelection: selectionState, 
            currentScore: params && params.verbose !== "false" ? getScoreSummary() : null
        };
    }

    function goToMeasure(params) {
        var validation = validateParams(params, ["measure"]);
        if (!validation.valid) return validation;

        return executeWithUndo(function() {
            var score = getScoreSummary();
            if (params.measure < 1 || params.measure > score.measures.length) {
                return { error: "Invalid measure number" };
            }
            var measureIdx = params.measure - 1;
            var measure = score.measures[measureIdx];
            var startTick = measure.startTick;
            
            var endTick = (measureIdx + 1 < score.measures.length) ? score.measures[measureIdx + 1].startTick : curScore.lastSegment.tick;
            
            curScore.selection.clear();
            curScore.selection.selectRange(startTick, endTick, 0, curScore.nstaves);
            
            var res = syncStateToSelection();
            if (res.error) return res;
            
            return { success: true, currentSelection: selectionState };
        });
    }

    function nextElement(params) {
        return executeWithUndo(function() {
            syncStateToSelection();
            
            var cursor = createCursor({ 
                startTick: selectionState.startTick, 
                startStaff: selectionState.startStaff 
            });

            var numElements = params && params.numElements || 1;
            var success = true;
            for (var i = 0; i < numElements && success; i++) {
                success = cursor.next();
            }
            
            if (success) {
                var element = processElement(cursor.element);
                var startTick = cursor.tick;
                var staffIdx = cursor.staffIdx;
                
                // Check if we need to append a measure
                if (startTick + element.durationTicks >= curScore.lastSegment.tick) {
                    cmd("append-measure");
                }

                curScore.selection.clear();
                curScore.selection.selectRange(startTick, startTick + element.durationTicks, staffIdx, staffIdx + 1);

                selectionState = {
                    startStaff: staffIdx,
                    endStaff: staffIdx + 1,
                    startTick: startTick,
                    elements: [element],
                    totalDuration: element.durationTicks
                };
                
                return { success: true, currentSelection: selectionState };
            } else {
                return { success: false, message: "End of score reached" };
            }
        });
    }

    function prevElement(params) {
        return executeWithUndo(function() {
            syncStateToSelection();
            
            var cursor = createCursor({ 
                startTick: selectionState.startTick, 
                startStaff: selectionState.startStaff 
            });

            var endTick = cursor.tick;
            var numElements = params && params.numElements || 1;
            var success = true;
            
            for (var i = 0; i < numElements && success; i++) {
                success = cursor.prev();
            }

            if (success) {
                var element = processElement(cursor.element);
                var startTick = cursor.tick;
                var staffIdx = cursor.staffIdx;
                
                curScore.selection.clear();
                curScore.selection.selectRange(startTick, endTick, staffIdx, staffIdx + 1);

                selectionState = {
                    startStaff: staffIdx,
                    endStaff: staffIdx + 1,
                    startTick: startTick,
                    elements: [element],
                    totalDuration: endTick - startTick
                };
                
                return { success: true, currentSelection: selectionState };
            } else {
                return { success: false, message: "Beginning of score reached" };
            }
        });
    }

    function nextStaff(params) {
        return executeWithUndo(function() {
            syncStateToSelection();

            if (selectionState.endStaff >= curScore.nstaves) {
                return { success: false, message: "Already at last staff" };
            }

            var newStaff = selectionState.endStaff;
            var cursor = createCursor({ 
                startTick: selectionState.startTick, 
                startStaff: newStaff 
            });

            var element = processElement(cursor.element);
            
            curScore.selection.clear();
            curScore.selection.selectRange(
                selectionState.startTick, 
                selectionState.startTick + element.durationTicks, 
                newStaff, 
                newStaff + 1
            );

            selectionState = {
                startStaff: newStaff,
                endStaff: newStaff + 1,
                startTick: selectionState.startTick,
                elements: [element],
                totalDuration: element.durationTicks
            };

            return { success: true, currentSelection: selectionState };
        });
    }

    function prevStaff(params) {
        return executeWithUndo(function() {
            syncStateToSelection();

            if (selectionState.startStaff <= 0) {
                return { success: false, message: "Already at first staff" };
            }

            var newStaff = selectionState.startStaff - 1;
            var cursor = createCursor({ 
                startTick: selectionState.startTick, 
                startStaff: newStaff 
            });

            var element = processElement(cursor.element);
            
            curScore.selection.clear();
            curScore.selection.selectRange(
                selectionState.startTick, 
                selectionState.startTick + element.durationTicks, 
                newStaff, 
                newStaff + 1
            );

            selectionState = {
                startStaff: newStaff,
                endStaff: newStaff + 1,
                startTick: selectionState.startTick,
                elements: [element],
                totalDuration: element.durationTicks
            };

            return { success: true, currentSelection: selectionState };
        });
    }

    function goToFinalMeasure(params) {
        return executeWithUndo(function() {
            var cursor = createCursor({ startTick: 0 });
            var count = 0;
            var startTick = 0;

            while (cursor.nextMeasure()) {
                startTick = cursor.tick;
                count++;
            }

            if (count === 0) {
                return { success: false, message: "Already at the last measure" };
            }

            cursor.rewindToTick(startTick);
            cursor.next();
            var endTick = cursor.tick;
            var staffIdx = cursor.staffIdx;
            
            curScore.selection.clear();
            curScore.selection.selectRange(startTick, endTick, staffIdx, staffIdx + 1);
            
            selectionState = {
                startStaff: staffIdx,
                endStaff: staffIdx + 1,
                startTick: startTick,
                elements: [processElement(cursor.element)],
                totalDuration: endTick - startTick
            };

            return { success: true, currentSelection: selectionState };
        });
    }

    // ========================================
    // SELECTION FUNCTIONS
    // ========================================

    function selectCurrentMeasure() {
        return executeWithUndo(function() {
            var cursor = createCursor({ 
                startTick: selectionState.startTick || 0, 
                startStaff: selectionState.startStaff || 0 
            });

            var currTick = cursor.tick;
            var scoreSummary = getScoreSummary();

            var measureIdx = scoreSummary.measures.filter(function(m) { 
                return m.startTick <= currTick; 
            }).length - 1;
            
            if (measureIdx < 0) return { error: "Invalid cursor position" };
            
            var measure = scoreSummary.measures[measureIdx];
            var startTick = measure.startTick;
            var endTick = (measureIdx + 1 < scoreSummary.measures.length) ? scoreSummary.measures[measureIdx + 1].startTick : curScore.lastSegment.tick;

            curScore.selection.clear();
            curScore.selection.selectRange(startTick, endTick, 0, curScore.nstaves);

            var res = syncStateToSelection();
            if (res.error) return res;
            
            return { success: true, message: `Selected measure ${measureIdx + 1}`, currentSelection: selectionState };
        });
    }

    function selectCustomRange(params) {
        var validation = validateParams(params, ["startTick", "endTick", "startStaff", "endStaff"]);
        if (!validation.valid) return validation;

        return executeWithUndo(function() {
            var startTick = params.startTick;
            var endTick = params.endTick;
            var startStaff = params.startStaff;
            var endStaff = params.endStaff;

            // Visual GUI snap
            curScore.selection.clear();
            curScore.selection.selectRange(startTick, endTick, startStaff, endStaff);

            var elementsMap = {};
            for (var st = startStaff; st < endStaff; st++) {
                elementsMap[`staff${st}`] = [];
            }

            var c = createCursor({ startTick: 0, startStaff: startStaff });
            c.rewind(0);
            var currentSegment = c.segment;

            while (currentSegment && currentSegment.tick < startTick) {
                currentSegment = currentSegment.next;
            }

            while (currentSegment && currentSegment.tick < endTick) {
                for (var s = startStaff; s < endStaff; s++) {
                    for (var v = 0; v < 4; v++) {
                        var track = s * 4 + v;
                        var el = currentSegment.elementAt(track);
                        if (el) {
                            var processed = processElement(el);
                            if (processed) {
                                processed.voice = v;
                                processed.startTick = currentSegment.tick;
                                elementsMap[`staff${s}`].push(processed);
                            }
                        }
                    }
                }
                currentSegment = currentSegment.next;
            }

            selectionState = {
                startStaff: startStaff,
                endStaff: endStaff,
                startTick: startTick,
                elements: elementsMap,
                totalDuration: endTick - startTick
            };

            return { success: true, message: "Custom range mapped", currentSelection: selectionState };
        });
    }

    // ========================================
    // NOTE & MUSIC OPERATIONS
    // ========================================

    function addNote(params) {
        var validation = validateParams(params, ["pitch", "duration"]);
        if (!validation.valid) return validation;

        if (!params.duration.numerator || !params.duration.denominator) {
            return { error: "Duration must be specified as { numerator: int, denominator: int }" };
        }

        return executeWithUndo(function() {
            syncStateToSelection();
            
            var cursorParams = {};
            if (params.staff !== undefined) cursorParams.startStaff = params.staff;
            if (params.startTick !== undefined) cursorParams.startTick = params.startTick;
            if (params.voice !== undefined) cursorParams.voice = params.voice;
            var cursor = createCursor(cursorParams);
            cursor.setDuration(params.duration.numerator, params.duration.denominator);
            
            // Melody is the default. Pass addToChord: true to stack a pitch on the current chord.
            cursor.addNote(params.pitch, params.addToChord === true);
            cursor.rewindToTick(selectionState.startTick);

            if (params.advanceCursorAfterAction) {
                cursor.next();
            }

            var element = processElement(cursor.element);
            var startTick = cursor.tick;
            var staffIdx = cursor.staffIdx;
            var durationTicks = element && element.durationTicks ? element.durationTicks : 0;

            curScore.selection.clear();
            if (durationTicks > 0) {
                curScore.selection.selectRange(startTick, startTick + durationTicks, staffIdx, staffIdx + 1);
            }

            var syncRes = syncStateToSelection();
            if (syncRes && syncRes.error) {
                var staffMap = {};
                staffMap["staff" + staffIdx] = element ? [element] : [];
                selectionState = {
                    startStaff: staffIdx,
                    endStaff: staffIdx + 1,
                    startTick: startTick,
                    elements: staffMap,
                    totalDuration: durationTicks
                };
            }

            return { 
                success: true, 
                message: "Note added with pitch " + params.pitch,
                currentSelection: selectionState
            };
        });
    }

    function addChord(params) {
        if (!curScore) return { error: "No score open" };
        if (!params || !Array.isArray(params.pitches) || params.pitches.length === 0)
            return { error: "pitches must be a nonempty array of MIDI pitches" };
        if (!params.duration || !Number.isInteger(params.duration.numerator) ||
            !Number.isInteger(params.duration.denominator) || params.duration.numerator <= 0 ||
            params.duration.denominator <= 0)
            return { error: "duration must contain positive integer numerator and denominator" };
        var staff = params.staff === undefined ? selectionState.startStaff : params.staff;
        var voice = params.voice === undefined ? 0 : params.voice;
        var startTick = params.startTick === undefined ? selectionState.startTick : params.startTick;
        if (!Number.isInteger(staff) || staff < 0 || staff >= curScore.nstaves)
            return { error: "staff must be a valid zero-based staff index" };
        if (!Number.isInteger(voice) || voice < 0 || voice > 3)
            return { error: "voice must be an integer from 0 to 3" };
        if (!Number.isInteger(startTick) || startTick < 0)
            return { error: "startTick must be a nonnegative integer" };
        var seen = {};
        for (var i = 0; i < params.pitches.length; i++) {
            var pitch = params.pitches[i];
            if (!Number.isInteger(pitch) || pitch < 0 || pitch > 127)
                return { error: "Every pitch must be an integer from 0 to 127" };
            if (seen[pitch]) return { error: "Duplicate pitches are not allowed in a chord" };
            seen[pitch] = true;
        }
        if (params.tpcs !== undefined) {
            if (!Array.isArray(params.tpcs) || params.tpcs.length !== params.pitches.length)
                return { error: "tpcs must be an array matching pitches" };
            if (curScore.style.value("concertPitch"))
                return { error: "Written TPC input requires the score's concert pitch display to be off" };
            for (var j = 0; j < params.tpcs.length; j++) {
                if (!Number.isInteger(params.tpcs[j]) || params.tpcs[j] < -1 || params.tpcs[j] > 35)
                    return { error: "Every TPC must be an integer from -1 to 35" };
            }
        }
        return executeWithUndo(function() {
            // Locate on the staff before switching voice. An empty secondary voice has
            // no chord/rest segment for rewindToTick() to find until MuseScore expands it.
            var cursor = createCursor({startStaff: staff, startTick: startTick});
            if (cursor.tick !== startTick)
                throw new Error("No score position exists at startTick " + startTick);
            cursor.voice = voice;
            cursor.setDuration(params.duration.numerator, params.duration.denominator);
            for (var p = 0; p < params.pitches.length; p++) {
                if (p > 0) cursor.rewindToTick(startTick);
                cursor.addNote(params.pitches[p], p > 0);
            }
            cursor.rewindToTick(startTick);
            var chord = cursor.element;
            if (!chord || chord.type !== Element.CHORD)
                throw new Error("MuseScore did not create a chord at the requested position");
            var written = [];
            for (var q = 0; q < params.pitches.length; q++) {
                var matched = null;
                for (var n = 0; n < chord.notes.length; n++) {
                    if (chord.notes[n].pitch === params.pitches[q]) { matched = chord.notes[n]; break; }
                }
                if (!matched) throw new Error("MuseScore did not retain pitch " + params.pitches[q]);
                if (params.tpcs !== undefined) {
                    matched.tpc = params.tpcs[q];
                    if (matched.tpc !== params.tpcs[q])
                        throw new Error("MuseScore did not retain TPC " + params.tpcs[q]);
                }
                written.push({pitch: matched.pitch, tpc: matched.tpc});
            }
            var durationTicks = chord.actualDuration ? chord.actualDuration.ticks : 0;
            if (durationTicks <= 0) throw new Error("MuseScore created a zero-duration chord");
            curScore.selection.clear();
            curScore.selection.selectRange(startTick, startTick + durationTicks, staff, staff + 1);
            selectionState = {startStaff: staff, endStaff: staff + 1, startTick: startTick,
                              elements: [processElement(chord)], totalDuration: durationTicks};
            return {success: true, changed: true, staff: staff, voice: voice,
                    startTick: startTick, durationTicks: durationTicks, notes: written,
                    currentSelection: selectionState};
        });
    }

    function addTie(params) {
        if (!curScore) return { error: "No score open" };
        if (!params || !Number.isInteger(params.staff) || params.staff < 0 || params.staff >= curScore.nstaves)
            return { error: "staff must be a valid zero-based staff index" };
        if (!Number.isInteger(params.voice) || params.voice < 0 || params.voice > 3)
            return { error: "voice must be an integer from 0 to 3" };
        if (!Number.isInteger(params.startTick) || params.startTick < 0)
            return { error: "startTick must be a nonnegative integer" };
        if (!Number.isInteger(params.pitch) || params.pitch < 0 || params.pitch > 127)
            return { error: "pitch must be an integer from 0 to 127" };
        return executeWithUndo(function() {
            var cursor = createCursor({startStaff: params.staff, voice: params.voice, startTick: params.startTick});
            if (cursor.tick !== params.startTick || !cursor.element || cursor.element.type !== Element.CHORD)
                throw new Error("No source chord exists at the requested position");
            var source = null;
            for (var i = 0; i < cursor.element.notes.length; i++) {
                if (cursor.element.notes[i].pitch === params.pitch) { source = cursor.element.notes[i]; break; }
            }
            if (!source) throw new Error("Source chord does not contain pitch " + params.pitch);
            if (source.tieForward)
                return {success: true, changed: false, staff: params.staff, voice: params.voice,
                        startTick: params.startTick, pitch: params.pitch};
            if (!cursor.next() || !cursor.element || cursor.element.type !== Element.CHORD)
                throw new Error("The next event in this voice is not a chord");
            var targetTick = cursor.tick;
            var targetFound = false;
            for (var j = 0; j < cursor.element.notes.length; j++) {
                if (cursor.element.notes[j].pitch === params.pitch) { targetFound = true; break; }
            }
            if (!targetFound) throw new Error("The next chord does not contain matching pitch " + params.pitch);
            curScore.selection.clear();
            curScore.selection.select(source, false);
            cmd("tie");
            var verify = createCursor({startStaff: params.staff, voice: params.voice, startTick: params.startTick});
            var tied = null;
            for (var k = 0; verify.element && k < verify.element.notes.length; k++) {
                if (verify.element.notes[k].pitch === params.pitch) { tied = verify.element.notes[k]; break; }
            }
            if (!tied || !tied.tieForward || !tied.tieForward.endNote ||
                tied.tieForward.endNote.pitch !== params.pitch)
                throw new Error("MuseScore did not create the requested tie");
            return {success: true, changed: true, staff: params.staff, voice: params.voice,
                    startTick: params.startTick, endTick: targetTick, pitch: params.pitch};
        });
    }

    function addRest(params) {
        if (!curScore) return { error: "No score open" };
        params = params || {};
        var staff = params.staff !== undefined ? params.staff : selectionState.startStaff;
        var voice = params.voice !== undefined ? params.voice : 0;
        var startTick = params.startTick !== undefined ? params.startTick : selectionState.startTick;
        if (!Number.isInteger(staff) || staff < 0 || staff >= curScore.nstaves)
            return { error: "staff must be a valid zero-based staff index" };
        if (!Number.isInteger(voice) || voice < 0 || voice > 3)
            return { error: "voice must be an integer from 0 to 3" };
        if (!Number.isInteger(startTick) || startTick < 0)
            return { error: "startTick must be a nonnegative integer" };
        if (!params.duration || !Number.isInteger(params.duration.numerator) ||
            !Number.isInteger(params.duration.denominator) || params.duration.numerator <= 0 ||
            params.duration.denominator <= 0)
            return { error: "duration must contain positive integer numerator and denominator" };
        return executeWithUndo(function() {
            // Find the rhythmic position before selecting the voice. This also
            // lets MuseScore expand an empty secondary voice when addRest runs.
            var cursor = createCursor({startStaff: staff, startTick: startTick});
            if (cursor.tick !== startTick)
                throw new Error("No score position exists at startTick " + startTick);
            cursor.voice = voice;
            cursor.setDuration(params.duration.numerator, params.duration.denominator);
            cursor.addRest();
            cursor.rewindToTick(startTick);
            if (!cursor.element || cursor.element.type !== Element.REST)
                throw new Error("MuseScore did not create a rest at the requested position");
            var durationTicks = cursor.element.actualDuration ? cursor.element.actualDuration.ticks : 0;
            if (durationTicks <= 0) throw new Error("MuseScore created a zero-duration rest");
            curScore.selection.clear();
            curScore.selection.selectRange(startTick, startTick + durationTicks, staff, staff + 1);
            selectionState = {
                startStaff: staff,
                endStaff: staff + 1,
                startTick: startTick,
                elements: [processElement(cursor.element)],
                totalDuration: durationTicks
            };
            return {success: true, changed: true, staff: staff, voice: voice,
                    startTick: startTick, durationTicks: durationTicks,
                    currentSelection: selectionState};
        });
    }

    function addTuplet(params) {
        if (!curScore) return { error: "No score open" };
        params = params || {};
        if (!Number.isInteger(params.staff) || params.staff < 0 || params.staff >= curScore.nstaves)
            return { error: "staff must be a valid zero-based staff index" };
        if (!Number.isInteger(params.voice) || params.voice < 0 || params.voice > 3)
            return { error: "voice must be an integer from 0 to 3" };
        if (!Number.isInteger(params.startTick) || params.startTick < 0)
            return { error: "startTick must be a nonnegative integer" };
        if (!params.ratio || !Number.isInteger(params.ratio.numerator) ||
            !Number.isInteger(params.ratio.denominator) || params.ratio.numerator <= 0 ||
            params.ratio.denominator <= 0)
            return { error: "ratio must contain positive integer numerator and denominator" };
        if (!params.duration || !Number.isInteger(params.duration.numerator) ||
            !Number.isInteger(params.duration.denominator) || params.duration.numerator <= 0 ||
            params.duration.denominator <= 0)
            return { error: "duration must contain positive integer numerator and denominator" };
        return executeWithUndo(function() {
            var cursor = createCursor({startStaff: params.staff, startTick: params.startTick});
            if (cursor.tick !== params.startTick)
                throw new Error("No score position exists at startTick " + params.startTick);
            cursor.voice = params.voice;
            cursor.setDuration(params.duration.numerator, params.duration.denominator);
            var ratio = fraction(params.ratio.numerator, params.ratio.denominator);
            var duration = fraction(params.duration.numerator, params.duration.denominator);
            cursor.addTuplet(ratio, duration);
            cursor.rewindToTick(params.startTick);
            var element = cursor.element;
            if (!element || !element.tuplet)
                throw new Error("MuseScore did not create a tuplet at the requested position");
            if (element.tuplet.actualNotes !== params.ratio.numerator ||
                element.tuplet.normalNotes !== params.ratio.denominator)
                throw new Error("MuseScore created a different tuplet ratio");
            var tupletTicks = element.tuplet.actualDuration ? element.tuplet.actualDuration.ticks : 0;
            if (tupletTicks <= 0) throw new Error("MuseScore created a zero-duration tuplet");
            curScore.selection.clear();
            curScore.selection.selectRange(params.startTick, params.startTick + tupletTicks,
                                           params.staff, params.staff + 1);
            selectionState = {startStaff: params.staff, endStaff: params.staff + 1,
                              startTick: params.startTick, elements: [processElement(element)],
                              totalDuration: tupletTicks};
            return {success: true, changed: true, staff: params.staff, voice: params.voice,
                    startTick: params.startTick, durationTicks: tupletTicks,
                    ratio: {numerator: element.tuplet.actualNotes,
                            denominator: element.tuplet.normalNotes},
                    currentSelection: selectionState};
        });
    }

    function addLyrics(params) {
        if (!params.lyrics || !Array.isArray(params.lyrics) || params.lyrics.length === 0) {
            return { error: "Lyrics must be specified as an array of strings" };
        }
        
        return executeWithUndo(function() {
            syncStateToSelection();
            
            var cursor = createCursor({ 
                startTick: selectionState.startTick, 
                startStaff: selectionState.startStaff 
            });
            
            var lyricsArray = params.lyrics.slice();
            var verse = params.verse || 0;
            var addedCount = 0;
            var skippedCount = 0;
            
            while (cursor.element && lyricsArray.length > 0) {
                var element = cursor.element;
                
                if (element.type === Element.CHORD || element.name === "Chord") {
                    var lyr = newElement(Element.LYRICS);
                    lyr.text = lyricsArray.shift();
                    lyr.verse = verse;
                    
                    cursor.add(lyr);
                    addedCount++;
                } else if (element.type === Element.REST || element.name === "Rest") {
                    skippedCount++;
                }
                
                if (!cursor.next()) break;
            }
            
            var finalElement = processElement(cursor.element) || selectionState.elements[0];
            var finalTick = cursor.tick;
            var staffIdx = cursor.staffIdx;
            
            selectionState = {
                startStaff: staffIdx,
                endStaff: staffIdx + 1,
                startTick: finalTick,
                elements: [finalElement],
                totalDuration: finalElement.durationTicks || selectionState.totalDuration
            };
            
            curScore.selection.clear();
            curScore.selection.selectRange(finalTick, finalTick + (finalElement.durationTicks || 0), staffIdx, staffIdx + 1);
            
            var message = `Added ${addedCount} lyrics`;
            if (skippedCount > 0) message += `, skipped ${skippedCount} rests`;
            if (lyricsArray.length > 0) message += `, ${lyricsArray.length} lyrics remaining`;
            
            return { 
                success: true, 
                message: message,
                addedCount: addedCount,
                skippedCount: skippedCount,
                remainingLyrics: lyricsArray,
                currentSelection: selectionState
            };
        });
    }

    function addDynamic(params) {
        if (!params || typeof params.type !== "string") return { error: "Dynamic type must be a string" };
        var validation = validateParams(params, ["type"]);
        if (!validation.valid) return validation;
        var allowed = ["ppp", "pp", "p", "mp", "mf", "f", "ff", "fff", "sfz", "fp", "rfz"];
        if (allowed.indexOf(params.type) < 0) return { error: "Unsupported dynamic: " + params.type };
        return executeWithUndo(function() {
            syncStateToSelection();
            var cursor = createCursor({ startTick: selectionState.startTick, startStaff: selectionState.startStaff });
            var dynamic = newElement(Element.DYNAMIC);
            if (typeof DynamicType === "undefined" || DynamicType[params.type.toUpperCase()] === undefined) {
                throw new Error("Standard dynamic types require MuseScore 4.6 or later");
            }
            dynamic.dynamicType = DynamicType[params.type.toUpperCase()];
            var symbols = { p: "dynamicPiano", m: "dynamicMezzo", f: "dynamicForte",
                            s: "dynamicSforzando", r: "dynamicRinforzando", z: "dynamicZ" };
            var display = "";
            for (var j = 0; j < params.type.length; j++) {
                display += "<sym>" + symbols[params.type[j]] + "</sym>";
            }
            dynamic.text = display;
            cursor.add(dynamic);
            return { success: true, message: "Dynamic " + params.type + " added", currentSelection: selectionState };
        });
    }

    function validateNotationRange(minChords, singleVoice) {
        if (!curScore) return { error: "No score open" };
        var selection = curScore.selection;
        var start = selection.startSegment;
        var end = selection.endSegment;
        if (!start || !end || start.tick >= end.tick)
            return { error: "Select an explicit nonempty tick range before adding notation" };
        if (selection.endStaff !== selection.startStaff + 1)
            return { error: "Notation commands require a single-staff range" };
        var count = 0;
        var voices = {};
        for (var segment = start; segment && segment.tick < end.tick; segment = segment.next) {
            for (var voice = 0; voice < 4; voice++) {
                var element = segment.elementAt(selection.startStaff * 4 + voice);
                if (element && element.type === Element.CHORD) {
                    count++;
                    voices[voice] = true;
                }
            }
        }
        if (count < minChords) return { error: "Selected range requires at least " + minChords + " note/chord positions" };
        if (singleVoice && Object.keys(voices).length !== 1)
            return { error: "Slur range must contain notes in exactly one voice" };
        return { valid: true };
    }

    function addArticulation(params) {
        if (!params || typeof params.type !== "string") return { error: "Articulation type must be a string" };
        var validation = validateParams(params, ["type"]);
        if (!validation.valid) return validation;
        var actions = { staccato: "add-staccato", marcato: "add-marcato", tenuto: "add-tenuto" };
        if (!Object.prototype.hasOwnProperty.call(actions, params.type)) return { error: "Unsupported articulation: " + params.type };
        var range = validateNotationRange(1, false);
        if (!range.valid) return range;
        return executeWithUndo(function() {
            cmd(actions[params.type]);
            return { success: true, message: "Articulation " + params.type + " added", currentSelection: selectionState };
        });
    }

    function addSlur(params) {
        var range = validateNotationRange(2, true);
        if (!range.valid) return range;
        return executeWithUndo(function() {
            cmd("add-slur");
            return { success: true, message: "Slur added", currentSelection: selectionState };
        });
    }

    function addTechniqueText(params) {
        var validation = validateParams(params, ["text"]);
        if (!validation.valid) return validation;
        if (!String(params.text).trim()) return { error: "Technique text must not be empty" };
        return executeWithUndo(function() {
            syncStateToSelection();
            var cursor = createCursor({ startTick: selectionState.startTick, startStaff: selectionState.startStaff });
            var marking = newElement(Element.STAFF_TEXT);
            marking.text = params.text;
            cursor.add(marking);
            return { success: true, message: "Technique text added", currentSelection: selectionState };
        });
    }

    // ========================================
    // MEASURE OPERATIONS
    // ========================================

    function appendMeasure(params) {
        return executeWithUndo(function() {
            var count = params && params.count || 1;
            
            for (var i = 0; i < count; i++) {
                cmd("append-measure");
            }
            
            return { 
                success: true, 
                message: count + " measure(s) appended",
                currentSelection: selectionState
            };
        });
    }

    function insertMeasure(params) {
        return executeWithUndo(function() {
            cmd("insert-measure");
            syncStateToSelection();
            
            return { 
                success: true, 
                message: "Measure inserted",
                currentSelection: selectionState
            };
        });
    }

    function deleteSelection(params) {
        return executeWithUndo(function() {
            if (params && params.measure) {
                createCursor({ measure: params.measure });
            }
            
            cmd("delete");
            
            return { 
                success: true, 
                message: "Selection deleted",
                currentSelection: selectionState
            };
        });
    }

    // ========================================
    // STAFF & INSTRUMENT OPERATIONS
    // ========================================

    function addInstrument(params) {
        var validation = validateParams(params, ["instrumentId"]);
        if (!validation.valid) return validation;
        
        return executeWithUndo(function() {
            curScore.appendPart(params.instrumentId);
            return { success: true, message: "Instrument " + params.instrumentId + " added" };
        });
    }

    function setStaffMute(params) {
        return { error: "setStaffMute is not implemented; use setStaffVisible for engraving visibility" };
        /*
        var validation = validateParams(params, ["staff"]);
        if (!validation.valid) return validation;
        
        return executeWithUndo(function() {
            var staff = curScore.staves && curScore.staves[params.staff] || 
                       (typeof curScore.staff === "function" ? curScore.staff(params.staff) : null);
            
            if (staff) {
                staff.invisible = Boolean(params.mute);
                return { success: true, message: "Staff " + (params.mute ? "muted" : "unmuted") };
            } else {
                return { error: "Staff not found" };
            }
        });
        */
    }

    function setStaffVisible(params) {
        var validation = validateParams(params, ["staff", "visible"]);
        if (!validation.valid) return validation;
        return executeWithUndo(function() {
            var staff = curScore.staves && curScore.staves[params.staff] ||
                       (typeof curScore.staff === "function" ? curScore.staff(params.staff) : null);
            if (!staff) return { error: "Staff not found" };
            staff.invisible = !Boolean(params.visible);
            return { success: true, message: "Staff visibility updated" };
        });
    }

    function getMidiChannels(params) {
        if (!curScore) return { error: "No score open" };
        var tick = params && params.tick !== undefined ? params.tick : 0;
        if (!Number.isInteger(tick) || tick < 0) return { error: "tick must be a nonnegative integer" };
        var parts = [];
        for (var i = 0; i < curScore.parts.length; i++) {
            var instrument = curScore.parts[i].instrumentAtTick(tick);
            var channels = [];
            if (instrument) {
                for (var j = 0; j < instrument.channels.length; j++) {
                    var channel = instrument.channels[j];
                    channels.push({channel: j, name: channel.name,
                                   program: channel.midiProgram, bank: channel.midiBank});
                }
            }
            parts.push({part: i, instrumentId: instrument ? instrument.instrumentId : null,
                        name: instrument ? instrument.longName : null, channels: channels});
        }
        return { tick: tick, parts: parts, scope: "Notation MIDI channels; audio resource selection is separate" };
    }

    function setMidiPatch(params) {
        return { error: "setMidiPatch does not control MuseScore 4 audio resources; use setPartInstrument" };
    }

    function setPartInstrument(params) {
        if (!curScore) return { error: "No score open" };
        if (!params || !Number.isInteger(params.part) || params.part < 0 || params.part >= curScore.parts.length)
            return { error: "part must be a valid zero-based part index" };
        if (typeof params.instrumentId !== "string" || !params.instrumentId.trim())
            return { error: "instrumentId must be a nonempty MuseScore instrument ID" };
        var partIndex = params.part;
        var instrumentId = params.instrumentId.trim();
        var current = curScore.parts[partIndex].instrumentAtTick(0);
        var previousId = current ? current.instrumentId : null;
        if (previousId === instrumentId)
            return { success: true, changed: false, part: partIndex, instrumentId: instrumentId };
        return executeWithUndo(function() {
            curScore.replaceInstrument(curScore.parts[partIndex], instrumentId);
            var updated = curScore.parts[partIndex].instrumentAtTick(0);
            var actualId = updated ? updated.instrumentId : null;
            if (actualId !== instrumentId)
                throw new Error("Instrument replacement failed; unknown instrumentId: " + instrumentId);
            return { success: true, changed: true, part: partIndex,
                     previousInstrumentId: previousId, instrumentId: actualId,
                     scope: "MuseScore instrument template, notation defaults, and playback sound" };
        });
    }

    function setInstrumentSound(params) {
        return { error: "setInstrumentSound is not implemented for MuseScore 4.7.4" };
        /*
        var validation = validateParams(params, ["staff", "instrumentId"]);
        if (!validation.valid) return validation;
        
        return executeWithUndo(function() {
            cmd("instruments");
            return { success: true, message: "Instrument dialog opened, manual selection required" };
        });
        */
    }

    function getPageLayout() {
        if (!curScore) return { error: "No score open" };
        var style = curScore.style;
        return { widthMm: style.value("pageWidth") * 25.4,
                 heightMm: style.value("pageHeight") * 25.4,
                 printableWidthMm: style.value("pagePrintableWidth") * 25.4,
                 leftMm: style.value("pageOddLeftMargin") * 25.4,
                 rightMm: (style.value("pageWidth") - style.value("pagePrintableWidth") - style.value("pageOddLeftMargin")) * 25.4,
                 topMm: style.value("pageOddTopMargin") * 25.4,
                 bottomMm: style.value("pageOddBottomMargin") * 25.4,
                 evenLeftMm: style.value("pageEvenLeftMargin") * 25.4,
                 evenTopMm: style.value("pageEvenTopMargin") * 25.4,
                 evenBottomMm: style.value("pageEvenBottomMargin") * 25.4,
                 pageCount: curScore.npages };
    }

    function setPageLayout(params) {
        if (!curScore) return { error: "No score open" };
        var names = ["widthMm", "heightMm", "leftMm", "rightMm", "topMm", "bottomMm"];
        for (var i = 0; i < names.length; i++) {
            var value = params && params[names[i]];
            if (typeof value !== "number" || !isFinite(value) || value < 0)
                return { error: names[i] + " must be a finite nonnegative number in millimeters" };
        }
        if (params.widthMm <= params.leftMm + params.rightMm || params.heightMm <= params.topMm + params.bottomMm)
            return { error: "Page margins must leave a positive printable area" };
        return executeWithUndo(function() {
            var values = {pageWidth: params.widthMm, pageHeight: params.heightMm,
                pagePrintableWidth: params.widthMm - params.leftMm - params.rightMm,
                pageOddLeftMargin: params.leftMm, pageEvenLeftMargin: params.leftMm,
                pageOddTopMargin: params.topMm, pageEvenTopMargin: params.topMm,
                pageOddBottomMargin: params.bottomMm, pageEvenBottomMargin: params.bottomMm};
            for (var name in values) {
                curScore.style.setValue(name, values[name] / 25.4);
                if (Math.abs(curScore.style.value(name) * 25.4 - values[name]) > 0.001)
                    throw new Error("Page setting was not applied: " + name);
            }
            return { success: true, layout: getPageLayout() };
        });
    }

    function setLayoutBreak(params) {
        if (!curScore) return { error: "No score open" };
        if (!params || !Number.isInteger(params.measure) || params.measure < 1)
            return { error: "measure must be a positive one-based measure number" };
        if (["line", "page", "none"].indexOf(params.type) < 0)
            return { error: "Layout break type must be line, page, or none" };
        var cursor = createCursor({startTick: 0, startStaff: 0, voice: 0});
        for (var i = 1; i < params.measure; i++) {
            if (!cursor.nextMeasure()) return { error: "Measure is outside the score" };
        }
        var measure = cursor.measure;
        if (!measure) return { error: "No target measure" };
        var breaks = [];
        for (var j = 0; j < measure.elements.length; j++) {
            var item = measure.elements[j];
            if (item.type === Element.LAYOUT_BREAK) {
                if (item.layoutBreakType === LayoutBreak.SECTION)
                    return { error: "A section break exists here; preserve its musical settings" };
                breaks.push(item);
            }
        }
        var target = params.type === "line" ? LayoutBreak.LINE : LayoutBreak.PAGE;
        if ((params.type === "none" && !breaks.length) ||
            (params.type !== "none" && breaks.length === 1 && breaks[0].layoutBreakType === target))
            return { success: true, changed: false, measure: params.measure, type: params.type };
        return executeWithUndo(function() {
            for (var k = 0; k < breaks.length; k++) measure.remove(breaks[k]);
            if (params.type !== "none") {
                var br = newElement(Element.LAYOUT_BREAK);
                br.layoutBreakType = target;
                measure.add(br);
            }
            return { success: true, changed: true, measure: params.measure, type: params.type };
        });
    }

    function writtenToConcertKey(fifths, interval) {
        // A chromatic semitone contributes seven fifths; a diatonic step twelve.
        var key = fifths + 7 * interval.chromatic - 12 * interval.diatonic;
        while (key < -7) key += 12;
        while (key > 7) key -= 12;
        return key;
    }

    function setKeySignature(params) {
        if (!curScore) return { error: "No score open" };
        if (!params || !Number.isInteger(params.fifths) || params.fifths < -7 || params.fifths > 7)
            return { error: "fifths must be an integer from -7 (flats) to 7 (sharps)" };
        if (!Number.isInteger(params.staff) || params.staff < 0 || params.staff >= curScore.nstaves)
            return { error: "staff must be a valid zero-based staff index" };
        if (!Number.isInteger(params.measure) || params.measure < 1)
            return { error: "measure must be a positive one-based measure number" };
        if (curScore.style.value("concertPitch"))
            return { error: "Written-key editing requires the score's concert pitch display to be off" };
        var cursor = createCursor({startTick: 0, startStaff: params.staff, voice: 0});
        for (var m = 1; m < params.measure; m++) {
            if (!cursor.nextMeasure()) return { error: "Measure is outside the score" };
        }
        if (!cursor.measure || !cursor.segment) return { error: "No music at target measure" };
        var staff = curScore.staves[params.staff];
        var interval = staff.transpose(cursor.fraction);
        var concert = writtenToConcertKey(params.fifths, interval);
        var tick = cursor.tick;
        var existing = null;
        for (var segment = cursor.measure.firstSegment; segment && segment.tick <= tick; segment = segment.next) {
            var item = segment.elementAt(params.staff * 4);
            if (item && item.type === Element.KEYSIG && segment.tick === tick) {
                existing = item;
                break;
            }
        }
        if (existing && existing.actualKey === params.fifths && existing.concertKey === concert)
            return { success: true, changed: false, staff: params.staff, measure: params.measure,
                     tick: tick, writtenFifths: params.fifths, concertFifths: concert };
        return executeWithUndo(function() {
            if (existing) removeElement(existing);
            var key = newElement(Element.KEYSIG);
            key.concertKey = concert;
            key.actualKey = params.fifths;
            cursor.add(key);
            return { success: true, changed: true, staff: params.staff, measure: params.measure,
                     tick: tick, writtenFifths: key.actualKey, concertFifths: key.concertKey };
        });
    }

    function setTimeSignature(params) {
        var validation = validateParams(params, ["numerator", "denominator"]);
        if (!validation.valid) return validation;
        
        return executeWithUndo(function() {
            var cursor = createCursor();
            var currTick = cursor.tick;
            var currStaff = cursor.staffIdx;

            var ts = newElement(Element.TIMESIG);
            ts.timesig = fraction(params.numerator, params.denominator);
            cursor.add(ts);

            return { 
                success: true, 
                message: "Time signature set to " + params.numerator + "/" + params.denominator
            };
        });
    }

    function setTempo(params) {
        var validation = validateParams(params, ["bpm"]);
        if (!validation.valid) return validation;
        
        return executeWithUndo(function() {
            var cursor = createCursor();
            
            var tempo = newElement(Element.TEMPO_TEXT);
            tempo.tempo = params.bpm / 60.0;
            tempo.text = "♩ = " + params.bpm;
            
            cursor.add(tempo);
            
            return { success: true, message: "Tempo set to " + params.bpm + " BPM" };
        });
    }

    // ========================================
    // SCORE ANALYSIS
    // ========================================

    function getScore(params) {
        if (!curScore) return { error: "No score open" };
        
        try {
            return { success: true, analysis: getScoreSummary() };
        } catch (e) {
            return { error: e.toString() };
        }
    }

    function getScoreSummary() {
        if (!curScore) return { error: "No score open" };

        return executeWithUndo(function() {
            var tempState = selectionState;
            var score = {
                title: curScore.metaTag("workTitle") || curScore.title || "",
                numMeasures: curScore.nmeasures,
                measures: [],
                staves: []
            };
            
            // Analyze staves
            for (var i = 0; i < curScore.nstaves; i++) {
                var staff = curScore.staves && curScore.staves[i] || 
                           (typeof curScore.staff === "function" ? curScore.staff(i) : null);
                
                score.staves.push({
                    name: `staff${i}`,
                    shortName: staff ? staff.shortName : "",
                    visible: staff ? !staff.invisible : true
                });
            }

            // Analyze measures
            var cursor = createCursor({startTick: 0});
            var measureBoundaries = [];

            // Get measure boundaries
            for (var i = 0; i < curScore.nmeasures; i++) {
                var measure = {
                    measure: i + 1, 
                    startTick: cursor.tick,
                    numElements: 0, 
                    elements: {}
                };

                for (var j = 0; j < curScore.nstaves; j++) {
                    measure.elements[`staff${j}`] = [];
                }

                measureBoundaries.push(cursor.tick);
                score.measures.push(measure);
                cursor.nextMeasure();
            }

            // Process elements for each staff
            for (var k = 0; k < curScore.nstaves; k++) {
                cursor.rewind(0);
                var currentSegment = cursor.segment;

                while (currentSegment) {
                    var measureIdx = measureBoundaries.filter(function(tick) {
                        return tick <= currentSegment.tick;
                    }).length - 1;

                    for (var v = 0; v < 4; v++) {
                        var track = k * 4 + v;
                        var el = currentSegment.elementAt(track);
                        if (el) {
                            score.measures[measureIdx].numElements++;
                            var processedElement = processElement(el);
                            if (processedElement) {
                                processedElement.startTick = currentSegment.tick;
                                processedElement.voice = v;
                                score.measures[measureIdx].elements[`staff${k}`].push(processedElement);
                            }
                        }
                    }
                    currentSegment = currentSegment.next;
                }
            }

            // Restore state
            selectionState = tempState;
            return score;
        });
    }

    // ========================================
    // INITIALIZATION
    // ========================================

    onRun: {
        console.log("Starting MuseScore API Server (Clean Version) on port 8765");
        
        api.websocketserver.listen(8765, function(clientId) {
            console.log("Client connected with ID: " + clientId);
            clientConnections.push(clientId);
            
            api.websocketserver.onMessage(clientId, function(message) {
                processMessage(message, clientId);
            });
        });
    
        if (curScore) {
            initCursorState();
        }
    }
}
