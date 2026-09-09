from scorebridge.score_ir import Event, Measure, Part, Score, Staff

def rests(count, duration): return [Event("rest", duration) for _ in range(count)]
def fixture_score():
    parts=[]
    specifications=[
        ("P1","Flute","wind.flutes.flute",None,"treble"),
        ("P2","Clarinet in B-flat","wind.reed.clarinet.bflat","Bb","treble"),
        ("P3","Horn in F","brass.french-horn","F","treble"),
    ]
    for pid,name,iid,trans,clef in specifications:
        measures=[Measure(1,[Event("note","quarter","C5"),Event("note","quarter","D5"),Event("note","quarter","E5"),Event("note","quarter","F5")],key_fifths=0,time_beats=4,time_beat_type=4,tempo_bpm=96,dynamics=["mf"]),Measure(2,rests(3,"quarter"),key_fifths=-1,time_beats=3,time_beat_type=4,directions=["legato"])]
        parts.append(Part(pid,name,iid,trans,[Staff(pid+"-S1",measures,clef)]))
    upper=[Measure(1,rests(4,"quarter"),key_fifths=0,time_beats=4,time_beat_type=4),Measure(2,rests(3,"quarter"),key_fifths=-1,time_beats=3,time_beat_type=4)]
    lower=[Measure(1,rests(4,"quarter"),key_fifths=0,time_beats=4,time_beat_type=4),Measure(2,rests(3,"quarter"),key_fifths=-1,time_beats=3,time_beat_type=4)]
    parts.append(Part("P4","Piano","keyboard.piano",None,[Staff("P4-S1",upper,"treble"),Staff("P4-S2",lower,"bass")]))
    return Score("ScoreBridge Vertical Slice",parts,"written",{"fixture":True})
