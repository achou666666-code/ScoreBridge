"""Diagnosable MuseScore process adapter."""
from dataclasses import dataclass
from pathlib import Path
import os
import shutil
import subprocess
from typing import Optional
from zipfile import BadZipFile, ZipFile

class MuseScoreError(RuntimeError):
    pass


class MuseScoreBackend:
    """Small backend contract shared by CLI and future MCP adapters."""

    name = "base"

    def status(self) -> dict:
        raise NotImplementedError

    def convert(self, input_path: str, output_path: str) -> dict:
        raise NotImplementedError

@dataclass
class MuseScoreAdapter(MuseScoreBackend):
    executable: Optional[str] = None
    timeout: int = 90
    name: str = "cli"

    def resolve(self) -> Optional[Path]:
        candidates = [self.executable] if self.executable else [os.environ.get("MUSESCORE_BIN")]
        candidates += [shutil.which("mscore"), shutil.which("MuseScore"), "/Applications/MuseScore 4.app/Contents/MacOS/mscore"]
        for candidate in candidates:
            if candidate and Path(candidate).exists():
                return Path(candidate)
        return None

    def status(self) -> dict:
        exe = self.resolve()
        return {"available": bool(exe), "executable": str(exe) if exe else None, "backend": "cli" if exe else None,
                "hint": None if exe else "Install MuseScore 4 or set MUSESCORE_BIN."}

    @staticmethod
    def _valid_output(path: Path) -> bool:
        if not path.is_file() or path.stat().st_size == 0:
            return False
        if path.suffix.lower() != ".mscz":
            return True
        try:
            with ZipFile(path) as archive:
                return archive.testzip() is None and any(
                    name.lower().endswith(".mscx") for name in archive.namelist()
                )
        except (BadZipFile, OSError):
            return False

    def convert(self, input_path: str, output_path: str) -> dict:
        exe = self.resolve()
        if not exe:
            raise MuseScoreError(self.status()["hint"])
        src, dst = Path(input_path), Path(output_path)
        if not src.exists():
            raise MuseScoreError(f"Input does not exist: {src}")
        dst.parent.mkdir(parents=True, exist_ok=True)
        env = os.environ.copy()
        # MuseScore's macOS bundle ships only the cocoa Qt platform plugin.
        # Leave platform selection untouched unless the caller explicitly set it.
        try:
            proc = subprocess.run([str(exe), "-o", str(dst), str(src)], capture_output=True, text=True, timeout=self.timeout, env=env)
        except subprocess.TimeoutExpired as exc:
            raise MuseScoreError(f"MuseScore timed out after {self.timeout}s") from exc
        result = {"command": [str(exe), "-o", str(dst), str(src)], "returncode": proc.returncode, "stdout": proc.stdout[-4000:], "stderr": proc.stderr[-4000:], "output_path": str(dst.resolve())}
        output_valid = self._valid_output(dst)
        if proc.returncode != 0 and output_valid:
            result["warning"] = f"MuseScore exited with code {proc.returncode} after writing a valid output file"
            result["output_valid"] = True
            return result
        if proc.returncode != 0 or not output_valid:
            detail = proc.stderr[-1000:].strip()
            if proc.returncode < 0:
                detail = f"process terminated by signal {-proc.returncode}; {detail}"
            raise MuseScoreError(f"MuseScore conversion failed (code {proc.returncode}): {detail}")
        result["output_valid"] = True
        return result
