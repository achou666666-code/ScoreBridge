# ScoreBridge

Agent-led sheet-music transcription and MuseScore control. The calling Agent reads
PDF/PNG/JPG/TIFF/WebP sources, organizes music, and uses editor tools to produce
an editable, playable **MSCZ**. Audiveris is opt-in assistance.

## Default workflow

```text
PDF / images → source preparation → Agent reads the score
→ internal music / command plan → MuseScore editing → MSCZ
```

The default backend runs Agent notation commands in MuseScore's official
`--extension` host. **No computer use, screen control, menu automation,
Accessibility permission, running GUI or live plugin is required.** The Agent
recognizes the score; ScoreBridge does not embed a recognition model.
See [command details and supported notation](skills/scorebridge/references/editor-plan.md).

## Create a score

After the Agent reads the source, it supplies a specification and notation steps:

```bash
.venv/bin/scorebridge build-score examples/native-plan.json --output my-score.mscz
```

MCP equivalent: `musescore_build_score(specification, steps, output_path)`.
For later edits, supply the returned exact target in a plan and use
`musescore_apply_plan` or `scorebridge apply-plan PLAN.json --input SCORE.mscz`.
The extension executes against a private copy and writes a per-run receipt into
MSCZ. A failed or wrong-target batch never replaces the source or an existing
output. Successful batches publish one native MSCZ.

The file backend is verified on **macOS / MuseScore Studio 4.7.4**. Linux and
Windows extension paths are provided, but their runtime acceptance is still
unverified. Use `SCOREBRIDGE_EXTENSION_DIR` to override the extension install path.
MuseScore must support `--extension`. Future Sibelius/Cubase adapters are outside
this release.

## Install

```bash
git clone https://github.com/achou666666-code/ScoreBridge.git
cd ScoreBridge
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[mcp,image,websocket,test]'
.venv/bin/scorebridge doctor
```

Install MuseScore separately. `doctor` checks dependencies. The default extension route does not need a
WebSocket listener. `editor-status` checks the optional live plugin. Audiveris is optional and its absence does
not fail the environment check. Install the skill folder `skills/scorebridge`
in your Agent's skill directory, and configure the MCP server with the environment's
Python executable and the absolute path to `mcp_server/server.py`:

```bash
.venv/bin/python mcp_server/server.py
```

## Optional live WebSocket editing

The following setup applies only to an already-open interactive document.
It is not needed for `build-score` or `apply-plan`. `editor-connect` checks a
listener without controlling the screen; enable the plugin once in MuseScore
for live use.

The compatible MuseScore QML plugin is included in `plugins/`. On macOS,
install it with:

```bash
bash scripts/install_musescore_plugin.sh
```

Then open a score in MuseScore and choose `Plugins > MuseScore API Server`
(older reloads may display the filename `musescore-mcp-websocket`).
Leave the plugin running while ScoreBridge sends editing commands. Verify the
live connection with `.venv/bin/scorebridge editor-status`.

