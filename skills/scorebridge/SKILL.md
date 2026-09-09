---
name: scorebridge
description: Transcribe PDF or image music, compile structured scores, and inspect or edit notation through ScoreBridge and supported notation-software adapters. Use for OMR, MusicXML, MSCZ, MIDI, MuseScore, Sibelius, or Cubase score workflows.
---

# ScoreBridge

Use ScoreBridge as the structured bridge between source documents, music semantics, and notation software.

## Workflow

1. Inspect the input and preserve whether the source is written pitch or concert pitch. Printed instrumental scores default to written pitch.
2. For PDF or image input, retain page coordinates for every recognized element. Enhance a page when its quality score predicts recognition loss, then keep both original and enhanced images.
3. Establish parts, staves, clefs, key and meter timelines before compiling notes. Treat percussion and multi-staff instruments explicitly.
4. Convert recognition output to Score IR. Do not send thousands of untracked GUI note-entry actions when a score or measure transaction is available.
5. Validate duration closure, staff alignment, instrument identity, key and meter changes, then compile to MusicXML or a target adapter.
6. Round-trip through the target editor and compare the returned structure. Surface precise review items with page, staff, measure and source crop.

For multi-page PDFs, render each page at about 450 DPI and process pages independently. Classify only obvious cover or illustration pages as `non_score`; keep uncertain pages in the OMR queue. Retain original, rendered, enhanced, OMR logs, and MusicXML for every page. Continue after a page failure and record it in `run-summary.json`; never discard the complete score because one page failed.

## Agent review protocol

After OMR import, call `review_create` with the Score IR JSON and the input `manifest.json`. The result contains one task per part/staff/measure. Each task includes the instrument identity, clef, candidate events, previous and next measure numbers, source coordinates, and the original/rendered/enhanced page paths.

The Agent may leave a task unchanged with `{"action":"keep"}` or provide a replacement `patch` using the same high-level fields as `score_apply_patch`. Decisions are applied with `review_apply`. A rejected local decision is reported with its target and validation issue; the full score remains available and can still be compiled, so one uncertain measure never discards the rest of the transcription.

Use the enhanced page as the primary reading view, then inspect the original source whenever preprocessing may have altered an accidental, notehead, lyric, articulation, or other symbol. Review results should record the Agent's confidence and rationale in the task's `decision` object for later audit.

Use `scorebridge validate FILE.score.json` before compilation and `scorebridge compile FILE.score.json --output FILE.musicxml` to produce editable MusicXML.

For a complete job, call `score_transcribe` once with the user input and an output directory. It runs input normalization, source evidence creation, OMR, and review packet generation. Pass an Agent decision JSON as `decisions_path` to continue automatically through review application and final MuseScore exports. PDF is retained as an internal bridge artifact, while single-page raster input may be sent directly to Audiveris when that backend handles it more reliably.

When review decisions are complete, call `score_finalize` to compile and export MusicXML, MSCZ, MIDI, and PDF in one transaction. It also imports the MSCZ back to MusicXML and returns an instrument/part audit. A nonzero MuseScore exit code is acceptable only when the requested output file passes archive/file validation; the result then includes a warning.
