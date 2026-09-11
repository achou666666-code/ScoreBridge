import argparse, json
from pathlib import Path
from scorebridge.doctor import diagnose
from scorebridge.score_ir import load_score
from scorebridge.musicxml import compile_musicxml
from scorebridge.validation import validate_score

def main():
    parser=argparse.ArgumentParser(prog="scorebridge", description="Compile and validate Agent-readable music scores")
    sub=parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor")
    prepare=sub.add_parser("prepare"); prepare.add_argument("input"); prepare.add_argument("--output", required=True)
    prepare.add_argument("--dpi", type=int, default=450)
    sub.add_parser("editor-status")
    open_score = sub.add_parser("open-score")
    open_score.add_argument("input")
    open_score.add_argument("--executable", default="")
    execute=sub.add_parser("execute-plan"); execute.add_argument("input"); execute.add_argument("--url", default="")
    validate=sub.add_parser("validate"); validate.add_argument("input")
    compile_cmd=sub.add_parser("compile"); compile_cmd.add_argument("input"); compile_cmd.add_argument("--output", required=True)
    args=parser.parse_args()
    if args.command == "doctor":
        report = diagnose(); print(json.dumps(report, ensure_ascii=False, indent=2)); raise SystemExit(0 if report["status"] == "pass" else 1)
    if args.command == "prepare":
        from .agent_workflow import prepare_agent_job
        print(json.dumps(prepare_agent_job(args.input, args.output, args.dpi), ensure_ascii=False, indent=2)); return
    if args.command == "editor-status":
        from .musescore import MuseScoreWebSocketBackend
        report = MuseScoreWebSocketBackend().status()
        print(json.dumps(report, ensure_ascii=False, indent=2)); raise SystemExit(0 if report["available"] else 1)
    if args.command == "open-score":
        from .musescore import MuseScoreAdapter, MuseScoreError
        try:
            report = MuseScoreAdapter(executable=args.executable or None).open_score(args.input)
        except MuseScoreError as exc:
            print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False, indent=2))
            raise SystemExit(1)
        print(json.dumps(report, ensure_ascii=False, indent=2)); return
    if args.command == "execute-plan":
        from .agent_workflow import execute_plan_file
        report = execute_plan_file(args.input, args.url)
        print(json.dumps(report, ensure_ascii=False, indent=2)); raise SystemExit(0 if report["status"] == "executed" else 1)
    score=load_score(args.input); report=validate_score(score)
    if args.command=="validate": print(json.dumps(report, ensure_ascii=False, indent=2)); raise SystemExit(0 if report["status"]=="pass" else 1)
    if report["status"]!="pass": print(json.dumps(report, ensure_ascii=False, indent=2)); raise SystemExit(1)
    output=compile_musicxml(score,args.output); print(json.dumps({"status":"pass","output":str(output.resolve())},ensure_ascii=False))
