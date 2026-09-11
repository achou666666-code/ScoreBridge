# Live editor plans

A plan is execution data, not a new mandatory music representation. Use small,
ordered batches with stable IDs:

```json
{"steps": [
  {"id": "flute-m1-position", "action": "goToMeasure", "params": {"measure": 1}},
  {"id": "flute-m1-dynamic", "action": "addDynamic", "params": {"type": "p"}}
]}
```

These example actions target mcp-score and assume the correct score/staff is open.
The bundled action-protocol plugin supports `save`, which saves the currently
open document to its existing MuseScore path.
`addDynamic` is present in the bundled implementation but stays reserved until
it passes a clean MuseScore-version smoke test; plans must not treat a reserved
command as acknowledged editor work.
Read the installed plugin's parameters before writing. Do not assume command names
or duration conventions are interchangeable across plugins.

## Backend evidence

ScoreBridge is a WebSocket client; it does not bundle a MuseScore plugin.
The two locally inspected upstream plugin implementations differ:

| Plugin | Wire key | Implemented examples | Missing or misleading operations |
| --- | --- | --- | --- |
| mcp-score | `command` | notes, keys, meter, tempo, dynamics, chord symbols, repeats, staff navigation, sequences | No create/open/save, instrument management, lyrics, slurs or layout commands in inspected dispatcher; voice fixed to 0 |
| mcp-musescore style API Server | `action` | notes, rests, tuplets, lyrics, append instrument, meter, tempo, save (bundled plugin) | `setInstrumentSound` opens a dialog only; `setStaffMute` changes visibility; no create/open or key command in inspected dispatcher |

This table describes inspected source, not every release or a live capability guarantee.
There is no universal capability discovery command. The status tool reports the
negotiated wire protocol, not full editor coverage. Neither upstream plugin alone
currently supplies the complete intended workflow.

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
