# Image To Score Demo

This is the first reproducible image-to-editable-score demo. The input is normalized into a source-linked evidence package before OMR.

Prepare any PDF, image, or naturally sorted image directory:

```bash
.venv/bin/python - <<'PY'
from scorebridge.input import prepare_input
print(prepare_input("demos/image-to-score/public-samples/twinkle-twinkle-cc0.png",
                    "demos/image-to-score/output/twinkle-evidence", dpi=450))
PY
```

Run it from the repository root:

```bash
.venv/bin/python tests/make_fixture.py
.venv/bin/scorebridge validate examples/vertical-slice.score.json
.venv/bin/scorebridge compile examples/vertical-slice.score.json --output examples/vertical-slice.musicxml
```

Open the resulting MusicXML in MuseScore and save it as MSCZ. Later this directory will contain the input image, generated IR, output files, screenshots, and the recorded walkthrough.

## Public PNG smoke tests

The `public-samples/` directory contains openly licensed raster scores. Run one through the full OMR path:

```bash
out="$(mktemp -d /tmp/scorebridge-omr.XXXXXX)"
.venv/bin/python - "$out" <<'PY'
import sys
from scorebridge.omr.pipeline import run_omr
print(run_omr("demos/image-to-score/public-samples/twinkle-twinkle-cc0.png", sys.argv[1]))
PY
```

The pipeline first tries a contrast-enhanced image and automatically retries the original raster when preprocessing hurts recognition. This matters for older 1-bit scans such as the Chester sample.

The checked-in smoke run is under `output/twinkle-run/`: it includes the manifest, source/rendered/enhanced page evidence, Audiveris output, Score IR, and MuseScore MSCZ/MusicXML round-trip.
