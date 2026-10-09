from __future__ import annotations
import hmac, os, re, subprocess, tempfile
from typing import Annotated
import numpy as np
from fastapi import FastAPI, File, Form, HTTPException, Request, Response, UploadFile
from fastapi.responses import JSONResponse
from fastapi.concurrency import run_in_threadpool

from .render import render_mp4
from .render3d import available as renderer3d_available, render_3d_mp4
from fastapi.middleware.cors import CORSMiddleware

VERSION="0.3.0"; SR=24000; FPS=30; MAX_BYTES=20*1024*1024; MAX_STORY_BYTES=10*1024*1024; MAX_DURATION_SECONDS=120; API_KEY=os.getenv("ROBOT_STUDIO_API_KEY","")
app=FastAPI(title="Robot Studio API",version=VERSION)
app.add_middleware(CORSMiddleware,allow_origins=["https://humberto0o0.github.io","http://localhost:8080","http://127.0.0.1:8080"],allow_credentials=False,allow_methods=["GET","POST"],allow_headers=["*"])

@app.middleware("http")
async def api_key_guard(request:Request,call_next):
    if API_KEY and request.url.path in {"/analyze","/director","/render","/render3d"}:
        supplied=request.headers.get("X-Robot-Studio-Key","")
        if not hmac.compare_digest(supplied,API_KEY):
            return JSONResponse(status_code=401,content={"detail":"Unauthorized"})
    return await call_next(request)


def clamp(v,a,b): return max(a,min(b,v))
def pct(a,p): return float(np.percentile(a,p*100)) if a.size else 0.0

def decode(blob:bytes)->np.ndarray:
    if not blob: raise HTTPException(400,"Empty audio upload")
    if len(blob)>MAX_BYTES: raise HTTPException(413,"Audio file is too large")
    with tempfile.NamedTemporaryFile(suffix=".media") as f:
        f.write(blob); f.flush()
        cmd=["ffmpeg","-hide_banner","-loglevel","error","-i",f.name,"-t",str(MAX_DURATION_SECONDS+1),"-vn","-ac","1","-ar",str(SR),"-f","f32le","pipe:1"]
        try: p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=45)
        except subprocess.TimeoutExpired as e: raise HTTPException(422,"Audio decode timed out") from e
    if p.returncode or not p.stdout: raise HTTPException(422,p.stderr.decode("utf-8","ignore")[-400:] or "Unsupported audio")
    pcm=np.frombuffer(p.stdout,dtype=np.float32)
    if len(pcm)/SR>MAX_DURATION_SECONDS:
        raise HTTPException(413,f"Audio must be {MAX_DURATION_SECONDS} seconds or shorter")
    return pcm

