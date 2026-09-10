"""Diagnosable MuseScore process adapter."""
from dataclasses import dataclass
from pathlib import Path
import os
import shutil
import subprocess
import tempfile
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
        if self.executable:
            explicit = Path(self.executable)
            return explicit if explicit.is_file() else None
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
        src, dst = Path(input_path), Path(output_path)
        if not src.exists():
            raise MuseScoreError(f"Input does not exist: {src}")
        exe = self.resolve()
        if not exe:
            raise MuseScoreError(self.status()["hint"])
        dst.parent.mkdir(parents=True, exist_ok=True)
        env = os.environ.copy()
        # MuseScore's macOS bundle ships only the cocoa Qt platform plugin.
        # Leave platform selection untouched unless the caller explicitly set it.
        # Generate into an empty location: an old valid destination must never
        # turn a failed export into a false success. Publish only verified output.
        with tempfile.TemporaryDirectory(prefix="scorebridge-", dir=dst.parent) as temporary:
            generated = Path(temporary) / dst.name
            try:
                proc = subprocess.run([str(exe), "-o", str(generated), str(src.resolve())], capture_output=True, text=True, timeout=self.timeout, env=env)
            except subprocess.TimeoutExpired as exc:
                raise MuseScoreError(f"MuseScore timed out after {self.timeout}s") from exc
            result = {"command": [str(exe), "-o", str(generated), str(src.resolve())], "returncode": proc.returncode, "stdout": proc.stdout[-4000:], "stderr": proc.stderr[-4000:], "output_path": str(dst.resolve())}
            if not self._valid_output(generated):
                detail = proc.stderr[-1000:].strip()
                raise MuseScoreError(f"MuseScore conversion failed (code {proc.returncode}): {detail}")
            if proc.returncode != 0:
                result["warning"] = f"MuseScore exited with code {proc.returncode} after writing a valid output file"
            generated.replace(dst)
            result["output_valid"] = True
            return result
