"""Agent-owned transcription preparation and explicit editor command plans.

No recognition engine runs here. The calling multimodal Agent reads the evidence.
"""
from pathlib import Path
import json

from .input import prepare_input
from .musescore import MuseScoreWebSocketBackend, MuseScoreWebSocketError


def prepare_agent_job(input_path, output_dir, dpi=450):
    evidence = prepare_input(input_path, str(Path(output_dir) / "evidence"), dpi=dpi)
    if evidence.get("status") != "pass":
        return evidence
    return {"status": "awaiting_agent", "stage": "read_source", "input": evidence,
            "recognizer": "calling_agent", "omr_used": False,
            "delivery_format": "mscz",
            "next": "Read the source images, organize score content, then execute editor commands. No user review is required."}


def execute_plan(plan, backend=None):
    """Execute a small, ordered edit batch; report partial progress, never replay it.

    This is not an atomic transaction. On timeout the failed command may have
    applied: read editor state before deciding how to continue.
    """
    steps = plan.get("steps") if isinstance(plan, dict) else None
    if not isinstance(steps, list) or not steps:
        return {"status": "error", "error": "plan.steps must be a nonempty list"}
    ids = set()
    for i, step in enumerate(steps):
        if (not isinstance(step, dict) or not isinstance(step.get("id"), str)
                or not step["id"] or step["id"] in ids
                or not isinstance(step.get("action"), str) or not step["action"]
                or not isinstance(step.get("params", {}), dict)):
            return {"status": "error", "failed_index": i,
                    "error": "Each step needs a unique string id, action, and object params"}
        ids.add(step["id"])
    bridge = backend or MuseScoreWebSocketBackend()
    completed = []
    for step in steps:
        try:
            response = bridge.command(step["action"], step.get("params", {}))
        except MuseScoreWebSocketError as exc:
            return {"status": "incomplete", "completed": completed,
                    "failed_step": step["id"], "error": str(exc),
                    "next": "Read editor state before continuing; do not replay the whole plan."}
        completed.append({"id": step["id"], "response": response})
    return {"status": "executed", "completed": completed,
            "verification": "Command acknowledgements only; not source accuracy or playback verification."}


def execute_plan_file(input_path, url=""):
    return execute_plan(json.loads(Path(input_path).read_text(encoding="utf-8")),
                        MuseScoreWebSocketBackend(url=url or None))
