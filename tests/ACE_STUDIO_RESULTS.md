# ACE Studio prototype verification

Date: 2026-10-02. Platform: macOS, ACE Studio 2.1.8, official MCP Surface 17.1.

This is an integration feasibility test. It is not yet a shipped ScoreBridge
ACE adapter. Project naming and product descriptions are unchanged.

## Connection and execution

The official `acestudio-cli` connected to the running app. An MCP stdio client
also initialized `ace-mcp-server`, read its command schemas, imported the MIDI,
read a mounted AI source, modified/restored a note and saved the native project.
The official CLI handled instrument assignment, voice splitting, playback,
audio rendering and reopening. No desktop automation was used.

The source was an existing, privately held orchestral MSCZ with 211 measures,
22 parts and 23 staves. MuseScore exported an internal MIDI transfer file.
ACE imported 23 editable tracks, including separate piano hands, with the
source tempo and meter explicitly enabled. Source notation recognition was
not re-tested in this run.

## Actual AI sources

Sound sources were discovered from ACE's live instrument catalog. Loading them
changed the tracks to `Instrument`; `sound-source get` verified the source refs,
the `Chorus26` model and the `ready` state. Names alone were not used as evidence.

| Source family | Verified library sources |
| --- | --- |
| Strings | Violins 1 (12), Violins 2 (10), Violas (8), Celli (6), Basses (4) |
| Clarinet | Clarinet - Carlo Alfonso |
| Trumpet | Trumpet - Xiaochuan Li |
| Horn | French Horn - William Hughes |
| Trombone | Trombone - Luis Aguirre, Trombone - Daniel Eddington |

Six wind tracks with overlapping notes were duplicated and partitioned into
monophonic lanes before loading solo AI instruments. The union of both lanes
matched the original note content. After splitting, the project had **29 tracks,
18 mounted AI instrument tracks and 15,954 positive-duration notes**. Reopening
preserved the bindings, pitches, start ticks and durations. The ten meter
entries and tempo changes before the content end matched the exported MIDI.

## Rendering and editing

- The actual MCP note edit changed a pitch and restored it; note content was
  read back after each write. Native saving also ran through MCP.
- A separate five-measure native project held 222 notes. AI synthesis reached
  idle before its final audio check.
- Per-track export jobs reported `succeeded`. Four active AI tracks produced
  stereo 44.1 kHz WAV, approximately 9.696 seconds each. Normalized peaks were
  0.3122 (clarinet), 0.1192 (violin 2), 0.2006 (viola), and 0.2631 (cello).
- The short project reopened with the 222 notes and 18 AI bindings intact.
- Playback was read back as `playing`, with the playhead advancing. It was
  stopped after testing; the full native project was restored in the app.

Native `.acep` projects, source music and raw traces remain on the owner's
computer. They are not included in this repository.

## Findings for an ACE adapter

The current library had no exact AI counterpart for eleven imported tracks,
including flute, oboe, bass clarinet, bassoon, tuba, timpani, percussion, mallets
and piano hands. Their MIDI content was retained and those tracks were muted
for the AI test. The test establishes control of available AI sources; it does
not establish a complete orchestral sound assignment.

The MIDI exporter emitted 48 zero-duration note events. ACE omitted them; every
positive-duration note matched. A tempo reset at the exact content end was also
omitted by import, with timing inside the musical content preserved.

The next adapter must resolve instruments from the live catalog, preserve
source-to-track mapping through voice splitting, and map notation techniques
to supported ACE articulations and parameter curves. Printed technique text
and a MIDI import alone do not complete that mapping.
