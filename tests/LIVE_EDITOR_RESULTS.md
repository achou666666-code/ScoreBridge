# Live editor verification

## Plugin 2.8 semantic grace notes, September 20, 2026

On MuseScore 4.7.4, `addGraceNote` targeted existing main chords by exact staff,
voice and tick and created all eight supported semantic types: `acciaccatura`,
`appoggiatura`, `grace4`, `grace16`, `grace32`, `grace8after`, `grace16after`,
and `grace32after`. Each command read back the requested MIDI pitch, written TPC,
MuseScore `NoteType`, before/after placement and grace-note count before success.

After plugin save, direct MSCZ/MSCX inspection found each corresponding XML tag
exactly once and the requested pitches/TPC2 values beside those tags. MuseScore
also rendered the edited score to a 6,179,686-byte, 44.1 kHz stereo Float32 WAV.
The test used only `/tmp` artifacts. During the test, `create-score --open` started
a second MuseScore process while the WebSocket remained attached to the first;
the live edits were therefore deliberately run on the first process's disposable
score after checking `getScore`. Selecting the intended open MuseScore instance
is an explicit requirement for the remaining end-to-end regression.

## CLI scaffold to live MCP lifecycle, September 20, 2026

`scorebridge create-score` created a five-measure 12/8 MSCZ from a JSON
specification with flute, B-flat clarinet, F horn and two-staff piano. MuseScore
4.7.4 opened the resulting 34 KB file. `getScore` reported five measures and five
staves with 2880-tick measure rests. `getMidiChannels` read the real MuseScore
instrument IDs `flute`, `bb-clarinet`, `horn`, and `piano`; replaying the returned
`setPartInstrument` steps was idempotent (`changed:false`) for all four parts.

The same live plan wrote a dotted-quarter flute note, clarinet note, horn note and
piano triad at tick 0, then saved through the plugin. Saved MSCX inspection
confirmed the four instrument IDs, 12/8 signatures, requested pitches/TPC values,
written/concert key handling for the transposing parts, and tempo quarter=124.
MuseScore rendered the MSCZ to a valid 44.1 kHz stereo WAV of 6,179,686 bytes.
This verifies the complete scaffold → open → MCP edit → save → playable-render
lifecycle on this standard orchestral subset. The smoke artifacts remained under
`/tmp` and are not repository fixtures.

The macOS path opener was also changed to send a normal application document-open
event through `/usr/bin/open -a`. Repeating `scorebridge open-score` then opened
the requested MSCZ directly in MuseScore, including when another instance had
recently been active; launching the bundle's inner binary had previously returned
a process ID without reliably opening the document.

## Plugin 2.7 positioned rests and tuplets, September 19, 2026

On MuseScore 4.7.4, `addRest` wrote a quarter rest at tick 0 on staff 0,
voice 2 (the third voice). `addTuplet` then created a 3:2 tuplet at tick 960 on
voice 3 with a requested total duration of 1/4. The command read back ratio 3:2
and 480 ticks. Saved MSCX inspection confirmed a separate third-voice block with
the requested rest and a separate fourth-voice block containing `normalNotes=2`,
`actualNotes=3`, three eighth rests and `endTuplet`.

The live batch saved through the plugin. The fixture was then restored from its
pre-test backup; both files had SHA-256
`b1011bb5854be7c2d7e7cf941d437893e2a72ee2590d4b44714e7a608b7f94`.
Automated tests cover explicit staff/voice/tick/duration, invalid inputs, ratio
verification, selection bounds and null parameter handling. This verifies simple
same-measure tuplets; nested, cross-measure and beamed-note replacement remain
outside this result.

## Plugin 2.6 positioned chords, voices and ties, September 19, 2026

On MuseScore 4.7.4, two `addChord` calls replaced the three quarter rests in the
first staff's second 3/4 measure with two 3/8 chords. The saved MSCX contained
two dotted-quarter chords with exact requested pairs: (72/C TPC14, 76/E TPC18,
79/G TPC15) and (72/C TPC14, 77/F TPC13, 81/A TPC17). `addTie` on pitch 72 saved
paired forward/back Tie spanners at relative offsets +3/8 and -3/8; the other
notes were not tied.

