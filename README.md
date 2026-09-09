# ScoreBridge

ScoreBridge gives AI agents a structured path from PDF or image notation to editable scores and direct notation-software control.

The current vertical slice provides a Score IR model, structural validation, MusicXML compilation, and an MCP server with inspect, validate, compile, and MuseScore environment tools. OMR and transactional GUI control are the next active slices.

## Try the vertical slice

```bash
uv venv
uv pip install -e '.[test,mcp]'
python tests/make_fixture.py
scorebridge validate examples/vertical-slice.score.json
scorebridge compile examples/vertical-slice.score.json --output examples/vertical-slice.musicxml
pytest
```

The fixture contains flute, B-flat clarinet, horn in F, and a two-staff piano. It changes from 4/4 to 3/4 and carries written keys, tempo, dynamics, and technique text.

## MCP

```bash
python mcp_server/server.py
```

Available tools: `score_inspect`, `score_validate`, `score_compile`, `score_apply_patch`, `score_build_mscz`, `input_inspect`, `input_prepare`, `image_prepare`, `musescore_status`, and `musescore_convert`.
OMR tools now include `omr_status` and `musicxml_import`. The OMR engine is optional: when Audiveris is installed, its MusicXML output can be imported into ScoreBridge; when it is absent, the status tool reports the exact setup needed.

`input_prepare` is the canonical first step for agent jobs. It accepts a PDF, one raster page, or a directory of raster pages. Image directories are naturally sorted (for example `page-2` before `page-10`) and combined into an internal PDF. The output directory contains `original/` untouched sources, `pages/` high-resolution renders, `enhanced/` OMR copies, `input.pdf` for image inputs, and `manifest.json` with source/page/DPI/coordinate metadata. The original and enhanced pages are both retained so an Agent can use the enhanced image for reading while returning to the source when preprocessing may have changed a symbol.

For multi-page PDFs, `score_transcribe` follows the validated Pirates regression path: render each page at about 450 DPI, classify only obvious cover or illustration pages as `non_score`, and run OMR independently on every other page. Uncertain pages remain in the OMR queue, so classification cannot silently discard a possible score page. Each page keeps its OMR output and log, and one bad page does not stop the rest. The run writes `run-summary.json` with classifications, skipped pages, failed pages, and the merged Score IR path.

On macOS (Apple Silicon), install the official Audiveris release and place `Audiveris.app` in `/Applications`. ScoreBridge discovers `/Applications/Audiveris.app/Contents/MacOS/Audiveris` automatically; `AUDIVERIS_BIN` can be used for a custom location. The MCP `omr_run` tool accepts a PDF or image and always writes the detected MusicXML plus a `.score.json` into the requested output directory. When structural checks find suspicious measures, the result is `needs_review` with a validation report; the editable output is still produced so the Agent never discards the whole score because of local recognition errors.

Edits use a transaction-like operation. For example, an Agent can replace one measure by identifying its part and staff, supplying events, and choosing an output JSON path. The patch is rejected when the resulting measure does not close its time signature, and the input remains unchanged on rejection.

`musescore_status` should be called before conversion. The adapter reports the executable it found and returns captured process diagnostics when conversion fails. Set `MUSESCORE_BIN` or pass `executable` when MuseScore is installed outside the standard macOS path. On macOS, MuseScore's CLI still requires a healthy GUI runtime; when that process is unavailable, the next backend is the installed QML/WebSocket plugin rather than repeated blind retries.

After OMR import, call `review_create` to produce source-linked, measure-level tasks for the Agent. Each task carries the candidate notes, part/staff identity, source page and coordinates, neighboring measure context, and evidence paths. Put the Agent's accepted replacement in the task's `decision.patch`, with optional `confidence` and `rationale`, and call `review_apply`; the result keeps a decision log and reports invalid local edits while the complete score remains available for compilation.

Call `score_finalize` after review to produce MusicXML, MSCZ, MIDI, and PDF together. The command performs a MuseScore round-trip and returns an instrument/part audit. Instrument metadata includes MusicXML `instrument-sound`, MIDI program, MIDI channel, clef, and transposition; an unknown OMR label is reported for Agent mapping rather than silently assigned the piano sound.

For an Agent-facing one-call entry point, use `score_transcribe(input_path, output_dir)`. It runs `input_prepare → OMR → review_create` and returns paths to the evidence manifest, Score IR, and review tasks. Supplying `decisions_path` continues with `review_apply → score_finalize` and creates the editable/exported deliverables automatically. The canonical bridge PDF is always retained for image inputs; a single-page raster may also be used directly for OMR when the engine's raster path is more reliable.

## Run the demo

From the repository root:

```bash
uv venv
uv pip install -e '.[test,mcp]'
.venv/bin/python tests/make_fixture.py
.venv/bin/scorebridge validate examples/vertical-slice.score.json
.venv/bin/scorebridge compile examples/vertical-slice.score.json --output examples/vertical-slice.musicxml
```

Then open `examples/vertical-slice.musicxml` or `examples/vertical-slice.mscz` in MuseScore. This fixture is intentionally small and demonstrates four instruments, a two-staff piano, a meter change, key changes, tempo, dynamics, and technique text.

## Demos

`demos/image-to-score/` is reserved for a small image-to-editable-score walkthrough. `demos/pirates/` is reserved for the later 《加勒比海盗》 recording, screenshots, and validation reports. The public Twinkle smoke run currently produces an evidence package, Audiveris MusicXML, Score IR, and MuseScore round-trip files under `demos/image-to-score/output/twinkle-run/`. Videos are intentionally added only after they are recorded; source PDFs and other copyrighted material do not belong in the public repository.

## Product path

1. Reliable Score IR and editor round trips
2. MuseScore adapter with transactional editing and export
3. PDF/image quality analysis and enhancement
4. OMR/OCR fusion with source-linked review
5. Sibelius and Cubase adapters
6. Reproducible video demos under `demos/`