ScoreBridge includes its compatible MuseScore editor plugin and a WebSocket
client. Other implementations such as
[mcp-score](https://github.com/tskovlund/mcp-score) and
[mcp-musescore](https://github.com/ghchen99/mcp-musescore) use different command
sets and wire formats. The bundled plugin must be running for live editing.
Set `SCOREBRIDGE_MUSESCORE_WS` for a custom endpoint (default `ws://localhost:8765`).
Protocol detection uses read-only ping; `SCOREBRIDGE_MUSESCORE_PROTOCOL` can force
`action` or `command`. No mutation is automatically retried after a timeout.
`scorebridge editor-status` reads the plugin's declared command list without
editing the score. Restart MuseScore after updating the plugin so QML is reloaded.
The status response separates verified `commands` from `reserved_commands` that
are intentionally unavailable on MuseScore 4.7.4.
Playback mute and arbitrary audio-resource assignment remain reserved.
`setStaffVisible` controls engraving visibility and is never reported as audio mute.
Bundled plugin 2.5 adds `getMidiChannels` for diagnosis and
`setPartInstrument({part: 0, instrumentId: "flute"})` for replacing a part with
a standard MuseScore instrument template. This updates notation defaults and the
playback sound. Raw MIDI program changes are not advertised as sound assignment:
MuseScore 4 can retain the same audio resource after a MIDI program edit.

The live bridge edits and saves an already-open score. ScoreBridge creates the
initial MSCZ through the tested CLI adapter instead of guessing unsupported QML
creation and Save-As APIs. Call `musescore_create_score` with a title, measure
count, meter and parts; it builds a private MusicXML scaffold, converts it to a
validated MSCZ, and can open it for live MCP editing. Arbitrary MuseSound/VST
resource selection remains pending. The QML lifecycle command names stay reserved
and return a clear unsupported result rather than claiming success.

`musescore_open` is the supported path-opening helper for an existing MSCZ or
MusicXML file. It launches MuseScore with that file and returns the process id;
the Agent should then wait for `musescore_websocket_status` to confirm the plugin
before sending edits. CLI equivalents are `scorebridge create-score SPEC --output
SCORE.mscz --open` and `scorebridge open-score INPUT`.

Every newly created scaffold has a private `scorebridgeTargetId`. The create
result returns a `target` object containing that ID, score name, title, measure
count and staff count. Copy this exact object into the subsequent command plan.
`musescore_execute_plan` reads the live score identity before its first mutation
and returns `wrong_target` without sending edits if any field differs. To attach
an existing editor safely, call `musescore_bind_score(input_path, target)` or:

```bash
scorebridge bind-score score.mscz --target create-result.json
```

On macOS the binder reuses a listener only when it already owns the requested
score; otherwise it returns `wrong_target` without opening or editing anything.
When no listener exists it returns `needs_live_plugin`; it does not click menus
or launch an unbound editor. Use the default file backend instead. It reports
`bound` only after the plugin reads back the exact target. A process ID, window
title or successful file-open request alone is not accepted as binding.
Before exporting or editing playback, call `score_instrument_audit` on the
internal score plan. It reports unresolved IDs and detects an accidental piano
fallback; a part label alone is not evidence of a correct playback sound.
`addDynamic` and `addTechniqueText` are available individually and in
`processSequence` in bundled plugin 2.1. A live MuseScore 4.7.4 batch verified
range selection, standard `mp` dynamics, staff text, and saving to MSCZ.
Dynamic markings include a semantic playback value and engraved symbols.
Technique text preserves the printed instruction; it does not itself switch
playback to pizzicato, muted, or other techniques.
Bundled plugin 2.2 also supports `addArticulation` (staccato, marcato, tenuto)
and `addSlur` in batches. Select one explicit staff range first; articulations
need notes, and slurs need at least two chord positions in one voice. Live tests
verified saved symbols, slur endpoints, and isolation from other staves.
Articulation actions toggle existing markings: do not blindly replay a batch.
Cross-staff and mixed-voice slurs are outside this command's supported scope.
Bundled plugin 2.3 adds `setKeySignature({staff: 1, measure: 2, fifths: -1})`.
Use the printed key: negative numbers count flats, positive numbers count sharps,
and zero is no sharps/flats. Staff indices start at zero; measures start at one.
The plugin derives the concert key from the staff's transposition and writes both
values without transposing notes. It edits one staff at a measure start, replaces
an existing signature, and skips an identical setting. Written-pitch display must
be active. Standard keys from seven flats to seven sharps are supported; custom
microtonal signatures are outside this command's scope.
Bundled plugin 2.4 adds `getPageLayout`, `setPageLayout`, and `setLayoutBreak`.
Page dimensions and margins use millimeters; page settings apply equal left/top/
bottom margins to odd and even pages. Set a break after a one-based measure with
`setLayoutBreak({measure: 4, type: "line"})`; use `page` for a page break or `none`
to remove the layout break. Existing section breaks are preserved. Repeated
identical breaks do not accumulate. These are manual layout controls for the
Agent, not automatic source-layout matching.
Bundled plugin 2.5 adds `setPartInstrument`. Use a zero-based part index and a
real MuseScore instrument ID such as `flute`, `oboe`, `bb-clarinet`, `horn`, or
`piano`. The command verifies the resulting instrument ID before reporting
success and skips an identical assignment. Live verification replaced flute
with oboe, produced different rendered audio, then restored flute and reproduced
the original WAV byte for byte. This establishes standard-template playback
assignment; it does not select arbitrary MuseSounds, VSTs, or SoundFonts.
Bundled plugin 2.6 adds deterministic `addChord` and `addTie` commands. `addChord`
accepts an explicit zero-based staff and voice, absolute tick, whole-note duration
fraction, MIDI pitches, and optional written TPC values. It supports single notes,
chords, dotted durations, and empty secondary voices. `addTie` connects one pitch
to the immediate next chord in the same staff and voice and refuses mismatched
targets. Live verification saved two dotted-quarter triads with exact TPC spelling,
a C-to-C tie, and an independent voice-2 note while leaving the other four staves
unchanged.
Bundled plugin 2.7 makes `addRest` and `addTuplet` deterministic. Both accept an
explicit staff, voice, absolute tick and whole-note duration. `addRest` verifies
the resulting rest and supports empty secondary voices. `addTuplet` additionally
accepts an explicit ratio such as 3:2, verifies the created ratio and reports its
actual total duration. Live MuseScore 4.7.4 verification saved a quarter rest in
voice 3 and a quarter-duration eighth-note triplet in voice 4.
Bundled plugin 2.8 adds deterministic `addGraceNote`. It targets a main chord by
staff, voice and absolute tick, creates one MuseScore semantic grace chord, then
sets and reads back its MIDI pitch, optional written TPC, placement and note type.
It supports all eight before/after grace-note types exposed by MuseScore. Live
MuseScore 4.7.4 verification saved all eight XML tags and rendered the score.
See `tests/LIVE_EDITOR_RESULTS.md` for the scope of live verification.
Bundled plugin 2.9 adds read-only `getScoreIdentity`. It exposes the scaffold's
private target ID plus its current name, title, measure count and staff count for
pre-mutation binding checks. It does not infer identity from a visible filename.

## Agent entry point

Call `score_transcribe(input_path, output_dir)` through MCP, or:

```bash
scorebridge prepare INPUT --output WORKDIR
```

This prepares source-linked pages and returns `awaiting_agent`. The **calling
multimodal Agent** now reads the images; the program does not secretly run OMR
or invoke a second model. Original, rendered and enhanced images and their page
mapping remain in the working directory. Filename sorting is a convenience;
the Agent checks actual page order and identifies non-score pages.

The Agent records its established score context and notation steps in one plan:

```bash
scorebridge build-score PLAN.json --output score.mscz
```

`examples/native-plan.json` demonstrates the `score` and `steps` fields with
original demo music. The MCP form is
`musescore_build_score(specification, steps, output_path)`. It creates the native
score, applies the Agent's notation and checks the executed steps in one call.
MuseScore must be installed; a live plugin and computer use are unnecessary.

For subsequent edits, preserve the returned `target` unchanged in the edit plan:

```bash
scorebridge apply-plan EDITS.json --input score.mscz
```

The MCP equivalent is `musescore_apply_plan(plan_path, input_path)`. Each step has
a unique ID. A batch executes against a private copy; it publishes MSCZ only
after matching the target and complete execution receipt. On failure, correct
the reported step and resubmit; the previous file is preserved. `pass` establishes
execution of the supplied plan, not a measured source-recognition accuracy.

`musescore_execute_plan` and `musescore_websocket_command` remain available for
the [optional live backend](#optional-live-websocket-editing). They are not needed
for the default workflow.

## MSCZ delivery

`score_finalize` remains available for scores expressible in the legacy Score IR.
It compiles internal MusicXML, creates MSCZ through MuseScore, and keeps temporary
XML and structural audits under `.scorebridge/`. It no longer exports MIDI or PDF
by default. Failed MSCZ export returns `error`; failed reopen conversion returns
`incomplete`. The audit does not establish source accuracy or correct audible timbre.

The legacy IR cannot represent all notation. Do not silently drop unsupported
lyrics, slurs, articulations or performance semantics to make compilation pass.
For these, use supported native commands or extend the editor adapter. Missing
commands must be reported rather than replaced by computer use.

## Optional OMR and developer tools

Use `score_transcribe(..., mode="omr")` only to select the legacy
Audiveris → MusicXML → Score IR → review route. `omr_run`, `review_create`, and
`review_apply` remain available for that optional workflow. Agent-led jobs do
not require a second recognition pass or human measure-by-measure review.

`score_validate`, `score_compile`, `score_apply_patch`, `score_inspect`,
`score_build_mscz`, and `musescore_convert` are lower-level developer tools;
their intermediate files are not the default user delivery.

## Tests

```bash
.venv/bin/pytest -q
```

To check what another computer receives from Git, run:

```bash
python3 scripts/check_clean_install.py
```

This exports HEAD into a temporary directory, creates a fresh virtual environment,
installs the package and test extras, and runs the exported tests against the
installed package. It excludes uncommitted source changes and existing editable
installs. It needs network access for dependencies and Node.js for QML JavaScript
tests. The GitHub Actions workflow runs this check on pushes and pull requests.
Local-only orchestral evidence is skipped when absent; desktop MuseScore and
listening tests are separate from this installation check.

Tests include a local WebSocket server for both wire formats, nested plugin
errors, partial-plan failures without replay, input preparation without OMR,
and compilation checks. These protocol tests are distinct from real MuseScore
editing and listening tests.

## Demos

`demos/image-to-score/` is reserved for a small image-to-editable-score walkthrough. `demos/pirates/` is reserved for a later multi-page orchestral case study, screenshots, and validation reports. The public Twinkle smoke run currently produces an evidence package, Audiveris MusicXML, Score IR, and MuseScore round-trip files under `demos/image-to-score/output/twinkle-run/`. Videos are intentionally added only after they are recorded; source PDFs and other copyrighted material do not belong in the public repository.

## Release acceptance and future work

The first-release acceptance includes real MCP execution, special notation,
percussion, a five-measure orchestral regression and a clean installation check.
See [the fixed acceptance checklist](DELIVERY.md) and
[runtime evidence](tests/LIVE_EDITOR_RESULTS.md).

Future work includes two-chord tremolos, cross-staff slurs, playback technique
switching, real Windows/Linux acceptance and Sibelius/Cubase adapters.
