# Agent audio transcription development

[English](README.md) | [简体中文](README.zh-CN.md)

This directory tracks the audio input extension. Recognition belongs to the
calling Agent. CLI/MCP software adapters write and edit its music; application
audio-to-MIDI features are not part of recognition.

The current stage provides WAV/decoder input preparation, source-linked spectral
evidence, a note-event record and reproducible scoring. It does not yet provide
automatic audio-to-MSCZ/MusicXML/PDF/MIDI/DAW-project delivery.

## Reproduce the initial evaluation

```bash
python -m pip install -e '.[audio]'
python scripts/make_audio_benchmark.py --output work/controls --seed SEED
# Optional sampled-instrument fixtures, with MuseScore and ffmpeg installed:
python scripts/make_audio_benchmark.py --output work/sampled --seed SEED --musescore /path/to/mscore
scorebridge prepare-audio work/sampled/inputs/polyphonic.wav --output work/evidence
# A control with unknown note lengths/rests:
python scripts/make_audio_benchmark.py --output work/irregular --seed SEED --irregular-melody
```

Give the Agent `inputs/` and prepared evidence, not `answers/`. It writes event
predictions, then score them with `scorebridge evaluate-audio`. Do not change
predictions after opening references. The generator creates original short
four-bar patterns; synthetic control tones do not establish instrument identity.
The optional sampled fixtures are rendered by MuseScore, not recognized by it.
No proprietary samples or copyrighted composition are included.

See [validation.json](validation.json) for frozen initial judgments, reference
events, recipe seeds, prediction hashes and measurements. This is a development
self-evaluation: the same Agent knew the generator and rhythm template but did
not read random note answers before recording predictions. Drum templates were
known, so matching drum events is not independent drum classification evidence.
Instrument inference, arbitrary tempo/meter, expressive timing, real recordings
and dense orchestral audio have not been accepted by this evaluation. Figures
for these short samples are not product-wide accuracy estimates.

| Source | Matched pitched events / reference |
| --- | --- |
| Synthetic melody | 12 / 12 |
| Synthetic chords | 24 / 24 |
| Synthetic mixed | 25 / 32 |
| Sampled melody | 12 / 12 |
| Sampled piano chords | 23 / 24 |
| Sampled piano + bass + drums | 25 / 32 |
| Synthetic melody with randomized rests/durations | 10 / 10 |

The irregular control's note values and timing were read from images before
opening its answers; it remains a same-Agent synthetic test. A native MuseScore
extension run also saved the sampled-melody prediction to MSCZ. Its 12 saved
pitches were read back and matched the frozen Agent events; the flute template
was supplied from test setup, not established by independent instrument inference.

## Fixed development milestones

1. Agent audio evidence and measured event recognition (this stage).
2. Shared music plan: source seconds, performance timing, notation, instruments,
   percussion and explicit written/sounding pitch relations.
3. Score/MIDI delivery from one plan: MSCZ, MusicXML, PDF and multi-track MIDI.
4. First DAW adapter: editable note tracks, real sound routing and native saving.
5. Shared CLI/MCP/Skill workflow, exact task targets and resume support.
6. Clean-install acceptance, representative audio cases and synchronized docs.

New software adapters are later releases, not moving acceptance targets. The
next recognition test must use unfamiliar rhythm, rests, overlapping voices and
drum patterns; it must not reuse this known-template result as evidence of those
capabilities.
