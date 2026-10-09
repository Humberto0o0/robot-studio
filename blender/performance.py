"""Pure-Python timeline adapter shared by CLI rendering and server jobs.

Accepts browser performance/v3 and the server's director/v2 representation.
Text-derived cues remain estimated; imported timings are never re-labelled as
forced alignment. No dependency on bpy, so validation can run before Blender.
"""
import math

SHAPES=('A','E','O','U','M','F','S','SMILE')

def normalize(data):
    if not isinstance(data,dict):raise ValueError('Performance must be a JSON object')
    duration=float(data.get('duration',0))
    if not math.isfinite(duration) or not 0<duration<=120:
        raise ValueError('Performance duration must be between 0 and 120 seconds')
    cues=[];last=0
    for v in data.get('visemes',[]):
        start=float(v['time']);end=float(v['end']);shape=v['shape']
        if not all(math.isfinite(x) for x in (start,end)) or start<last-1e-6 or end<=start or end>duration+.025 or shape not in SHAPES:
            raise ValueError('Invalid or overlapping speech cue')
        cues.append(dict(time=start,end=min(end,duration),shape=shape));last=end
    words=[]
    for w in data.get('words',[]):
        start=float(w.get('time',w.get('start',0)))
        text=str(w.get('word',w.get('text','')))[:200]
        if not math.isfinite(start) or not 0<=start<=duration:raise ValueError('Invalid word time')
        words.append(dict(time=start,text=text))
    gestures=[]
    for g in data.get('cues',data.get('gestures',[])):
        start=float(g.get('t',g.get('time',0)))
        if not math.isfinite(start) or not 0<=start<=duration:raise ValueError('Invalid gesture time')
        gestures.append(dict(time=start,pose=g.get('pose',g.get('type','neutral'))))
    frames=[]
    for f in data.get('frames',[]):
        t=float(f.get('t',0));level=float(f.get('level',0))
        if not math.isfinite(t) or not math.isfinite(level) or not 0<=t<=duration+.04:raise ValueError('Invalid audio envelope')
        frames.append(dict(t=t,level=max(0,min(1,level))))
    return dict(duration=duration,visemes=cues,words=sorted(words,key=lambda w:w['time']),
                gestures=sorted(gestures,key=lambda g:g['time']),frames=sorted(frames,key=lambda f:f['t']),
                headline=str(data.get('headline',data.get('story',{}).get('headline','')))[:180],
                timingSource=data.get('timingSource','estimated'))

def pose_at(plan,t):
    current=None
    for c in plan['gestures']:
        if c['time']>t:break
        current=c
    if not current:return 'neutral',0
    age=t-current['time']
    if age>=1.7:return 'neutral',0
    smooth=lambda x:max(0,min(1,x))**2*(3-2*max(0,min(1,x)))
    return current['pose'],smooth(age/.25)*(1-smooth((age-1.1)/.6))

def shape_at(plan,t):
    if not plan['visemes']:
        frame=next((f for f in reversed(plan['frames']) if f['t']<=t),None)
        level=frame['level'] if frame else 0
        return 'A' if level>.55 else 'E' if level>.2 else 'S' if level>.08 else 'REST'
    for cue in plan['visemes']:
        if cue['time']<=t<cue['end']:return cue['shape']
        if cue['time']>t:break
    return 'REST'

def blink_at(t):
    p=(t+1.2)%4.6
    return 0 if p>.19 else p/.065 if p<.065 else max(0,1-(p-.065)/.125)
