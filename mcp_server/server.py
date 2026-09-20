"""ScoreBridge MCP entry point. Install with `pip install -e '.[mcp]'`."""
import json
from pathlib import Path
from typing import Optional
from scorebridge.score_ir import load_score
from scorebridge.musicxml import compile_musicxml
from scorebridge.validation import validate_score
from scorebridge.musescore import MuseScoreAdapter, MuseScoreError, MuseScoreWebSocketBackend, MuseScoreWebSocketError, create_seed_score
from scorebridge.patches import apply_patch
from scorebridge.score_ir import save_score
from scorebridge.input import classify_page, inspect_input, prepare_image, prepare_input
from scorebridge.omr import OMRAdapter, run_omr
from scorebridge.musicxml import parse_musicxml
from scorebridge.review import create_review_packet, apply_review
from scorebridge.finalize import finalize_score
from scorebridge.workflow import transcribe_score
from scorebridge.doctor import diagnose
from scorebridge.instrument_audit import audit_instruments
from scorebridge.agent_workflow import prepare_agent_job, execute_plan_file

try:
    from mcp.server.fastmcp import FastMCP
except ImportError as exc:
    raise SystemExit("Install ScoreBridge with the mcp extra: pip install -e '.[mcp]'") from exc

mcp = FastMCP("ScoreBridge")

@mcp.tool()
def musescore_connect() -> dict:
    """Activate the bundled plugin in an open macOS MuseScore and verify connection."""
    from scorebridge.musescore.connect import connect_editor
    return connect_editor()

@mcp.tool()
def scorebridge_doctor() -> dict:
    """Check Python, image, OMR, MuseScore and MCP dependencies."""
    return diagnose()

@mcp.tool()
def score_validate(input_path: str) -> dict:
    """Validate a Score IR JSON file before it is sent to notation software."""
    return validate_score(load_score(input_path))

@mcp.tool()
def score_compile(input_path: str, output_path: str, allow_issues: bool = False) -> dict:
    """Compile a validated Score IR JSON document to editable MusicXML."""
    score=load_score(input_path); report=validate_score(score)
    if report["status"] != "pass" and not allow_issues: return report
    output=compile_musicxml(score, output_path)
    return {"status":"pass" if report["status"] == "pass" else "needs_review", "output_path":str(output.resolve()), "validation": report}

@mcp.tool()
def score_inspect(input_path: str) -> dict:
    """Return the score title, pitch mode, parts, staves and measure counts."""
    score=load_score(input_path)
    return {"title":score.title,"pitch_mode":score.pitch_mode,"parts":[{"id":p.id,"name":p.name,"instrument_id":p.instrument_id,"staves":len(p.staves),"measures":[len(s.measures) for s in p.staves]} for p in score.parts]}

@mcp.tool()
def score_instrument_audit(input_path: str) -> dict:
    """Audit every part's instrument mapping before MuseScore export."""
    return audit_instruments(load_score(input_path))

@mcp.tool()
def score_apply_patch(input_path: str, patch: dict, output_path: str = "") -> dict:
    """Apply one validated, high-level edit without mutating the input file."""
    score = load_score(input_path)
    updated, report = apply_patch(score, patch)
    if report["status"] != "pass":
        return report
    destination = output_path or input_path
    save_score(updated, destination)
    return {**report, "output_path": str(Path(destination).resolve())}

@mcp.tool()
def musescore_status() -> dict:
    """Detect a local MuseScore executable and report the available backend."""
    return MuseScoreAdapter().status()

@mcp.tool()
def musescore_open(input_path: str, executable: str = "") -> dict:
    """Open an existing MSCZ or MusicXML file in MuseScore."""
    try:
        return MuseScoreAdapter(executable=executable or None).open_score(input_path)
    except (MuseScoreError, OSError) as exc:
        return {"status": "error", "error": str(exc)}

@mcp.tool()
def musescore_create_score(specification: dict, output_path: str, executable: str = "", open_editor: bool = True) -> dict:
    """Create a playable MSCZ scaffold from parts, meter and measure count, then optionally open it."""
    return create_seed_score(specification, output_path, executable, open_editor)

@mcp.tool()
def musescore_convert(input_path: str, output_path: str, executable: str = "") -> dict:
    """Convert MusicXML or MSCZ through MuseScore's command line exporter."""
    try:
        return {"status": "pass", **MuseScoreAdapter(executable=executable or None).convert(input_path, output_path)}
    except (MuseScoreError, TimeoutError) as exc:
        return {"status": "error", "error": str(exc)}

@mcp.tool()
def musescore_websocket_status(url: str = "") -> dict:
    """Check a running MuseScore QML/WebSocket plugin."""
    return MuseScoreWebSocketBackend(url=url or None).status()

