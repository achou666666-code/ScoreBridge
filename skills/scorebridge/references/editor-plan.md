# Live editor plans

A plan is execution data, not a new mandatory music representation. Use small,
ordered batches with stable IDs:

```json
{"steps": [
  {"id": "flute-m1-position", "action": "goToMeasure", "params": {"measure": 1}},
  {"id": "flute-m1-dynamic", "action": "addDynamic", "params": {"type": "p"}}
]}
```

Check the connected backend's capabilities and parameters before execution.
The bundled action-protocol plugin 2.1 supports standard `addDynamic`,
`addTechniqueText`, and `save` on an already-open score. `save` uses its existing
MuseScore path. Set an explicit staff/tick range when positioning a batch:
`selectCustomRange({startTick: 0, endTick: 480, startStaff: 0, endStaff: 1})`.
Staff indices are zero-based and endStaff is exclusive. Do not assume duration
conventions or command names are interchangeable across plugins.

## Backend evidence

ScoreBridge includes `plugins/musescore-mcp-websocket.qml`. Its `getCapabilities`
response separates available `commands` from `reserved_commands`; editor-status
exposes that response. Upstream mcp-score uses a different `command` protocol;
the bundled plugin uses `action`. Prefer the connected instance's capabilities
over an upstream command list. Opening an existing file is handled by
`musescore_open`; new-score creation, Save As, and direct sound assignment are
still reserved in the QML plugin.

The range → dynamic → technique text → save batch was verified on MuseScore
4.7.4 by inspecting the saved MSCZ: `mp` with velocity 64 and the exact staff text
occurred on the target staff only. This verifies these edits, not all notation
or audible technique switching.

Plugin 2.2 adds batched `addArticulation({type:"staccato"})` (also marcato,
tenuto) and `addSlur({})`. Use selectCustomRange before each operation. A slur
connects the selected notes in a single staff and voice; select at least two
chord positions. Live tests verified exact saved symbols and paired slur endpoints
in an initially unmarked second staff. Rest-only and multi-staff ranges are
rejected, as is a one-note slur. Articulations toggle existing marks; these writes
are not idempotent. Cross-staff and mixed-voice slurs need another editing route.

`SCOREBRIDGE_MUSESCORE_WS` overrides `ws://localhost:8765`.
`SCOREBRIDGE_MUSESCORE_PROTOCOL` may be `auto`, `action`, or `command`.
Auto mode probes only `ping`; write operations are never retried automatically.

Plans execute sequentially, not atomically. On `incomplete`, preserve completed
IDs and read actual editor state before continuing. A timeout can occur after an
edit applied. Do not replay the full plan and duplicate notes. `executed` means
commands acknowledged, not that a score has been saved or verified musically.

A notation-only marking and its playback effect are separate checks. An opened
instrument dialog, a renamed part, or a nonempty audio file does not demonstrate
a correct instrument assignment.

## Written key signatures (bundled plugin 2.3)

Use `setKeySignature` in a plan with explicit `staff`, `measure`, and `fifths`.
For a B-flat clarinet at staff 1 whose second measure prints one flat:
`{"action":"setKeySignature","params":{"staff":1,"measure":2,"fifths":-1}}`.
Read the printed key directly; do not pre-transpose this input. The command derives
the concert key from MuseScore's staff transposition at that measure. An identical
setting returns changed:false. A new setting replaces the signature at that
position without transposing existing notes. It affects the selected staff only.
Use written-pitch display and conventional keys (-7 through +7); percussion and
custom key signatures need another route. The target must be a measure start.
