import json
from test_plugin_behavior import run_function


def test_final_score_range_includes_last_chord_despite_clamped_end_segment():
    setup='''
var Element={CHORD:1};
var last={tick:8400,next:null,elementAt(t){return t===0?{type:1}:null;}};
var first={tick:8160,next:last,elementAt(t){return t===0?{type:1}:null;}};
var curScore={selection:{startSegment:first,endSegment:last,startStaff:0,endStaff:1}};
var selectionState={startTick:8160,totalDuration:480};
'''
    assert run_function('validateNotationRange',setup,'validateNotationRange(2,true)')=={'valid':True}


def test_tremolo_uses_running_musescore_enum_not_newer_version_integers():
    setup='''
var TremoloType={R8:0,R16:1,R32:2,R64:3,BUZZ_ROLL:4};
var Element={CHORD:1,TREMOLO_SINGLECHORD:2};
var chord={type:1,tremoloSingleChord:null,add(m){this.tremoloSingleChord=m;}};
function notationCursor(){return {element:chord};}
function executeWithUndo(f){return f();}
function newElement(){return {};}
'''
    result=run_function('addTremolo',setup,'addTremolo({staff:0,startTick:0,type:"buzz"})')
    assert result['success'] and result['tremoloType']==4


def test_percussion_rejects_unknown_drum_pitch_before_note_entry():
    setup='''function getDrumset(){return {instrumentId:"triangle",notes:[{pitch:81}]};}
function addChord(){throw Error("must not write");}'''
    result=run_function('addPercussionNote',setup,'addPercussionNote({staff:0,pitches:[60]})')
    assert 'not defined' in result['error']


def test_dotted_quarter_tempo_has_correct_playback_rate():
    setup='''
var Element={TEMPO_TEXT:1};
function executeWithUndo(f){return f();}
function notationCursor(){return {add(){}};}
function newElement(){return {};}
'''
    result=run_function('setTempo',setup,'setTempo({staff:0,startTick:0,bpm:124,beatUnit:"dottedQuarter",text:"With a bounce"})')
    assert result['quarterBpm']==186
    assert 'metAugmentationDot' in result['text']
