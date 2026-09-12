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
