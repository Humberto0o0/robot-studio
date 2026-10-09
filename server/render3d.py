"""Optional real 3D renderer. Uses a fixed Blender script and trusted model."""
from pathlib import Path
import json,math,os,shutil,subprocess,tempfile,threading

ROOT=Path(__file__).resolve().parents[1]
MODEL=ROOT/'models/robot-prototype.blend'
_LOCK=threading.BoundedSemaphore(1)


def available():
    return bool(shutil.which('blender') and MODEL.is_file() and shutil.which('ffmpeg'))


def timestamp(seconds):
    ms=max(0,round(seconds*1000));h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);s,ms=divmod(ms,1000)
    return f'{h:02}:{m:02}:{s:02},{ms:03}'


def write_captions(plan,path):
    words=plan.get('words',[]) if plan.get('settings',{}).get('captions',True) else [];blocks=[]
    for i in range(0,len(words),5):
        group=words[i:i+5];start=group[0].get('time',group[0].get('start',0))
        end=words[i+5].get('time',words[i+5].get('start',0)) if i+5<len(words) else plan['duration']
        text=' '.join(str(w.get('word',w.get('text',''))) for w in group)
        # Keep caption markup out of the subtitle parser.
        text=text.translate(str.maketrans({'{':'','}':'','\\':'','<':'','>':'','\n':' ','\r':' '}))
        if end>start:blocks.append(f'{len(blocks)+1}\n{timestamp(start)} --> {timestamp(end)}\n{text}\n')
    path.write_text('\n'.join(blocks),encoding='utf-8')
    return bool(blocks)


def render_3d_file(audio_path,plan,output_path,quality='preview',fps=24,timeout=1500):
    if not available():raise RuntimeError('Blender renderer is not installed; use the 3D image or render workflow.')
    if quality not in {'draft','preview','fullhd'}:raise ValueError('Unknown 3D quality preset')
    if not math.isfinite(float(plan.get('duration',0))) or not 0<float(plan['duration'])<=120:raise ValueError('Invalid duration')
    width,height={'draft':(360,640),'preview':(540,960),'fullhd':(1080,1920)}[quality]
    with tempfile.TemporaryDirectory(prefix='robot3d-') as tmp:
        temp=Path(tmp);timeline=temp/'plan.json';timeline.write_text(json.dumps(plan))
        silent=temp/'robot.mp4';captions=temp/'captions.srt'
        cmd=['blender','--background','--threads',os.getenv('ROBOT_RENDER_THREADS','2'),'--python-exit-code','1','--python',str(ROOT/'blender/render_performance.py'),'--',
             '--model',str(MODEL),'--plan',str(timeline),'--audio',str(audio_path),'--output',str(silent),'--width',str(width),'--height',str(height),'--fps',str(fps),'--samples','8' if quality=='draft' else '16']
        if shutil.which('xvfb-run'):cmd=['xvfb-run','-a']+cmd
        env={**os.environ,'LIBGL_ALWAYS_SOFTWARE':os.environ.get('LIBGL_ALWAYS_SOFTWARE','1')}
        with (temp/'blender.log').open('w+') as log:
            result=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,timeout=timeout,env=env)
            if result.returncode or not silent.is_file():
                log.seek(0);detail=log.read()[-2400:];raise RuntimeError('Blender failed: '+detail)
        args=['ffmpeg','-y','-loglevel','error','-i',str(silent),'-i',str(audio_path)]
        if write_captions(plan,captions):
            # Temp paths are generated internally and never taken from upload names.
            args+=['-vf',f"subtitles={captions}:force_style='FontName=DejaVu Sans,FontSize=18,Alignment=2,MarginV=48,Outline=2'",'-c:v','libx264','-preset','fast','-crf','19']
        else:args+=['-c:v','copy']
        args+=['-map','0:v:0','-map','1:a:0','-c:a','aac','-b:a','128k','-t',str(plan['duration']),'-movflags','+faststart',str(output_path)]
        subprocess.run(args,check=True,timeout=90)
    return Path(output_path)


def render_3d_mp4(audio_blob,plan,quality='preview'):
    # Synchronous API is intentionally limited; long takes should use a worker/CLI.
    if plan['duration']>30:raise ValueError('Synchronous 3D rendering supports at most 30 seconds; use the render worker for longer takes.')
    if not _LOCK.acquire(blocking=False):raise RuntimeError('A 3D render is already running; retry when it finishes.')
    try:
        with tempfile.TemporaryDirectory(prefix='robot3d-request-') as tmp:
            audio=Path(tmp)/'voice.media';audio.write_bytes(audio_blob)
            result=render_3d_file(audio,plan,Path(tmp)/'performance.mp4',quality=quality)
            return result.read_bytes()
    finally:_LOCK.release()
