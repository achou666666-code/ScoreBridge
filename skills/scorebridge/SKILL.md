---
name: scorebridge
description: Read PDF or image sheet music as an Agent and create editable MuseScore scores using ScoreBridge tools and a live MuseScore bridge.
---

# ScoreBridge

The calling Agent reads the music. Deliver one editable, playable `.mscz` by default.
Audiveris is optional assistance, not the default recognition engine.

## Source to score

1. Run `scorebridge doctor` and `scorebridge editor-status`. An installed MuseScore executable is not proof that the live plugin is connected.
2. Call `score_transcribe(input_path, output_dir)` or `scorebridge prepare INPUT --output WORKDIR`. The default prepares images and returns `awaiting_agent`: this is the Agent's next action, not a request for human review. Read the returned page images. Infer page order from printed numbering and musical continuity; filename sorting is only a starting point. Identify covers yourself before skipping them.
3. Read each part in musical order. Establish written/concert pitch, instruments, staves, clefs, keys and meters; then notes/rests/chords, voices, duration, tempo changes, lyrics, ties/slurs, dynamics, articulations, techniques, repeats and layout. Preserve printed pitch spelling and per-part key signatures. Use enhancement for readability, retaining the original as evidence when enhancement changes symbols. Resolve uncertain marks from visual and musical context; track guesses internally and continue the complete score.
4. Keep a compact internal plan per part/measure. It can be tool arguments or JSON; the legacy Score IR is optional. Do not force unsupported notation through a lossy schema. Read [editor-plan.md](references/editor-plan.md) for commands, protocol differences and verified backend limitations.
5. Create/import the initial score, then apply targeted editor changes through MCP. Batch known operations where supported. Check actual instrument identity and playback assignment, not just staff labels. Internal MusicXML is permitted for efficient initial import, but is not a user deliverable. Missing MCP actions require an adapter extension or an explicitly reported software-operation fallback, not silently dropped music.
6. Save MSCZ and check that it reopens, contains the intended parts and music, and uses the intended playback assignments. Keep checks proportional: no mandatory second full recognition pass or human measure-by-measure approval. A file/transport check is not proof of source accuracy or audible sound quality. Report only checks actually performed.

## Tools

- `musescore_websocket_status`: negotiate the plugin protocol with read-only ping.
- `musescore_open`: launch an existing MSCZ or MusicXML file in MuseScore before live editing.
- CLI equivalent: `scorebridge open-score INPUT`.
- `score_instrument_audit`: verify each part maps to a real instrument sound and MIDI program before export.
- `addDynamic` is reserved pending a clean MuseScore-version smoke test; do not claim it succeeded from static inspection alone.
- `addArticulation` (staccato, marcato, tenuto) and `addSlur` are implemented but reserved pending a clean selection smoke test.
- `musescore_websocket_command`: execute one plugin-supported command; plugin errors propagate.
- `musescore_execute_plan`: ordered JSON command plan with completed IDs on failure. CLI: `scorebridge execute-plan PLAN.json`.
- `score_finalize`: legacy Score IR compilation route delivering MSCZ, with temporary XML and audit data under `.scorebridge/`.
- `score_transcribe(..., mode="omr")`: opt-in legacy OMR/review route. Do not call it unless OMR assistance is wanted.

Deliver the MSCZ link. Keep plans, source copies, intermediate formats and diagnostics in the working directory rather than presenting them as additional deliverables.
