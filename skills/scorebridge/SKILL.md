---
name: scorebridge
description: Read PDF or image sheet music as an Agent and create editable, playable MSCZ files through ScoreBridge's MuseScore MCP or CLI.
---

# ScoreBridge

The calling Agent recognizes the original music. ScoreBridge executes the notation
plan in MuseScore and delivers one editable, playable `.mscz` by default.

**The workflow must not depend on computer use, screen control, menu clicking,
or Accessibility automation.** Use the official MuseScore extension host through
MCP or CLI. Live WebSocket editing is optional, not a prerequisite.

## Source to MSCZ

1. Run `scorebridge doctor`. Install MuseScore Studio with `--extension` support
   (verified on macOS Studio 4.7.4), and ScoreBridge's `mcp,image` extras. Neither
   Audiveris, a running GUI, nor the WebSocket plugin is required for the default route.
2. Use `score_transcribe(input_path, output_dir)` or `scorebridge prepare INPUT
   --output WORKDIR`. It prepares evidence and returns `awaiting_agent`: the
   **calling Agent** now reads the images. This is not human review or an OMR task.
   Preserve original images, processed images and their page mapping. Order pages
   from printed numbering and musical continuity; identify covers before skipping.
3. Read each part in musical order. Establish instruments, staves, clefs, printed
   keys and meter, then all pitches/spellings, rests, chords, voices, duration,
   tempo changes, lyrics, ties/slurs, dynamics, techniques and layout. Compare an
   enhanced image with the original if preprocessing changes a mark. Resolve
   uncertainty from visual and musical context and continue; no compulsory second
   recognition pass or human measure-by-measure approval.
4. Keep a compact internal `score` specification plus ordered `steps` with unique
   IDs. Legacy Score IR is optional. Read [editor-plan.md](references/editor-plan.md)
   for command parameters, written pitch/TPC handling and notation scope. Preserve
   every recognized mark: extend the adapter for missing operations rather than
   silently discarding music or switching to computer use.
5. Call `musescore_build_score(specification, steps, output_path)` for complete
   creation. It privately creates a scaffold, executes the same notation commands
   in MuseScore's official extension host, checks the execution receipt and
   publishes MSCZ only if the full batch succeeds. CLI: `scorebridge build-score
   PLAN.json --output SCORE.mscz`, where PLAN is `{"score":...,"steps":[...]}`.
   For subsequent edits use `musescore_apply_plan` / `scorebridge apply-plan` with
   the exact returned `target`. A failed private batch is not published; correct
   and replay it from the unchanged source. Verify real instrument assignments,
   not just printed labels. Standard templates carry playback assignments.
6. Verify saved MSCZ content, intended part identities and note data. Inspect a
   rendered page when layout matters, and render audio when playback is requested.
   These are software/output checks, not another recognition pass. A nonempty WAV
   proves signal, not recognition accuracy or subjective sound quality. Deliver
   the MSCZ link; intermediate XML, plans and diagnostics remain private.

## Optional live editing

If the user wants to edit a currently open document, the bundled QML/WebSocket
plugin can be enabled once by the user. `musescore_connect` only checks connection;
it does not click menus. `musescore_bind_score` and `musescore_execute_plan` check
exact document identity before edits. Live plans can partially apply; retain
completed IDs and inspect state after a timeout instead of blindly replaying.

`addTechniqueText` preserves instructions such as `pizz.` and `con sord.`;
text alone does not select a playback technique. Arbitrary MuseSound/VST resources,
cross-staff slurs and two-chord tremolos need additional backend support.
Do not report unsupported effects as implemented.

Audiveris is opt-in assistance via `score_transcribe(..., mode="omr")`, not the
recognition engine for this default workflow.
