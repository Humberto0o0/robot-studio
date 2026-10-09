"""Reproducible spoken test; espeak is a diagnostic voice, not the final brand voice."""
import json,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from server.main import analyze_pcm,decode,align
from server.render3d import render_3d_file

out=Path('demo-output');out.mkdir(exist_ok=True)
text=('Hello, I am your robot presenter. Here is a quick studio update. '
      'My new expressions help me speak more clearly. Look over here as I explain the story. '
      'Small movements make a big difference. Thanks for watching.')
voice=out/'demo-voice.wav'
subprocess.run(['espeak-ng','-s','155','-v','en-us','-w',str(voice),'--stdin'],input=text.encode(),check=True)
plan=align(analyze_pcm(decode(voice.read_bytes())),text)
plan['schema']='robot-studio-performance/v3';plan['timingSource']='estimated'
plan['cues']=[{'t':0,'pose':'wave'},{'t':4,'pose':'point'},{'t':8,'pose':'present'},{'t':12,'pose':'nod'},{'t':max(13,plan['duration']-2),'pose':'wave'}]
(out/'demo-plan.json').write_text(json.dumps(plan,indent=2));(out/'demo-script.txt').write_text(text)
render_3d_file(voice,plan,out/'robot-speaking-demo.mp4',quality='draft',fps=12,timeout=1200)
print('DEMO_OK',plan['duration'],flush=True)
