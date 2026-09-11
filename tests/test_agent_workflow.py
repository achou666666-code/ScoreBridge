from scorebridge.agent_workflow import execute_plan, prepare_agent_job
from scorebridge.musescore import MuseScoreWebSocketError


def test_prepare_never_runs_omr(tmp_path, monkeypatch):
    from PIL import Image
    import scorebridge.omr
    monkeypatch.setattr(scorebridge.omr, 'run_omr', lambda *a, **k: (_ for _ in ()).throw(AssertionError('OMR called')))
    source = tmp_path / 'page.png'
    Image.new('RGB', (300, 200), 'white').save(source)
    result = prepare_agent_job(str(source), str(tmp_path / 'job'), dpi=100)
    assert result['status'] == 'awaiting_agent'
    assert result['omr_used'] is False
    assert result['input']['pages']


class Bridge:
    def __init__(self): self.calls = []
    def command(self, action, params):
        self.calls.append(action)
        if action == 'fail': raise MuseScoreWebSocketError('timeout')
        return {'result': 'ok'}


def test_plan_stops_without_retry_or_later_writes():
    bridge = Bridge()
    result = execute_plan({'steps': [{'id': str(i), 'action': a} for i, a in enumerate(['first', 'fail', 'last'])]}, bridge)
    assert result['status'] == 'incomplete'
    assert result['failed_step'] == '1'
    assert [x['id'] for x in result['completed']] == ['0']
    assert bridge.calls == ['first', 'fail']


def test_plan_prevalidates_all_steps_before_writing():
    bridge = Bridge()
    result = execute_plan({'steps': [{'id': 'same', 'action': 'a'}, {'id': 'same', 'action': 'b'}]}, bridge)
    assert result['status'] == 'error'
    assert bridge.calls == []


def test_create_and_save_example_plan_is_ordered():
    import json
    from pathlib import Path
    plan = json.loads((Path(__file__).parents[1] / "examples/create-and-save-plan.json").read_text())
    bridge = Bridge()
    result = execute_plan(plan, bridge)
    assert result["status"] == "executed"
    assert bridge.calls == ["createScore", "setTimeSignature", "setTempo", "addNote", "saveAs"]
