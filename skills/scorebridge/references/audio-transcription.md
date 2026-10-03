# Agent-owned audio transcription

Use this reference for audio inputs; existing PDF/image instructions still apply
to sheet music. Do not ask a DAW or notation application's transcription feature
to recognize music. CLI/MCP editor interfaces receive Agent-authored music only.

## Available tools

Install `.[audio]`. WAV PCM16 can be prepared directly. Install `ffmpeg` for MP3,
float WAV and other formats it can decode, or set `SCOREBRIDGE_FFMPEG` to its path.

```bash
scorebridge prepare-audio INPUT.wav --output work/audio
```

MCP: `audio_prepare(input_path, output_dir)`. The tool returns `awaiting_agent`,
source-linked WAV segments, raw waveform/STFT images and an evidence manifest.
It never selects notes, recognizes an instrument, or invokes another model.
Read original audio with the host's audio input when supported. Otherwise use
spectral images as visual evidence and record `evidence_mode: raw_spectral_images`;
do not report that you heard the source. A path/preview alone does not establish
that the host exposes audio to its Agent.

Inspect both spectral resolutions: long windows distinguish pitches, short
windows locate attacks. Harmonics at octave/fifth intervals are not independent
notes unless their attacks, envelopes and context support that judgment. Request
a narrower display with `--midi-low 54 --midi-high 84` when needed. Read absolute
source seconds from the axes, join consecutive segments and deduplicate their
overlap. Keep note releases separate from acoustic reverb tails. Infer drum
events independently of pitched bass notes; do not assume a repeating pattern.

## Event record for the first development stage

Save Agent judgments before opening any benchmark reference:

```json
{
  "schema_version": 1,
  "recognizer": "calling_agent",
  "evidence_mode": "raw_spectral_images",
  "events": [
    {"kind": "note", "track": "lead", "midi_pitch": 69,
     "start_seconds": 0.0, "end_seconds": 0.5},
    {"kind": "drum", "track": "drums", "drum": "snare",
     "start_seconds": 1.0, "end_seconds": 1.1}
  ]
}
```

These are sounding MIDI pitches, not transposed instrument notation. Optional
`instrument_id` records a judged identity; a label is not a playback assignment.
This experimental event record is not yet the unified notation/performance plan.
Resolve uncertainty using source/context and produce the best complete record;
there is no mandatory human note-review stage or repeated recognition pipeline.

For development tests only, compare predictions with separately held answers:

```bash
scorebridge evaluate-audio reference.json prediction.json --output report.json
```

It reports one-to-one pitch/onset matches, missed/extra events, separate release
timing, drums and supplied instrument identity. It does not certify a musical
result. Keep test provenance (known templates, synthetic versus sampled sources,
native-audio versus spectral input) with results.

## Delivery

Use existing MuseScore command plans to write Agent-recognized music when
requested. Automatic conversion of audio events to notation, multi-track MIDI
and DAW projects belongs to the next development stages. Do not present evidence
preparation as completed transcription or native-project generation.