@mcp.tool()
def musescore_websocket_command(action: str, params: Optional[dict] = None, url: str = "") -> dict:
    """Send one command to a compatible MuseScore plugin, such as getScore or addNote."""
    try:
        return {"status": "pass", "response": MuseScoreWebSocketBackend(url=url or None).command(action, params or {})}
    except MuseScoreWebSocketError as exc:
        return {"status": "error", "error": str(exc)}

@mcp.tool()
def score_build_mscz(input_path: str, musicxml_path: str, mscz_path: str, executable: str = "", allow_issues: bool = False) -> dict:
    """Validate Score IR, compile MusicXML, then ask MuseScore for an MSCZ."""
    score = load_score(input_path)
    report = validate_score(score)
    if report["status"] != "pass" and not allow_issues:
        return report
    xml = compile_musicxml(score, musicxml_path)
    try:
        converted = MuseScoreAdapter(executable=executable or None).convert(str(xml), mscz_path)
    except (MuseScoreError, TimeoutError) as exc:
        return {"status": "error", "stage": "musescore", "error": str(exc), "musicxml_path": str(xml.resolve())}
    return {"status": "pass" if report["status"] == "pass" else "needs_review", "musicxml_path": str(xml.resolve()), "mscz_path": converted["output_path"], "validation": report}

@mcp.tool()
def input_inspect(input_path: str) -> dict:
    """Inspect a PDF or raster score before OMR processing."""
    return inspect_input(input_path)

@mcp.tool()
def image_prepare(input_path: str, output_path: str, scale: int = 2) -> dict:
    """Upscale and clean a raster score image for a later OMR pass."""
    try:
        return prepare_image(input_path, output_path, scale)
    except (ImportError, ValueError, OSError) as exc:
        return {"status": "error", "error": str(exc)}

@mcp.tool()
def input_prepare(input_path: str, output_dir: str, dpi: int = 450, enhance: bool = True) -> dict:
    """Normalize a PDF, image, or image directory into a source-linked evidence package."""
    return prepare_input(input_path, output_dir, dpi=dpi, enhance=enhance)

@mcp.tool()
def page_classify(input_path: str) -> dict:
    """Conservatively classify a raster page as score, non-score, or uncertain."""
    try:
        return classify_page(input_path)
    except (ImportError, OSError, ValueError) as exc:
        return {"status": "error", "error": str(exc)}

@mcp.tool()
def omr_status() -> dict:
    """Report whether a local Audiveris OMR engine is available."""
    return OMRAdapter().status()

@mcp.tool()
def omr_run(input_path: str, output_dir: str, executable: str = "", scale: int = 2) -> dict:
    """Run the complete inspect -> prepare -> OMR -> Score IR pipeline."""
    return run_omr(input_path, output_dir, executable, scale)

@mcp.tool()
def musicxml_import(input_path: str, output_score_path: str = "") -> dict:
    """Import OMR-produced MusicXML into ScoreBridge's canonical Score IR."""
    try:
        score = parse_musicxml(input_path)
        destination = output_score_path or str(Path(input_path).with_suffix(".score.json"))
        save_score(score, destination)
        report = validate_score(score)
        return {"status": "pass" if report["status"] == "pass" else "needs_review", "output_path": str(Path(destination).resolve()), "parts": len(score.parts), "validation": report}
    except (OSError, ValueError) as exc:
        return {"status": "error", "error": str(exc)}

@mcp.tool()
def review_create(score_path: str, manifest_path: str = "", output_path: str = "") -> dict:
    """Create source-linked measure review tasks for an Agent."""
    return create_review_packet(score_path, manifest_path, output_path)

@mcp.tool()
def review_apply(score_path: str, decisions_path: str, output_path: str = "") -> dict:
    """Apply Agent review decisions and keep rejected tasks in the report."""
    return apply_review(score_path, decisions_path, output_path)

@mcp.tool()
def score_finalize(score_path: str, output_dir: str, executable: str = "", allow_issues: bool = True) -> dict:
    """Deliver MSCZ only; keep compilation and structural audit files internal."""
    return finalize_score(score_path, output_dir, executable, allow_issues)

@mcp.tool()
def score_transcribe(input_path: str, output_dir: str, decisions_path: str = "", audiveris: str = "", musescore: str = "", dpi: int = 450, mode: str = "agent") -> dict:
    """Prepare source images for the calling Agent. OMR requires explicit mode='omr'."""
    if mode == "agent":
        return prepare_agent_job(input_path, output_dir, dpi)
    if mode == "omr":
        return transcribe_score(input_path, output_dir, decisions_path, audiveris, musescore, dpi)
    return {"status": "error", "error": "mode must be agent or omr"}

@mcp.tool()
def musescore_execute_plan(input_path: str, url: str = "") -> dict:
    """Execute ordered Agent editor commands; return completed IDs on partial failure."""
    return execute_plan_file(input_path, url)

if __name__ == "__main__": mcp.run()
