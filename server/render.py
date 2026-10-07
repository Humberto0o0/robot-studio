from __future__ import annotations

import base64, io, math, subprocess, tempfile
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps
from .robot_asset import ROBOT_WEBP_B64

W,H,FPS=540,960,24
Image.MAX_IMAGE_PIXELS=25_000_000
ROBOT=Image.open(io.BytesIO(base64.b64decode(ROBOT_WEBP_B64))).convert("RGBA")
try:
    FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    CAPTION_FONT=ImageFont.truetype(FONT,22); SMALL_FONT=ImageFont.truetype(FONT,13); HEADLINE_FONT=ImageFont.truetype(FONT,15)
except Exception:
    CAPTION_FONT=SMALL_FONT=HEADLINE_FONT=ImageFont.load_default()

def clamp(v,a,b): return max(a,min(b,v))
def frame_at(timeline,t):
    fs=timeline.get("frames") or []
    if not fs:return {"level":0,"speech":False,"brightness":0}
    return fs[min(len(fs)-1,max(0,int(t*timeline.get("fps",30))))]
def gesture_at(timeline,t):
    hit=None
    for g in timeline.get("gestures",[]):
        dt=t-g["time"]; dur=g.get("duration",.7)
        if -.08<=dt<=dur: hit={**g,"progress":clamp((dt+.08)/(dur+.08),0,1)}
    return hit
def word_index(timeline,t):
    words=timeline.get("words") or [];lo,hi=0,len(words)-1
    while lo<=hi:
        m=(lo+hi)//2;w=words[m]
        if t<w["start"]:hi=m-1
        elif t>w["end"]:lo=m+1
        else:return m
    return -1
def viseme_at(timeline,t,f):
    if not f.get("speech"):return "REST"
    for v in timeline.get("visemes") or []:
        if t<v["time"]-.03:break
        if v["time"]-.03<=t<=v["end"]+.03:return v["shape"]
    lv=f.get("level",0);br=f.get("brightness",0)
    if lv<.12:return "M"
    if br>.7:return "E"
    if br<.24:return "O"
    return "A" if lv>.66 else "S"
def story_at(timeline,t,ready):
    if not ready:return None
    for c in timeline.get("story",{}).get("cues",timeline.get("storyCues",[])):
        if c["time"]-.25<=t<=c["time"]+c["duration"]+.25:
            intro=clamp((t-(c["time"]-.25))/.45,0,1);outro=clamp((c["time"]+c["duration"]+.25-t)/.45,0,1)
            return {**c,"progress":min(intro,outro)}
def bg_frame():
    yy,xx=np.mgrid[0:H,0:W];cx,cy=W*.5,H*.39
    dist=np.sqrt(((xx-cx)/(W*.75))**2+((yy-cy)/(H*.55))**2);a=np.clip(1-dist,0,1)
    c0=np.array([23,61,116.]);c1=np.array([3,8,15.]);arr=(c1+a[:,:,None]*(c0-c1)).clip(0,255).astype(np.uint8)
    return Image.fromarray(np.dstack([arr,np.full((H,W),255,np.uint8)]),"RGBA")
BG=bg_frame()

