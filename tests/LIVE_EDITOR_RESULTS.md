# Live editor verification

## Plugin 2.2 articulation/slur batch, September 14, 2026

Reloaded MuseScore and activated the installed plugin through the desktop UI;
editor-status confirmed 2.2. On the existing five-staff Vertical Slice fixture,
selected the initially unmarked second staff and sent one nine-step sequence:
three select/articulation pairs, select ticks 0–1920, addSlur, save.
All indices 0–8 completed. Inspecting the actual saved MSCZ found:

- Tick 0: articStaccatoAbove; tick 480: articMarcatoAbove;
  tick 960: articTenutoAbove.
- Slur from the first to fourth quarter note: paired relative endpoints
  +3/4 and -3/4 in their respective chords.
- Other staves' saved articulation/spanner XML unchanged from a pre-test backup.

Three failing batches tested a rest-only articulation, one-note slur, and
multi-staff articulation. Each stopped at failedIndex 1, completedIndices [0],
without writing the following sentinel StaffText. A subsequent save confirmed
all markings unchanged. Automated JavaScript tests additionally cover missing
selection, empty selection, mixed voices and unsupported articulation names.
This promotes articulation/slur commands for these supported ranges; it is not
a listening test, arbitrary-voice engraving guarantee, or recognition benchmark.

## Plugin 2.1 batch verification, September 14, 2026

After restart, the automatic menu activation did not consistently establish a
connection. Selecting the plugin using the desktop UI did; editor-status then
reported pluginVersion 2.1. Automatic connection recovery remains incomplete.

One WebSocket processSequence call selected staff 0, ticks 1920–2400, inserted
`mp`, inserted `ScoreBridge batch verified`, and saved. The response reported
completedIndices [0, 1, 2, 3]. Reading the actual saved MSCZ confirmed `mp` subtype,
velocity 64, and exact StaffText in the first staff's second measure. The other
four staves had neither this dynamic nor the inserted marker. The original
fixture is kept out of the source commit because it contains live test edits.

This promotes addDynamic and addTechniqueText to available commands and enables
them with selectCustomRange in batch execution. It does not establish listening
quality, automatic technique switching, or general image transcription accuracy.

## Earlier follow-up, September 14, 2026

The macOS `editor-connect` CLI was tested after quitting and reopening MuseScore.
It discovered the plugin menu, clicked it in a separate AppleScript invocation,
and returned `activation: menu` only after a successful WebSocket ping.

The dynamic fix was tested in the prior live session: standard `pp` saved as
subtype `pp`, velocity 33, with canonical symbol text normalized by MuseScore.
The earlier type-only `ff` trial saved velocity 112 but empty display text;
the implementation now supplies both the type and SMuFL symbol text.
These are saved-file checks, not a listening test. Historical failures below
are retained as regression evidence.

Tested on MuseScore Studio 4.7.4 with the bundled action-protocol plugin.
The user opened the existing Vertical Slice fixture and enabled the plugin.
Commands were sent over WebSocket; results below were inspected in the saved
MSCZ's MSCX document, rather than inferred from successful replies.

| Operation | Saved result |
| --- | --- |
| addArticulation staccato at tick 480, staff 0 | articStaccatoAbove on the target staff |
| addArticulation marcato at tick 960, staff 0 | articMarcatoAbove on the target staff |
| addArticulation tenuto at tick 1440, staff 0 | articTenutoAbove on the target staff |
| addSlur over ticks 0–1920, staff 0 | Paired Slur spanners, relative endpoints +3/4 and -3/4 |
| addTechniqueText solo at tick 1920, staff 0 | StaffText containing solo |
| addDynamic pp at tick 0, staff 0 | BUG: other-dynamics with text pp, not standard pp subtype |

The other four staves contained no added articulations or slurs. No listening
test or reopened-editor verification was performed in this run. Staff text
does not establish playback technique switching. Commands remain reserved
pending broader selection/error handling checks. The dynamic implementation
must be corrected before it is advertised as standard playback dynamics.

The live selection response also included staff1 for endStaff=1 although the
saved edits correctly affected only staff0. Its reporting loop needs to match
the exclusive end-staff convention used by MuseScore selection.