def analyze_pcm(audio:np.ndarray)->dict:
    hop=max(1,SR//FPS); frames=[]
    for st in range(0,len(audio),hop):
        s=audio[st:st+hop]
        if not len(s): continue
        rms=float(np.sqrt(np.mean(s*s))); z=float(np.mean(np.signbit(s[1:])!=np.signbit(s[:-1]))) if len(s)>1 else 0
        frames.append({"t":st/SR,"rms":rms,"zcr":z})
    if not frames: raise HTTPException(422,"No decodable audio samples")
    vals=np.array([f["rms"] for f in frames],np.float32)
    if len(vals)>=5: vals=np.convolve(vals,np.ones(5,np.float32)/5,mode="same")
    floor=pct(vals,.18); hi=pct(vals,.90); threshold=max(.0075,floor+(hi-floor)*.18); peak_threshold=max(threshold*1.75,pct(vals,.84))
    zhi=max(.01,pct(np.array([f["zcr"] for f in frames],np.float32),.85))
    for i,f in enumerate(frames):
        f["rms"]=float(vals[i]); f["speech"]=f["rms"]>threshold
        f["level"]=clamp((f["rms"]-threshold)/max(hi-threshold,.001),0,1); f["brightness"]=clamp(f["zcr"]/zhi,0,1)
    raw=[]; opened=None
    for i,f in enumerate(frames):
        if f["speech"] and opened is None: opened=i
        if not f["speech"] and opened is not None: raw.append([opened,i-1]); opened=None
    if opened is not None: raw.append([opened,len(frames)-1])
    merged=[]
    for s in raw:
        if not merged: merged.append(s); continue
        p=merged[-1]
        if (s[0]-p[1])/FPS<.18: p[1]=s[1]
        else: merged.append(s)
    duration=len(audio)/SR
    speech=[{"start":frames[a]["t"],"end":min(duration,frames[b]["t"]+1/FPS)} for a,b in merged if frames[b]["t"]+1/FPS-frames[a]["t"]>.10]
    pauses=[]; cur=0.0
    for s in speech:
        if s["start"]-cur>.32: pauses.append({"start":cur,"end":s["start"]})
        cur=s["end"]
    if duration-cur>.32: pauses.append({"start":cur,"end":duration})
    peaks=[]; last=-99.0
    for i in range(2,len(frames)-2):
        f=frames[i]
        if f["rms"]>peak_threshold and f["rms"]>=frames[i-1]["rms"] and f["rms"]>=frames[i+1]["rms"] and f["t"]-last>.70:
            peaks.append({"time":f["t"],"strength":f["level"]}); last=f["t"]
    pattern=["present","nod","open-hand","mic-in","lean","present"]; gestures=[]
    for i,s in enumerate(speech):
        d=s["end"]-s["start"]
        if d<.65: continue
        when=s["start"]+min(.68,d*.27)
        if gestures and when-gestures[-1]["time"]<1.05: continue
        gestures.append({"time":when,"type":pattern[i%len(pattern)],"duration":min(1.0,d*.42),"source":"audio"})
    for i,p in enumerate(peaks):
        if any(abs(g["time"]-p["time"])<.6 for g in gestures): continue
        gestures.append({"time":p["time"],"type":"emphasis" if i%2 else "excited","duration":.72,"strength":p["strength"],"source":"audio"})
    gestures.sort(key=lambda g:g["time"])
    compact=[{"t":round(f["t"],3),"level":round(f["level"],4),"speech":f["speech"],"brightness":round(f["brightness"],4)} for f in frames]
    return {"version":5,"fps":FPS,"sampleRate":SR,"duration":duration,"threshold":threshold,"speech":speech,"pauses":pauses,"emphasis":peaks,"gestures":gestures,"frames":compact,"words":[],"visemes":[],"storyCues":[]}

def active_to_real(active,speech):
    r=active
    for s in speech:
        d=s["end"]-s["start"]
        if r<=d: return s["start"]+r
        r-=d
    return speech[-1]["end"] if speech else 0.0

def gesture_for(w):
    w=w.lower()
    if any(k in w for k in ["amazing","incredible","excellent","great","good","wonderful","breakthrough","record","success","saved"]): return "excited"
    if any(k in w for k in ["look","see","watch","here","this","these","show","found","discover"]): return "present"
    if w in {"but","however","although","instead","while"}: return "lean"
    if w in {"you","your","people","everyone","we","our"}: return "open-hand"
    if w in {"today","now","finally","update","news"}: return "mic-in"
    if any(c.isdigit() for c in w) or any(k in w for k in ["percent","million","billion","hundred","thousand"]): return "nod"

def viseme(c,n=""):
    if (c+n).lower() in {"sh","ch","th","zh"}: return "E"
    if c in "mbp": return "M"
    if c in "fv": return "F"
    if c in "ouqw": return "O"
    if c in "eiy": return "E"
    if c=="a": return "A"
    if c in "lrtdnkgcsxzjh": return "S"
    return "REST"

def align(t,script,headline=""):
    tokens=re.findall(r"[A-Za-z0-9][A-Za-z0-9’'%-]*",script)
    if not tokens or not t["speech"]: return t
    total=sum(s["end"]-s["start"] for s in t["speech"]); weights=[max(1.0,len(re.sub(r"[^a-z0-9%]","",x.lower()))**.72) for x in tokens]; sw=sum(weights)
    active=0.; last=-99.; words=[]; vs=[]; gs=[]
    for idx,tok in enumerate(tokens):
        clean=re.sub(r"[^a-z0-9%]","",tok.lower()); dur=total*(weights[idx]/sw)
        st=active_to_real(active,t["speech"]); en=max(active_to_real(min(total,active+dur),t["speech"]),st+.08); active+=dur
        words.append({"text":tok,"clean":clean,"start":st,"end":en}); letters=list(clean); prev=""
        for j,c in enumerate(letters):
            sh=viseme(c,letters[j+1] if j+1<len(letters) else "")
            end=st+(en-st)*((j+1)/max(1,len(letters)))
            if sh==prev and vs and vs[-1]['word']==idx:
                vs[-1]['end']=end
            else:
                vs.append({"time":st+(en-st)*(j/max(1,len(letters))),"end":end,"shape":sh,"word":idx})
            prev=sh
        gt=gesture_for(clean)
        if gt and st-last>1.15: gs.append({"time":st,"type":gt,"duration":.78,"source":"script","word":tok}); last=st
    t["words"]=words; t["visemes"]=vs; t["gestures"]=sorted(t["gestures"]+gs,key=lambda g:g["time"])
    if headline:
        cue=next((g["time"] for g in t["gestures"] if g["type"]=="present" and g["time"]>1.2),None)
        if cue is None: cue=next((p["time"] for p in t["emphasis"] if p["time"]>2),None)
        if cue is None: cue=t["speech"][1]["start"] if len(t["speech"])>1 else t["speech"][0]["start"]
        cue=clamp(cue,0,max(0,t["duration"]-.5)); t["storyCues"]=[{"time":cue,"duration":min(5.2,max(2.8,t["duration"]-cue)),"type":"story-reveal"}]
    return t

@app.get("/health")
def health(): return {"ok":True,"service":"robot-studio-api","version":VERSION}

@app.get("/capabilities")
def capabilities(): return {"audioAnalysis":True,"scriptAlignment":True,"alignmentMethod":"estimated","semanticGestures":True,"storyCuePlanning":True,"transcription":False,"rendering3d":renderer3d_available(),"rendering3dMaxSeconds":30,"rendering":True,"renderFormat":"540x960 H.264/AAC MP4 preview","maxAudioSeconds":MAX_DURATION_SECONDS,"apiKeyProtection":bool(API_KEY),"notes":"Set ROBOT_STUDIO_API_KEY in hosted environments. Transcription and production 1080x1920 rendering are next."}

@app.post("/analyze")
async def analyze(audio:Annotated[UploadFile,File(...)]):
    t=analyze_pcm(decode(await audio.read(MAX_BYTES+1))); return {"schema":"robot-studio-analysis/v1",**t}

@app.post("/director")
async def director(audio:Annotated[UploadFile,File(...)],script:Annotated[str,Form()]="",story_headline:Annotated[str,Form()]=""):
    t=analyze_pcm(decode(await audio.read(MAX_BYTES+1)))
    if script.strip(): t=align(t,script.strip(),story_headline.strip())
    elif story_headline.strip():
        cue=next((p["time"] for p in t["emphasis"] if p["time"]>2),None)
        if cue is None: cue=t["speech"][1]["start"] if len(t["speech"])>1 else (t["speech"][0]["start"] if t["speech"] else 0)
        t["storyCues"]=[{"time":cue,"duration":min(5.2,max(2.8,t["duration"]-cue)),"type":"story-reveal"}]
    return {"schema":"robot-studio-director/v2","story":{"headline":story_headline.strip(),"cues":t.pop("storyCues",[])},**t}


@app.post("/render")
async def render_video(
    audio: Annotated[UploadFile, File(...)],
    script: Annotated[str, Form()] = "",
    story_headline: Annotated[str, Form()] = "",
    story_image: UploadFile | None = File(default=None),
) -> Response:
    audio_blob = await audio.read(MAX_BYTES + 1)
    pcm = decode(audio_blob)
    timeline = analyze_pcm(pcm)

    if script.strip():
        timeline = align(timeline, script.strip(), story_headline.strip())
    elif story_headline.strip():
        cue = next((p["time"] for p in timeline["emphasis"] if p["time"] > 2.0), None)
        if cue is None:
            cue = timeline["speech"][1]["start"] if len(timeline["speech"]) > 1 else (timeline["speech"][0]["start"] if timeline["speech"] else 0)
        timeline["storyCues"] = [{"time": cue, "duration": min(5.2, max(2.8, timeline["duration"] - cue)), "type": "story-reveal"}]

    story_blob: bytes | None = None
    if story_image is not None:
        story_blob = await story_image.read(MAX_STORY_BYTES + 1)
        if len(story_blob) > MAX_STORY_BYTES:
            raise HTTPException(413, "Story image is too large")

    try:
        mp4 = await run_in_threadpool(
            render_mp4,
            audio_blob,
            timeline,
            story_blob,
            story_headline.strip(),
        )
    except (ValueError, OSError) as exc:
        raise HTTPException(422, f"Could not render video: {exc}") from exc
    except subprocess.TimeoutExpired as exc:
        raise HTTPException(504, "Video render timed out") from exc
    except subprocess.CalledProcessError as exc:
        raise HTTPException(500, "FFmpeg could not finish the render") from exc
    except RuntimeError as exc:
        raise HTTPException(500, str(exc)) from exc

    return Response(
        content=mp4,
        media_type="video/mp4",
        headers={
            "Content-Disposition": 'attachment; filename="robot-performance.mp4"',
            "Cache-Control": "no-store",
        },
    )


@app.post("/render3d")
async def render_video_3d(
    audio: Annotated[UploadFile, File(...)],
    script: Annotated[str, Form()] = "",
    quality: Annotated[str, Form()] = "preview",
    performance: Annotated[str, Form()] = "",
) -> Response:
    """Render the real Blender model. Existing /render remains the legacy path."""
    if not renderer3d_available():
        raise HTTPException(503,"This server does not have the optional Blender renderer installed")
    blob=await audio.read(MAX_BYTES+1)
    pcm=decode(blob)
    if len(pcm)/SR>30:raise HTTPException(413,"3D API takes must be 30 seconds or shorter")
    if quality not in {"draft","preview","fullhd"}:raise HTTPException(422,"Unknown quality preset")
    timeline=analyze_pcm(pcm)
    if script.strip():timeline=align(timeline,script.strip())
    if performance:
        if len(performance)>2*1024*1024:raise HTTPException(413,"Performance JSON is too large")
        try:
            import json
            from blender.performance import normalize
            imported=json.loads(performance)
            normalized=normalize(imported)
            if abs(normalized['duration']-len(pcm)/SR)>.25:raise ValueError('Performance duration does not match audio')
            timeline={**imported,'duration':len(pcm)/SR}
        except (ValueError,TypeError,KeyError) as exc:
            raise HTTPException(422,str(exc)) from exc
    try:
        mp4=await run_in_threadpool(render_3d_mp4,blob,timeline,quality)
    except ValueError as exc:raise HTTPException(422,str(exc)) from exc
    except subprocess.TimeoutExpired as exc:raise HTTPException(504,"3D render timed out") from exc
    except (RuntimeError,OSError,subprocess.CalledProcessError) as exc:
        raise HTTPException(503,"3D rendering failed or is busy; inspect server logs") from exc
    return Response(content=mp4,media_type="video/mp4",headers={
        "Content-Disposition":'attachment; filename="robot-3d-performance.mp4"',"Cache-Control":"no-store"})
