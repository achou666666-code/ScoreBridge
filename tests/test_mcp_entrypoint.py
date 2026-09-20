import asyncio
import importlib.util
from pathlib import Path
import pytest


def test_server_exposes_agent_default():
    pytest.importorskip('mcp')
    spec = importlib.util.spec_from_file_location('scorebridge_mcp_test', Path(__file__).parents[1] / 'mcp_server/server.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    tools = {t.name: t for t in asyncio.run(module.mcp.list_tools())}
    assert tools['score_transcribe'].inputSchema['properties']['mode']['default'] == 'agent'
    assert 'musescore_execute_plan' in tools
    assert 'musescore_create_score' in tools
    assert tools['musescore_create_score'].inputSchema['properties']['open_editor']['default'] is True
