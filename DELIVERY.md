# ScoreBridge first-release acceptance

## Fixed design

Skill instructs the calling Agent → Agent reads original PDF/images → internal
notation plan → MuseScore MCP executes the plan → MuseScore handles engraving,
instruments, playback and saving → MSCZ is the main user deliverable.

Computer use, screenshots of the desktop, menu automation and Accessibility are
not dependencies. Audiveris remains optional. No mandatory human review or
second recognition pass is inserted. Recognition is performed by the calling
multimodal Agent; ScoreBridge is its software-operation tool.

## Fixed acceptance checkpoints

The checkpoints for this release are fixed and are not estimates of recognition
accuracy. Future features do not change this release's denominator.

| Checkpoint | Acceptance | State |
| --- | --- | --- |
| 64% | Source preparation, base notation and standard instruments | Completed in prior commits |
| 73% | Exact document identity before live edits | Completed, CI passed |
| 82% | Special notation and real unpitched percussion | Passed native-file and audio checks |
| 91% | Unattended creation/edit/save without computer use | Passed official extension host and MCP stdio call |
| 100% | Native orchestral regression, installed-package checks and release | Pending final CI/release |

## What the delivered route does

`musescore_build_score` creates the scaffold and executes a complete Agent plan
without a running GUI/plugin. `musescore_apply_plan` edits an explicitly bound
file. Both use MuseScore's official extension host and a matching per-run receipt.
Failed batches never publish a partial copy or replace an existing output.
The optional live WebSocket backend remains available for already-open documents.

Tests cover notes/chords, voices, rests, tuplets, ties/slurs, grace notes and order,
dynamics, lyrics/text, tempo units, keys, layout, standard templates and percussion.
The local orchestral source is retained only on the owner's computer; it is not
included in the repository or release. The public executable plan uses original
demo music. Runtime evidence is recorded in `tests/LIVE_EDITOR_RESULTS.md`.

The verified platform is macOS / MuseScore Studio 4.7.4. Windows/Linux extension
locations are provided but have not had a real application acceptance run.

## Capabilities still outside this release

Arbitrary MuseSound/VST selection, playback changes triggered solely by technique
text, cross-staff slurs, two-chord tremolos, and Sibelius/Cubase backends are not
implemented here. The workflow preserves the Agent's supplied content; it does
not claim a measured recognition percentage or identical layout for arbitrary
scores. Missing commands return errors instead of silently discarding notation.