The first secondary-voice attempt exposed that setting an empty voice before
tick positioning leaves no track element for `rewindToTick`. The implementation
was changed to locate the staff tick first and then set the voice. After a full
plugin reload, voice 1 (the second voice) saved pitch 60/TPC14 at tick 1920 and
MuseScore created a distinct second `<voice>` block. Saved XML for staves 2-5 was
byte-for-byte unchanged from the pre-test snapshot. Automated tests cover invalid
pitches, duplicate chord tones, duration/TPC errors, concert-pitch display,
nonmatching tie destinations and batch dispatch. The fixture was restored to its
pre-test SHA-256 after verification.

These checks cover positioned pitched chords and ties in ordinary notation. They
do not yet cover grace notes, percussion noteheads, tablature, cross-staff voices
or nested tuplets.

## Plugin 2.5 standard instrument playback, September 19, 2026

On MuseScore 4.7.4, `getMidiChannels` read the live flute, B-flat clarinet,
F horn and piano instrument IDs and their expected MIDI programs. A trial raw
MIDI change saved flute program 0 in MSCX, but two deterministic WAV exports were
byte-identical to the flute baseline. `setMidiPatch` is therefore reserved and
is not presented as playback assignment.

The replacement implementation uses the upstream 4.7 API
`Score.replaceInstrument(part, instrumentId)`, documented to change the
instrument definition including name, clef and sound. Replacing part 0 from
`flute` to `oboe` changed the live ID, name and channel program. The rendered
WAV retained the same length but differed in 573,438 of 650,474 float samples
(difference RMS 0.108714). Replacing it back with `flute` restored program 73;
the restored WAV SHA-256 exactly matched both original baseline renders.

This verifies standard MuseScore instrument-template playback assignment and
reversibility. It does not implement arbitrary MuseSound, VST, SoundFont or
per-technique resource selection. The fixture was restored to flute after the
test and is not included in the source commit.

## Plugin 2.4 page layout, September 16, 2026

On MuseScore 4.7.4, setPageLayout set A4 (210 x 297 mm), left/right margins
18/12 mm and top/bottom margins 20/16 mm. After saving, restarting MuseScore and
reopening the MSCZ, getPageLayout returned these values within 0.001 mm.

The initial break call failed because the internal C++ enum name LayoutBreakType
is not exposed under that name in QML. Upstream v4.7.4 qmlpluginapi.h declares
LayoutBreak; after correcting it and reloading, a batch set a page break after
measure 1 and saved. getPageLayout reported two pages; a desktop screenshot showed
the first measure on page 1 and the beginning of page 2 separately.

Subsequent page -> line -> none -> page edits saved exactly one matching LayoutBreak
(or none) in MSCZ. Repeating the same page break returned changed:false. Note
pitches, durations and existing markings matched the pre-test snapshot. Margins
exceeding the paper width were rejected with no change to the read-back layout.

These checks verify manual page controls, not automatic engraving quality or
source-layout matching. The source API evidence is v4.7.4 style/styledef.cpp
(inch units), api/v1/style.h (setValue), elements.cpp (MeasureBase add/remove),
and qmlpluginapi.h (public LayoutBreak enum).

## Plugin 2.3 written key signatures, September 15, 2026

Verified on MuseScore 4.7.4 (the offered 4.7.5 update was not installed).
The implementation uses the v4.7.4 API's KeySig.concertKey/actualKey,
Staff.transpose(Fraction), and cursor.add. Source references are
src/engraving/api/v1/elements.h, cursor.cpp, apistructs.h and
src/engraving/dom/staff.cpp and keysig.cpp in the upstream v4.7.4 tag.

A real batch saved these (written, concert) fifth counts:

- Flute, measure 1: (-3, -3).
- B-flat clarinet, measure 1: (-1, -3).
- F horn, measure 1: (-2, -3).
- B-flat clarinet, measure 2: (2, 0), replacing the previous key.

A desktop screenshot confirmed the visible 3/1/2 flats and the clarinet's later
2 sharps. Saved MSCZ inspection found exactly one key per target position. All
notes retained their pitch/tpc/tpc2 values; both piano staves' XML was unchanged
from a pre-test backup. Repeating the clarinet measure-2 setting returned
changed:false. Out-of-range measures, staves and fifth counts returned errors.
These checks cover written-pitch display and these instruments, not arbitrary
custom keys or all transposing instruments. No listening test was performed.

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
