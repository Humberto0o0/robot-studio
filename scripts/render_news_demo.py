"""Seven-second authored study. Reference media is never published or embedded.
The diagnostic voice is freshly synthesized; timing remains text-derived.
"""
import json,sys,subprocess
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from server.main import analyze_pcm,decode,align
from server.render3d import render_3d_file
out=Path('demo-output');out.mkdir(exist_ok=True)
text='Hello there! Look over here. I have something exciting to share with you today. Thanks for joining me.'
raw=out/'diagnostic-voice.wav';voice=out/'demo-voice.wav'
subprocess.run(['espeak-ng','-s','190','-v','en-us','-w',str(raw),'--stdin'],input=text.encode(),check=True)
# Fit the complete utterance into the study, preserving all spoken words.
probe=subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1',str(raw)],text=True)
rate=max(1,float(probe)/7.1)
subprocess.run(['ffmpeg','-y','-loglevel','error','-i',str(raw),'-af',f'atempo={rate},apad','-t','7.47',str(voice)],check=True)
plan=align(analyze_pcm(decode(voice.read_bytes())),text)
plan.update(schema='robot-studio-performance/v3',timingSource='estimated',choreography='reference-study',settings={'captions':False,'energy':.6})
(out/'demo-plan.json').write_text(json.dumps(plan,indent=2));(out/'demo-script.txt').write_text(text)
render_3d_file(voice,plan,out/'robot-speaking-demo.mp4',quality='preview',fps=24,timeout=1500)
print('DEMO_OK',plan['duration'],flush=True)
