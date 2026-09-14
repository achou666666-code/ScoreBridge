"""Run the plugin's actual JavaScript functions with a small editor double."""
import json
from pathlib import Path
import re
import shutil
import subprocess

import pytest


def run_function(name, setup, expression):
    node = shutil.which('node')
    if not node:
        pytest.skip('Node.js required for plugin JavaScript behavior tests')
    source = (Path(__file__).parents[1] / 'plugins/musescore-mcp-websocket.qml').read_text()
    function = re.search(r'    function ' + name + r'\(.*?\n    }', source, re.S).group()
    result = subprocess.run([node, '-e', setup + '\n' + function + '\nconsole.log(JSON.stringify(' + expression + '));'], capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


@pytest.mark.parametrize('failure', [{'error': 'bad duration'}, {'valid': False}, {'success': False}])
def test_sequence_stops_at_returned_failure(failure):
    result = run_function('processSequence',
        'var curScore={}, selectionState={}, calls=[]; function processCommand(c) { calls.push(c.action); return calls.length===2 ? ' + json.dumps(failure) + ' : {success:true}; }',
        '({report:processSequence({sequence:[{action:"addNote"},{action:"addRest"},{action:"save"}]}),calls:calls})')
    assert result['calls'] == ['addNote', 'addRest']
    assert result['report']['failedIndex'] == 1
    assert result['report']['completedIndices'] == [0]
    assert result['report']['error']


def test_sequence_rejects_non_array():
    result = run_function('processSequence', 'var curScore={};', 'processSequence({sequence:{}})')
    assert result['error'] == 'Sequence must be an array'


def test_range_does_not_report_excluded_staff():
    result = run_function('selectCustomRange', '''
var selectionState={}, queried=[];
var curScore={selection:{clear(){},selectRange(){}}};
function validateParams(){return {valid:true};}
function executeWithUndo(f){return f();}
var segment={tick:0,next:null,elementAt(t){queried.push(t);return null;}};
function createCursor(){return {rewind(){},segment:segment};}
''', '({report:selectCustomRange({startTick:0,endTick:480,startStaff:0,endStaff:1}),queried:queried})')
    assert list(result['report']['currentSelection']['elements']) == ['staff0']
    assert result['queried'] == [0, 1, 2, 3]


def test_dynamic_sets_semantic_type_instead_of_plain_text():
    result = run_function('addDynamic', '''
var DynamicType={PP:6}, Element={DYNAMIC:1}, selectionState={startTick:0,startStaff:0}, inserted=[];
function validateParams(){return {valid:true};}
function executeWithUndo(f){return f();}
function syncStateToSelection(){}
function newElement(){return {};}
function createCursor(){return {add(e){inserted.push(e);}};}
''', '({report:addDynamic({type:"pp"}),inserted:inserted})')
    assert result['report']['success'] is True
    assert result['inserted'] == [{'dynamicType': 6, 'text': '<sym>dynamicPiano</sym><sym>dynamicPiano</sym>'}]


def test_dynamic_rejects_missing_parameters():
    assert run_function('addDynamic', '', 'addDynamic(null)')['error']


def test_sequence_dispatches_position_markings_and_save_in_order():
    actions = ['selectCustomRange', 'addDynamic', 'addTechniqueText', 'save']
    sequence = [
        {'action': actions[0], 'params': {'startTick': 1920, 'endTick': 2400, 'startStaff': 0, 'endStaff': 1}},
        {'action': actions[1], 'params': {'type': 'mp'}},
        {'action': actions[2], 'params': {'text': 'solo'}},
        {'action': actions[3], 'params': {}},
    ]
    result = run_function('processSequence',
        'var curScore={}, selectionState={}, calls=[]; function processCommand(c) { calls.push(c); return {success:true}; }',
        '({report:processSequence(' + json.dumps({'sequence': sequence}) + '),calls:calls})')
    assert result['calls'] == sequence
    assert result['report']['success'] is True
    assert result['report']['completedIndices'] == [0, 1, 2, 3]


@pytest.mark.parametrize('tracks,staff_end,min_chords,single_voice,valid', [
    ([0, 0], 1, 2, True, True),
    ([0], 1, 1, False, True),
    ([], 1, 1, False, False),
    ([0], 1, 2, True, False),
    ([0, 0], 2, 1, False, False),
    ([0, 1], 1, 2, True, False),
])
def test_notation_range_checks_actual_chords(tracks, staff_end, min_chords, single_voice, valid):
    setup = """
var Element={CHORD:1};
var tracks=TRACKS;
var end={tick:1920};
var segments=tracks.map((v,i)=>({tick:i*480,elementAt(t){return t===v ? {type:1} : null;}}));
segments.forEach((s,i)=>s.next=segments[i+1]||end);
var start=segments[0]||{tick:0,next:end,elementAt(){return null;}};
var curScore={selection:{startSegment:start,endSegment:end,startStaff:0,endStaff:STAFF_END}};
""".replace('TRACKS', json.dumps(tracks)).replace('STAFF_END', str(staff_end))
    result = run_function('validateNotationRange', setup,
                          f'validateNotationRange({min_chords}, {str(single_voice).lower()})')
    assert (result.get('valid') is True) is valid
    if not valid:
        assert result['error']


@pytest.mark.parametrize('setup', [
    'var curScore=null;',
    'var curScore={selection:{}};',
    'var curScore={selection:{startSegment:{tick:480},endSegment:{tick:480}}};',
])
def test_notation_requires_open_score_and_nonempty_range(setup):
    assert run_function('validateNotationRange', setup, 'validateNotationRange(1, false)')['error']


@pytest.mark.parametrize('kind', ['toString', 'constructor', 'unsupported'])
def test_articulation_rejects_unsupported_action_before_dispatch(kind):
    result = run_function('addArticulation',
        'function validateParams(){return {valid:true};}',
        'addArticulation(' + json.dumps({'type':kind}) + ')')
    assert result['error'].startswith('Unsupported articulation:')


@pytest.mark.parametrize('name,params', [('addArticulation', {'type':'staccato'}), ('addSlur', {})])
def test_notation_rejection_never_dispatches_editor_action(name, params):
    result = run_function(name,
        'function validateParams(){return {valid:true};} function validateNotationRange(){return {error:"bad range"};} function executeWithUndo(){throw Error("must not edit");}',
        name + '(' + json.dumps(params) + ')')
    assert result == {'error': 'bad range'}


def test_sequence_accepts_articulation_and_slur():
    result = run_function('processSequence',
        'var curScore={}, selectionState={}, calls=[]; function processCommand(c){calls.push(c.action);return {success:true};}',
        '({report:processSequence({sequence:[{action:"addArticulation",params:{type:"staccato"}},{action:"addSlur"},{action:"save"}]}),calls:calls})')
    assert result['calls'] == ['addArticulation', 'addSlur', 'save']
    assert result['report']['completedIndices'] == [0, 1, 2]