def mouth(layer,shape):
    d=ImageDraw.Draw(layer,"RGBA");cx=int(layer.width*.496);cy=int(layer.height*.451)
    pw,ph=int(layer.width*.145),int(layer.height*.077);patch=Image.new("RGBA",(pw*2,ph*2),(0,0,0,0));pd=ImageDraw.Draw(patch,"RGBA")
    pd.ellipse((6,5,patch.width-6,patch.height-5),fill=(245,248,252,255));patch=patch.filter(ImageFilter.GaussianBlur(1.5));layer.alpha_composite(patch,(cx-patch.width//2,cy-patch.height//2));d=ImageDraw.Draw(layer,"RGBA")
    if shape=="REST":d.arc((cx-22,cy-5,cx+22,cy+18),15,165,fill=(48,17,25,255),width=5);return
    dims={"M":(46,8),"O":(34,40),"A":(64,41),"E":(59,22),"F":(55,18),"S":(52,26)};mw,mh=dims.get(shape,(52,24))
    d.ellipse((cx-mw//2,cy-mh//2,cx+mw//2,cy+mh//2),fill=(50,8,17,255))
    if shape in ("F","E"):d.rectangle((cx-int(mw*.34),cy-int(mh*.25),cx+int(mw*.34),cy+1),fill=(250,248,240,255))
    if shape!="M":d.ellipse((cx-int(mw*.24),cy+int(mh*.12),cx+int(mw*.24),cy+int(mh*.36)),fill=(255,113,100,255))

def eye_reaction(layer,blink=False,excited=False):
    if not blink and not excited:return
    d=ImageDraw.Draw(layer,"RGBA")
    for rx,ry in ((.328,.280),(.624,.257)):
        cx,cy=int(layer.width*rx),int(layer.height*ry);ew,eh=int(layer.width*.061),int(layer.height*.047)
        d.ellipse((cx-ew,cy-eh,cx+ew,cy+eh),fill=(7,13,24,245))
        if blink:d.arc((cx-28,cy-5,cx+28,cy+16),195,345,fill=(93,238,255,255),width=6)
        else:d.arc((cx-28,cy-27,cx+28,cy+16),190,350,fill=(93,238,255,255),width=6)

def cover_resize(img,size):return ImageOps.fit(img,size,method=Image.Resampling.LANCZOS,centering=(.5,.5))
def story_card(frame,story_img,headline,p):
    e=1-(1-p)**3;x=int(318+(1-e)*150);y=150;w=192;h=265
    card=Image.new("RGBA",(w,h),(8,18,32,245));mask=Image.new("L",(w,h),0);ImageDraw.Draw(mask).rounded_rectangle((0,0,w,h),20,fill=255);frame.alpha_composite(Image.composite(card,Image.new("RGBA",(w,h)),mask),(x,y))
    media=cover_resize(story_img,(w-16,178));mm=Image.new("L",media.size,0);ImageDraw.Draw(mm).rounded_rectangle((0,0,*media.size),14,fill=255);media.putalpha(mm);frame.alpha_composite(media,(x+8,y+8))
    d=ImageDraw.Draw(frame,"RGBA");d.text((x+13,y+204),"STORY",font=SMALL_FONT,fill=(102,231,255,255));words=(headline or "Today's story").split();line="";yy=y+226
    for word in words:
        test=(line+" "+word).strip()
        if d.textbbox((0,0),test,font=HEADLINE_FONT)[2]>w-26 and line:d.text((x+13,yy),line,font=HEADLINE_FONT,fill="white");yy+=19;line=word
        else:line=test
    if line and yy<y+h-5:d.text((x+13,yy),line,font=HEADLINE_FONT,fill="white")

def caption(frame,timeline,t):
    i=word_index(timeline,t)
    if i<0:return
    words=timeline["words"];a=max(0,i-2);b=min(len(words),i+3);chunk=words[a:b];d=ImageDraw.Draw(frame,"RGBA");gap=7;max_w=W-70
    lines=[];line=[];line_w=0
    for k,w in enumerate(chunk):
        text=w["text"];ww=d.textbbox((0,0),text,font=CAPTION_FONT)[2];needed=ww if not line else gap+ww
        if line and line_w+needed>max_w and len(lines)<1:lines.append((line,line_w));line=[];line_w=0
        needed=ww if not line else gap+ww;line.append((a+k,text,ww));line_w+=needed
    if line:lines.append((line,line_w))
    base_y=828 if len(lines)>1 else 855
    for li,(items,total_w) in enumerate(lines[:2]):
        x=(W-total_w)/2;y=base_y+li*36
        for idx,text,ww in items:
            d.text((x,y),text,font=CAPTION_FONT,stroke_width=5,stroke_fill=(0,0,0,190),fill=(114,234,255,255) if idx==i else (255,255,255,255),anchor="lm");x+=ww+gap

def render_mp4(audio_blob:bytes,timeline:dict,story_blob:bytes|None=None,headline:str="")->bytes:
    story_img=None
    if story_blob:
        try:story_img=Image.open(io.BytesIO(story_blob)).convert("RGB")
        except Exception:story_img=None
    duration=float(timeline["duration"]);n=max(1,math.ceil(duration*FPS));robot_base=ROBOT.copy()
    with tempfile.TemporaryDirectory() as td:
        td=Path(td);audio_path=td/"audio.media";video_path=td/"video.mp4";out_path=td/"out.mp4";audio_path.write_bytes(audio_blob)
        proc=subprocess.Popen(["ffmpeg","-y","-loglevel","error","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),"-i","-","-an","-c:v","libx264","-preset","veryfast","-crf","21","-pix_fmt","yuv420p",str(video_path)],stdin=subprocess.PIPE)
        for i in range(n):
            t=i/FPS;f=frame_at(timeline,t);g=gesture_at(timeline,t);st=story_at(timeline,t,story_img is not None);frame=BG.copy();d=ImageDraw.Draw(frame,"RGBA")
            for k in range(14):
                xx=(k*97+int(t*5*(1+k%3)))%W;yy=(k*61+53)%700;d.ellipse((xx-1,yy-1,xx+1,yy+1),fill=(100,232,255,55))
            d.ellipse((165,781,375,807),outline=(96,231,255,110),width=4)
            if st:story_card(frame,story_img,headline,st["progress"])
            r=robot_base.copy();mouth(r,viseme_at(timeline,t,f));blink=(i%(FPS*3)) in (0,1);eye_reaction(r,blink=blink,excited=bool(g and g["type"] in ("excited","emphasis")))
            lv=float(f.get("level",0));p=math.sin(g["progress"]*math.pi) if g else 0;yoff=math.sin(t*1.75)*6-lv*6-p*8;xoff=math.sin(t*.65)*3;rot=math.sin(t*.9)*.8
            if g:
                if g["type"]=="present":xoff+=8*p;rot+=1*p
                elif g["type"]=="lean":xoff-=7*p;rot-=2*p
                elif g["type"] in ("excited","emphasis"):yoff-=8*p
            scale=.99+(lv*.01)+(p*.015);shift=-70*st["progress"] if st else 0;scale*=1-.12*st["progress"] if st else 1
            rr=r.resize((int(r.width*scale),int(r.height*scale)),Image.Resampling.BICUBIC).rotate(rot,Image.Resampling.BICUBIC,expand=True)
            frame.alpha_composite(rr,(int(W/2-rr.width/2+xoff+shift),int(H*.49-rr.height/2+yoff)));caption(frame,timeline,t);proc.stdin.write(np.asarray(frame.convert("RGB"),np.uint8).tobytes())
        proc.stdin.close()
        if proc.wait():raise RuntimeError("video encoder failed")
        subprocess.run(["ffmpeg","-y","-loglevel","error","-i",str(video_path),"-i",str(audio_path),"-c:v","copy","-c:a","aac","-b:a","128k","-shortest","-movflags","+faststart",str(out_path)],check=True,timeout=60)
        return out_path.read_bytes()
