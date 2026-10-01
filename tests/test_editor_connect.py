from scorebridge.musescore import connect


def test_connection_check_never_controls_a_screen(monkeypatch):
    class Bridge:
        def status(self):return {'available':False}
    monkeypatch.setattr(connect,'MuseScoreWebSocketBackend',lambda **kw:Bridge())
    report=connect.connect_editor()
    assert report['status']=='needs_live_plugin'
    assert report['computer_use'] is False
    assert 'build-score' in report['next']


def test_existing_live_connection_is_reused(monkeypatch):
    class Bridge:
        def status(self):return {'available':True}
    monkeypatch.setattr(connect,'MuseScoreWebSocketBackend',lambda **kw:Bridge())
    assert connect.connect_editor()['activation']=='already_running'


TARGET={'targetId':'sb-1','scoreName':'target','title':'Target','numMeasures':5,'numStaves':2}
class Bridge:
    def __init__(self,identity,available=True):self.identity=identity;self.available=available;self.calls=[]
    def status(self):return {'available':self.available}
    def command(self,action,params=None):self.calls.append(action);return {'result':self.identity}


def test_exact_binding_or_wrong_listener_never_writes(tmp_path):
    path=tmp_path/'target.mscz';path.write_bytes(b'score')
    bridge=Bridge(TARGET)
    assert connect.bind_editor_score(str(path),TARGET,bridge=bridge)['status']=='bound'
    wrong=Bridge({**TARGET,'scoreName':'wrong'})
    assert connect.bind_editor_score(str(path),TARGET,bridge=wrong)['status']=='wrong_target'
    assert bridge.calls==wrong.calls==['getScoreIdentity']


def test_missing_listener_never_launches_uncontrolled_gui(tmp_path):
    path=tmp_path/'target.mscz';path.write_bytes(b'score')
    class Adapter:
        def launch_score_process(self,path):raise AssertionError('GUI launched')
    report=connect.bind_editor_score(str(path),TARGET,bridge=Bridge(TARGET,False),adapter=Adapter())
    assert report['status']=='needs_live_plugin' and report['computer_use'] is False


def test_identity_rejects_invalid_target():
    assert 'target' in connect.identity_mismatches({**TARGET,'targetId':''},{})
