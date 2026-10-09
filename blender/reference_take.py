"""Hand-authored 7.47-second presenter study, inspired by the supplied reference.
No pose extraction or generative video is used. Values are Blender XYZ radians.
The approved hand meshes stay rigid; only shoulder/elbow/wrist parents move.
"""
import math
# time, presenting shoulder, elbow, wrist, head tilt, head turn, body turn,
# friendly, surprised, gaze right. Smooth transitions include anticipation/settle.
KEYS=(
 (0.00,-.12,.06,-.08,-.07,-.035,-.025,.15,.10,0),
 (.40,-.23,.10,-.13,-.045,-.020,-.015,.30,0,0),
 (1.20,-.08,.04,-.03,.025,.025,.015,.55,0,0),
 (1.70,.03,.10,.04,.040,.045,.025,.25,.15,.15),
 (2.35,-.43,.18,-.20,-.065,.080,.045,.10,.65,.75),
 (2.85,-.34,.14,-.13,-.020,.040,.020,.35,.10,.20),
 (3.55,.17,.49,.20,.050,-.030,-.025,.15,.35,0),
 (4.05,.21,.52,.24,.025,-.040,-.030,.75,0,0),
 (4.70,.11,.35,.13,-.025,-.015,-.010,.55,0,0),
 (5.20,-.05,.17,-.03,-.045,.020,.010,.05,.65,0),
 (5.90,-.36,.11,-.18,-.040,.045,.025,.35,.10,.40),
 (6.60,-.29,.09,-.12,.020,.015,.010,.80,0,0),
 (7.47,-.15,.07,-.06,0,0,0,.55,0,0),
)
def sample(t):
    t=max(0,min(7.47,float(t)))
    a,b=KEYS[-2:]
    for left,right in zip(KEYS,KEYS[1:]):
        if t<=right[0]:a,b=left,right;break
    u=max(0,min(1,(t-a[0])/(b[0]-a[0])));u=u*u*(3-2*u)
    v=[x+(y-x)*u for x,y in zip(a[1:],b[1:])]
    blink=0
    for center in (1.42,4.22,6.80):
        distance=abs(t-center)
        blink=max(blink,max(0,1-distance/.105))
    return dict(rotations={
        'Head_Pivot':(.015*math.sin(t*2.1),v[3],v[4]),
        'Shoulder_R':(0,v[0],.025*math.sin(t)),
        'Elbow_R':(0,v[1],0),'Wrist_R':(0,0,v[2]),
        'Shoulder_L':(.010*math.sin(t*1.5),-.018+.015*math.sin(t),0),
        'Elbow_L':(0,.012*math.sin(t*1.7),0),
    },body_turn=v[5],friendly=v[6],surprised=v[7],gaze=v[8],blink=blink)
