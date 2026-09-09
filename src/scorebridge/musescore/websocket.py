"""Optional bridge to MuseScore QML/WebSocket MCP plugins."""
from __future__ import annotations

import asyncio
import json
import os
from typing import Any, Dict, Optional


class MuseScoreWebSocketError(RuntimeError):
    pass


class MuseScoreWebSocketBackend:
    name = "websocket"

    def __init__(self, url: Optional[str] = None, timeout: float = 8.0):
        self.url = url or os.environ.get("SCOREBRIDGE_MUSESCORE_WS", "ws://localhost:8765")
        self.timeout = timeout

    async def _send_async(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            import websockets
        except ImportError as exc:
            raise MuseScoreWebSocketError("Install with: pip install -e '.[websocket]'") from exc
        try:
            async with websockets.connect(self.url, open_timeout=self.timeout, close_timeout=self.timeout) as socket:
                await socket.send(json.dumps({"action": action, "params": params}))
                raw = await asyncio.wait_for(socket.recv(), timeout=self.timeout)
                result = json.loads(raw)
                return result if isinstance(result, dict) else {"result": result}
        except Exception as exc:
            raise MuseScoreWebSocketError(f"MuseScore WebSocket unavailable at {self.url}: {exc}") from exc

    def command(self, action: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return asyncio.run(self._send_async(action, params or {}))

    def status(self) -> dict:
        try:
            result = self.command("ping")
            return {"available": True, "backend": self.name, "url": self.url, "response": result}
        except MuseScoreWebSocketError as exc:
            return {"available": False, "backend": self.name, "url": self.url, "error": str(exc),
                    "hint": "Enable a compatible MuseScore QML/WebSocket plugin and keep MuseScore open."}
