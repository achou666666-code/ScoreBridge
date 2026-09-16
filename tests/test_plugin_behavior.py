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


@pytest.mark.parametrize('written,diatonic,chromatic,concert', [
    (-3, 0, 0, -3), (-1, -1, -2, -3), (-2, -4, -7, -3),
    (2, -1, -2, 0), (0, -7, -12, 0), (-7, -1, -2, 3), (7, 1, 2, -3),
])
def test_written_key_conversion(written, diatonic, chromatic, concert):
    args = json.dumps({'diatonic': diatonic, 'chromatic': chromatic})
    assert run_function('writtenToConcertKey', '', f'writtenToConcertKey({written}, {args})') == concert


@pytest.mark.parametrize('params', [None, {}, {'fifths': 8}, {'fifths': -8},
    {'fifths': 0.5}, {'fifths': '2'}, {'fifths': 0, 'staff': -1, 'measure': 1},
    {'fifths': 0, 'staff': 5, 'measure': 1}, {'fifths': 0, 'staff': 0, 'measure': 0},
])
def test_invalid_key_request_does_not_enter_editor(params):
    result = run_function('setKeySignature', 'var curScore={nstaves:5};',
                          'setKeySignature(' + json.dumps(params) + ')')
    assert result['error']


@pytest.mark.parametrize('existing,changed', [
    (None, True),
    ({'type': 1, 'concertKey': -3, 'actualKey': -1}, True),
    ({'type': 1, 'concertKey': 0, 'actualKey': 2}, False),
])
def test_key_replaces_only_target_and_is_idempotent(existing, changed):
    setup = '''
var Element={KEYSIG:1}, existing=EXISTING, removed=[], added=[], undoCalls=0;
var target={tick:1920,next:null,elementAt(track){return track===4 ? existing : null;}};
var cursor={tick:0,segment:{tick:0},fraction:{},measure:{firstSegment:null},
  nextMeasure(){this.tick=1920;this.segment=target;this.measure.firstSegment=target;return true;},
  add(k){added.push(k);}};
var curScore={nstaves:2,style:{value(){return false;}},staves:[{}, {transpose(){return {diatonic:-1,chromatic:-2};}}]};
function createCursor(p){if(p.startStaff!==1)throw Error('wrong staff');return cursor;}
function writtenToConcertKey(k,i){return k-2;}
function executeWithUndo(f){undoCalls++;return f();}
function removeElement(e){removed.push(e);}
function newElement(){return {};}
'''.replace('EXISTING', json.dumps(existing))
    result = run_function('setKeySignature', setup,
        '({report:setKeySignature({staff:1,measure:2,fifths:2}),removed:removed,added:added,undoCalls:undoCalls})')
    assert result['report']['changed'] is changed
    assert result['report']['writtenFifths'] == 2
    assert result['report']['concertFifths'] == 0
    assert result['undoCalls'] == int(changed)
    assert result['removed'] == ([existing] if existing and changed else [])
    assert result['added'] == ([{'concertKey': 0, 'actualKey': 2}] if changed else [])


def test_key_requires_written_display():
    setup = 'var curScore={nstaves:1,style:{value(){return true;}}};'
    assert 'concert pitch' in run_function('setKeySignature', setup,
        'setKeySignature({staff:0,measure:1,fifths:0})')['error']


@pytest.mark.parametrize('params', [None, {}, {'widthMm': '210'},
    {'widthMm': -1}, {'widthMm': float('inf')},
    dict(widthMm=210, heightMm=297, leftMm=110, rightMm=110, topMm=20, bottomMm=16),
    dict(widthMm=210, heightMm=297, leftMm=18, rightMm=12, topMm=150, bottomMm=147),
])
def test_invalid_page_settings_never_enter_edit(params):
    assert run_function('setPageLayout', 'var curScore={};',
        'setPageLayout(' + json.dumps(params) + ')')['error']


def test_page_settings_convert_millimeters_and_update_both_page_margins():
    setup = '''
var values={};
var curScore={style:{setValue(k,v){values[k]=v;},value(k){return values[k];}}};
function executeWithUndo(f){return f();}
function getPageLayout(){return {};}
'''
    result = run_function('setPageLayout', setup,
        '({report:setPageLayout({widthMm:210,heightMm:297,leftMm:18,rightMm:12,topMm:20,bottomMm:16}),values:values})')
    assert result['report']['success'] is True
    expected = dict(pageWidth=210, pageHeight=297, pagePrintableWidth=180,
        pageOddLeftMargin=18, pageEvenLeftMargin=18,
        pageOddTopMargin=20, pageEvenTopMargin=20,
        pageOddBottomMargin=16, pageEvenBottomMargin=16)
    assert result['values'] == pytest.approx({k: v/25.4 for k, v in expected.items()})


def test_page_write_mismatch_is_not_reported_as_success():
    setup = '''
var curScore={style:{setValue(){},value(){return 0;}}};
function executeWithUndo(f){try{return f();}catch(e){return {error:String(e)};}}
'''
    assert run_function('setPageLayout', setup,
        'setPageLayout({widthMm:210,heightMm:297,leftMm:18,rightMm:12,topMm:20,bottomMm:16})')['error']


@pytest.mark.parametrize('existing,kind,changed,expected', [
    ([], 'page', True, [0]), ([0], 'page', False, [0]),
    ([0], 'line', True, [1]), ([1], 'none', True, []),
    ([], 'none', False, []), ([0, 1], 'page', True, [0]),
])
def test_layout_break_replacement_deduplication_and_removal(existing, kind, changed, expected):
    setup = '''
var Element={LAYOUT_BREAK:1}, LayoutBreak={PAGE:0,LINE:1,SECTION:2};
var untouched={type:99};
var measure={elements:EXISTING.map(t=>({type:1,layoutBreakType:t})).concat([untouched]),
remove(e){this.elements.splice(this.elements.indexOf(e),1);},add(e){this.elements.push(e);}};
var curScore={};
function createCursor(){return {measure:measure};}
function executeWithUndo(f){return f();}
function newElement(t){return {type:t};}
'''.replace('EXISTING', json.dumps(existing))
    result = run_function('setLayoutBreak', setup,
        '({report:setLayoutBreak(' + json.dumps({'measure':1,'type':kind}) + '),elements:measure.elements})')
    assert result['report']['changed'] is changed
    assert [e['layoutBreakType'] for e in result['elements'] if e['type']==1] == expected
    assert {'type':99} in result['elements']


def test_section_break_is_preserved():
    setup = '''
var Element={LAYOUT_BREAK:1}, LayoutBreak={SECTION:2}, curScore={};
function createCursor(){return {measure:{elements:[{type:1,layoutBreakType:2}]}};}
'''
    assert 'section break' in run_function('setLayoutBreak', setup,
        'setLayoutBreak({measure:1,type:"page"})')['error']


def test_layout_commands_dispatch_in_sequence():
    result = run_function('processSequence',
        'var curScore={},selectionState={},calls=[];function processCommand(c){calls.push(c.action);return {success:true};}',
        '({report:processSequence({sequence:[{action:"setPageLayout"},{action:"setLayoutBreak"},{action:"save"},{action:"getPageLayout"}]}),calls:calls})')
    assert result['calls'] == ['setPageLayout', 'setLayoutBreak', 'save', 'getPageLayout']
    assert result['report']['completedIndices'] == [0, 1, 2, 3]
