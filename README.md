# ScoreBridge

On macOS, after opening a score, `scorebridge editor-connect` (MCP:
`musescore_connect`) activates the installed bundled plugin and verifies its
WebSocket connection. An existing connection is reused without clicking the
plugin again. MuseScore must be running and macOS Accessibility permission must
be available. This command does not install the plugin or restart MuseScore.

Agent-led sheet-music transcription and MuseScore control. The calling Agent reads
PDF/PNG/JPG/TIFF/WebP sources, organizes music, and uses editor tools to produce
an editable, playable **MSCZ**. Audiveris is opt-in assistance.

## Default workflow

```text
PDF / images → source preparation → Agent reads the score
→ internal music / command plan → MuseScore editing → MSCZ
```

The current implementation prepares source images, executes ordered live-plugin
commands, and offers a legacy Score IR compilation adapter. It does **not** yet
supply every MuseScore editing operation or prove high-accuracy orchestral
transcription end to end. See the [actual editor capabilities](skills/scorebridge/references/editor-plan.md).

## Install

```bash
git clone https://github.com/achou666666-code/ScoreBridge.git
cd ScoreBridge
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[mcp,image,websocket,test]'
.venv/bin/scorebridge doctor
.venv/bin/scorebridge editor-status
```

Install MuseScore separately. `doctor` checks dependencies; `editor-status`
actually contacts a running plugin. Audiveris is optional and its absence does
not fail the environment check. Install the skill folder `skills/scorebridge`
in your Agent's skill directory, and configure the MCP server with the environment's
Python executable and the absolute path to `mcp_server/server.py`:

```bash
.venv/bin/python mcp_server/server.py
```

The compatible MuseScore QML plugin is included in `plugins/`. On macOS,
install it with:

```bash
bash scripts/install_musescore_plugin.sh
```

Then open a score in MuseScore and choose `Plugins > musescore-mcp-websocket`.
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

The current live bridge edits and saves an already-open score. New-score creation,
opening a path, Save As, and arbitrary MuseSound/VST resource selection remain
pending for MuseScore 4.7.4. Standard instrument replacement is available through
`setPartInstrument`. The lifecycle command names are reserved and return a clear
unsupported result until a version-tested implementation is available; ScoreBridge
does not claim those operations succeeded.

`musescore_open` is the supported path-opening helper for an existing MSCZ or
MusicXML file. It launches MuseScore with that file and returns the process id;
the Agent should then wait for `musescore_websocket_status` to confirm the plugin
before sending edits. Creating a blank score and Save As remain version-dependent.
The same operation is available locally as `scorebridge open-score INPUT`.
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
See `tests/LIVE_EDITOR_RESULTS.md` for the scope of live verification.

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

The Agent can keep a compact command plan instead of the legacy Score IR:

```bash
scorebridge execute-plan PLAN.json
```

`examples/create-and-save-plan.json` shows the recommended lifecycle order for a
new score: create, set notation context, write content, then save as MSCZ. The
same plan can be sent through `musescore_execute_plan`; each step has a stable ID
so a partial failure can resume from the last acknowledged command.

The MCP equivalent is `musescore_execute_plan(input_path)`. It prevalidates step
IDs, executes in order, and reports completed IDs and the failed step. It is not
an atomic transaction. Inspect current editor state after a failure before
continuing. `executed` means acknowledged commands, not completed transcription.
Use `musescore_websocket_command` for individual supported operations.

## MSCZ delivery

`score_finalize` remains available for scores expressible in the legacy Score IR.
It compiles internal MusicXML, creates MSCZ through MuseScore, and keeps temporary
XML and structural audits under `.scorebridge/`. It no longer exports MIDI or PDF
by default. Failed MSCZ export returns `error`; failed reopen conversion returns
`incomplete`. The audit does not establish source accuracy or correct audible timbre.

The legacy IR cannot represent all notation. Do not silently drop unsupported
lyrics, slurs, articulations or performance semantics to make compilation pass.
For these, extend the editor adapter or use a documented software-operation
fallback and verify the actual saved score.

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

## Next editor work

Complete and verify create/open/save, instrument playback assignments, multi-voice
entry, slurs/articulations/techniques, and layout through an actual MuseScore
plugin. Then run the local orchestral regression. Sibelius support is future work.
