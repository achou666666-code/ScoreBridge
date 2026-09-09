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
    validate=sub.add_parser("validate"); validate.add_argument("input")
    compile_cmd=sub.add_parser("compile"); compile_cmd.add_argument("input"); compile_cmd.add_argument("--output", required=True)
    args=parser.parse_args()
    if args.command == "doctor":
        report = diagnose(); print(json.dumps(report, ensure_ascii=False, indent=2)); raise SystemExit(0 if report["status"] == "pass" else 1)
    score=load_score(args.input); report=validate_score(score)
    if args.command=="validate": print(json.dumps(report, ensure_ascii=False, indent=2)); raise SystemExit(0 if report["status"]=="pass" else 1)
    if report["status"]!="pass": print(json.dumps(report, ensure_ascii=False, indent=2)); raise SystemExit(1)
    output=compile_musicxml(score,args.output); print(json.dumps({"status":"pass","output":str(output.resolve())},ensure_ascii=False))
