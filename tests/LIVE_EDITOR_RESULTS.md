# Live editor verification

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
