import {SPEECH_SHAPES,estimateVisemes,validateTiming,shapeAt,blinkAt} from './performance.mjs';
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';

// Robot Studio 3D. One compositor canvas is the sole visual/export source.
// Voice analysis and transcript timing run locally; no microphone upload or API keys.
const $=id=>document.getElementById(id);
const canvas=$('stage'),ctx=canvas.getContext('2d',{alpha:false});
const wave=$('wave'),wctx=wave.getContext('2d');
const audio=$('audio');
const VW=540,VH=960,FPS=30,AMBIENT="#071323";
const clamp=(n,a=0,b=1)=>Math.max(a,Math.min(b,n));
const mix=(a,b,t)=>a+(b-a)*t;
const smooth=(a,b,t)=>{let x=clamp((t-a)/Math.max(.001,b-a));return x*x*(3-2*x)};
const rnd=(v)=>Math.sin(v*25.367+17)*43758.5453%1;
const fmt=(s)=>{s=Number.isFinite(s)?Math.max(0,s):0;return String(Math.floor(s/60)).padStart(2,"0")+":"+String(Math.floor(s%60)).padStart(2,"0")};
const state={ready:false,file:null,objectURL:null,duration:0,buffer:null,env:[],speech:[],pauses:[],emphasis:[],cues:[],
 words:[],story:null,storyURL:null,script:"",headline:"",playing:false,demo:false,analyzing:false,
 t:0,lastT:0,uiDrag:false,pose:"neutral",poseUntil:0,poseIndex:0,angle:0,pitch:0.042,orbitDistance:8.35,dragX:null,
 record:null,recordStarted:false,mediaSource:null,audioContext:null,destination:null,
 visemes:[],timingSource:"estimated",manualShape:"AUTO",expression:"AUTO",mouthValue:0,blinkValue:0,lastBlink:0,videoURL:null,gestureT:0};
const settings={mouth:true,gestures:true,captions:true,blink:true,float:true,camera:true,energy:.6};
let rig=null;
let captureScale=1;
let renderClock=performance.now();
const glcanvas=document.createElement('canvas');
glcanvas.width=VW;glcanvas.height=VH;
let renderer,scene,camera,keyLight,fillLight,ambientLight;
try{
 renderer=new THREE.WebGLRenderer({canvas:glcanvas,alpha:true,antialias:true,preserveDrawingBuffer:true,powerPreference:'high-performance'});
 renderer.setSize(VW,VH,false);
 renderer.setPixelRatio(1);
 renderer.outputColorSpace=THREE.SRGBColorSpace;
 renderer.toneMapping=THREE.ACESFilmicToneMapping;
 renderer.toneMappingExposure=1.2;
 scene=new THREE.Scene();
 camera=new THREE.PerspectiveCamera(45,VW/VH,.05,100);
 camera.position.set(0,2.25,8.35);
 camera.lookAt(0,1.9,0);
 ambientLight=new THREE.HemisphereLight(0xd9efff,0x193466,2.1);scene.add(ambientLight);
 keyLight=new THREE.DirectionalLight(0xffffff,3.2);keyLight.position.set(-3,8,6);scene.add(keyLight);
 fillLight=new THREE.DirectionalLight(0x399dff,2.0);fillLight.position.set(3,2,-2);scene.add(fillLight);
}catch(error){$('status').textContent='3D graphics unavailable';$('liveAction').textContent='This browser cannot start WebGL. '+error.message;}

const nodes={},defaults={},faceMeshes=[];
function findRig(model){
 model.traverse(o=>{
   if(o.name)nodes[o.name]=o;
   // Preserve saturated screen colours under the bright studio exposure.
   if(o.isMesh){
    for(const mat of (Array.isArray(o.material)?o.material:[o.material])){
     if(mat&&/Blue LED diffuser|Cyan LED pixel matrix/.test(mat.name))mat.toneMapped=false;
    }
   }
   if(o.morphTargetDictionary)faceMeshes.push(o);
   if(o.isObject3D)defaults[o.uuid]={q:o.quaternion.clone(),p:o.position.clone(),scale:o.scale.clone()};
 });
 rig=model;
 // Three.js glTF positions are anchored in real 3D, including shoulder/elbow joints.
 scene.add(rig);
 $('status').textContent=Object.keys(nodes).some(n=>/Eye[_ ]emissive[_ ]LED[_ ]matrix[_ ]L/i.test(n))&&Object.keys(nodes).some(n=>/Mouth[_ ]open[_ ]burgundy[_ ]recess/i.test(n))?'3D ready · Speech & expressions':'3D ready';
 $('liveAction').textContent='Real shoulder and elbow joints loaded. Add audio for automatic direction.';
}
if(renderer){
 new GLTFLoader().load('./models/robot-prototype.glb?v=28',
  gltf=>{findRig(gltf.scene);state.ready=true;updateControls();},
  undefined,
  err=>{$('status').textContent='3D model failed';$('liveAction').textContent='Could not load the .glb model. Check connection or reload. '+String(err?.message||err);}
 );
}
const drawRounded=(x,y,w,h,r,fill)=>{
 ctx.beginPath();ctx.roundRect(x,y,w,h,r);ctx.fillStyle=fill;ctx.fill();
};
function background(t){
 let g=ctx.createLinearGradient(0,0,VW,VH);g.addColorStop(0,'#142b55');g.addColorStop(.52,'#071a33');g.addColorStop(1,'#030b17');
 ctx.fillStyle=g;ctx.fillRect(0,0,VW,VH);
 const halo=ctx.createRadialGradient(255,395,35,255,395,405);
 halo.addColorStop(0,'rgba(31,117,207,.35)');halo.addColorStop(.4,'rgba(19,79,142,.1)');halo.addColorStop(1,'rgba(10,19,31,0)');
 ctx.fillStyle=halo;ctx.fillRect(0,0,VW,VH);
 ctx.strokeStyle='rgba(81,164,252,.07)';ctx.lineWidth=1;
 for(let x=-180;x<VW+250;x+=74){ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x+200,VH);ctx.stroke();}
 for(let y=82;y<VH;y+=82){ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(VW,y);ctx.stroke();}
 for(let i=0;i<15;i++){
  let x=(i*137.2+Math.sin(t*.29+i)*11)%VW, y=((i*179.1-t*(5+i%3))%VH+VH)%VH;
  ctx.fillStyle='rgba(108,211,255,'+(.08+.12*(1+Math.sin(t+i))/2)+')';
  ctx.beginPath();ctx.arc(x,y,1.5+i%3,0,Math.PI*2);ctx.fill();
 }
}
function overlayPanels(t,loud){
 // Deliberately leave the visor clear; titles/photo are above or beside the shoulders.
 drawRounded(22,22,143,30,15,'rgba(1,15,30,.68)');
 ctx.font='800 12px system-ui';ctx.fillStyle='#91e7ff';ctx.fillText('ROBOT STUDIO',37,42);
 ctx.fillStyle='rgba(98,173,240,.55)';ctx.fillRect(34,74,1,38);
 ctx.textAlign='right';ctx.font='800 11px system-ui';ctx.fillStyle='#a8c5e9';ctx.fillText(state.file?.name?'VOICE PERFORMANCE':'3D DIRECTOR',VW-26,39);ctx.textAlign='left';
 const bottom=ctx.createLinearGradient(0,VH-290,0,VH);
 bottom.addColorStop(0,'rgba(3,8,18,0)');bottom.addColorStop(.43,'rgba(3,8,18,.47)');bottom.addColorStop(1,'rgba(3,8,18,.9)');
 ctx.fillStyle=bottom;ctx.fillRect(0,VH-290,VW,290);
 ctx.beginPath();ctx.moveTo(38,VH-70);ctx.lineTo(VW-38,VH-70);
 ctx.lineWidth=1;ctx.strokeStyle='rgba(92,204,255,.22)';ctx.stroke();
 ctx.textAlign='center';ctx.font='700 11px system-ui';ctx.fillStyle='#77b6da';ctx.fillText('YOUR AI NEWS PRESENTER',VW/2,VH-43);ctx.textAlign='left';
 for(let i=0;i<22;i++){
  const x=150+i*11, h=5+32*Math.pow(Math.sin(i*1.2+t*7),2)*loud;
  ctx.fillStyle=i%4?'rgba(68,195,250,.55)':'#8af1ff';
  ctx.fillRect(x,VH-105-h/2,4,h);
 }
}
function imageCover(img,x,y,w,h){
 if(!img||!img.width||!img.height)return;
 const k=Math.max(w/img.width,h/img.height),iw=img.width*k,ih=img.height*k;
 ctx.drawImage(img,x+(w-iw)/2,y+(h-ih)/2,iw,ih);
}
function wrap(text,maxWidth,font){
 ctx.font=font;const words=(text||'').split(/\s+/).filter(Boolean),lines=[];let line='';
 for(let word of words){let candidate=line?line+' '+word:word;if(ctx.measureText(candidate).width>maxWidth&&line){lines.push(line);line=word;}else line=candidate;}
 if(line)lines.push(line);return lines;
}
function drawStory(t){
 if(!state.story&&!state.headline)return;
 // Lower-middle card, deliberately small enough not to overlap the robot's face.
 const show=(state.duration? t<Math.min(state.duration,7):true);
 if(!show)return;
 const w=228,h=state.story?196:98,x=VW-w-18,y=118;
 ctx.save();ctx.globalAlpha=.94;smooth(.05,1.1,t);
 drawRounded(x,y,w,h,16,'rgba(9,28,50,.97)');
 ctx.save();ctx.beginPath();ctx.roundRect(x+3,y+3,w-6,h-6,13);ctx.clip();
 if(state.story) imageCover(state.story,x+3,y+3,w-6,state.headline?h-47:h-6);
 if(state.headline){ctx.fillStyle='rgba(4,18,35,.92)';ctx.fillRect(x,y+h-48,w,48);const lines=wrap(state.headline,w-20,'750 15px system-ui').slice(0,2);ctx.textAlign='center';ctx.fillStyle='#eefbff';ctx.font='750 15px system-ui';lines.forEach((line,i)=>ctx.fillText(line,x+w/2,y+h-29+i*17));ctx.textAlign='left';}
 ctx.restore();ctx.strokeStyle='rgba(90,206,255,.45)';ctx.lineWidth=1;ctx.beginPath();ctx.roundRect(x,y,w,h,16);ctx.stroke();ctx.restore();
}
function getCurrentWord(t){
 const words=state.words;if(!words.length)return -1;
 let lo=0,hi=words.length-1;
 while(lo<=hi){let m=(lo+hi)>>1;if(words[m].time<=t)lo=m+1;else hi=m-1;}
 return clamp(hi,0,words.length-1);
}
function drawCaptions(t){
 if(!settings.captions||!state.words.length||!state.playing&&!state.uiDrag&&t===0)return;
 const i=getCurrentWord(t);
 if(i<0)return;
 const c=Math.floor(i/5),group=state.words.slice(c*5,c*5+5),s=group.map(x=>x.word).join(' ');
 let size=29,lines=wrap(s,470,'850 '+size+'px system-ui');
 if(lines.length>2){size=24;lines=wrap(s,465,'850 '+size+'px system-ui');}
 let y=VH-206;
 ctx.textAlign='center';ctx.shadowColor='rgba(0,0,0,.9)';ctx.shadowBlur=9;
 ctx.font='850 '+size+'px system-ui';ctx.fillStyle='#fff';
 // Current word highlighted only in single-line captions; multiline stays readable.
 lines.slice(0,3).forEach((line,li)=>{
   const ly=y+li*(size+9);ctx.lineWidth=6;ctx.strokeStyle='#061020';ctx.strokeText(line,VW/2,ly);ctx.fillText(line,VW/2,ly);
 });
 if(lines.length===1){
   const offsetWords=group.slice(0,i%5).map(x=>x.word).join(' '),active=group[i%5]?.word||'';
   const textWidth=ctx.measureText(s).width,left=VW/2-textWidth/2;
   const ahead=ctx.measureText(offsetWords+(offsetWords?' ':'')).width;
   ctx.textAlign='left';ctx.fillStyle='#79e9ff';ctx.fillText(active,left+ahead,y);
 }
 ctx.shadowBlur=0;ctx.textAlign='left';
}
function frameAudio(t){
 if(!state.env.length)return 0;
 let i=clamp(Math.floor(t*FPS),0,state.env.length-1);
 return mix(state.env[i]||0,state.env[Math.min(i+1,state.env.length-1)]||0,t*FPS-i);
}
function currentCue(t){
 let out=null;
 for(let c of state.cues){if(c.t<=t)out=c;else break;}
 return out;
}
const activeSpeech=(t)=>state.speech.some(p=>t>=p.start&&t<=p.end);
function gestureAt(t){
 if(state.poseUntil && performance.now()<state.poseUntil && !state.playing)return state.pose;
 if(!state.duration)return state.pose;
 const cue=currentCue(t);
 if(!settings.gestures||!cue)return 'neutral';
 if(t-cue.t>=1.7)return 'neutral';
 return cue.pose;
}
function applyJoint(name,axis,amount){
 const o=nodes[name];if(!o)return;
 const def=defaults[o.uuid];
 o.quaternion.copy(def.q);
 const v=axis==='y'?new THREE.Vector3(0,1,0):axis==='x'?new THREE.Vector3(1,0,0):new THREE.Vector3(0,0,1);
 o.quaternion.multiply(new THREE.Quaternion().setFromAxisAngle(v,amount));
}
function applyPosition(name,x,y,z){
 const o=nodes[name];if(!o)return;const d=defaults[o.uuid].p;o.position.set(d.x+x,d.y+y,d.z+z);
}
function animate3D(t,dt,loud){
 if(!rig)return;
 let energy=settings.energy,pose=gestureAt(t),clipTime=state.duration?t:performance.now()/1000;
 let intro=state.duration&&t<2&&!(state.poseUntil && performance.now()<state.poseUntil)?'wave':pose;
 if(!state.duration&&state.poseUntil>0&&performance.now()>state.poseUntil){state.pose='neutral';state.poseUntil=0;intro='neutral';}
 const ph=clipTime;
 // Smooth cosine envelopes at gesture boundaries prevent sudden arm pops.
 let start=0,strength=0;
 const cue=currentCue(t);
 if(state.poseUntil && performance.now()<state.poseUntil && !state.playing){strength=intro==='neutral'?0:1;}
 else if(state.duration&&cue&&intro!=='neutral'){start=t-cue.t;strength=smooth(0,.25,start)*(1-smooth(1.1,1.7,start));}
 else if(!state.duration){strength=intro==='neutral'?0:1;}
 const pulse=energy*strength;
 const hover=settings.float ? .035*Math.sin(ph*1.65) : 0;
 applyPosition('Robot_Root',0,hover,0);
 applyJoint('Head_Pivot','z',.028*Math.sin(ph*1.13)+.045*loud*energy);
 applyJoint('Shoulder_L','y',-.08+.04*Math.sin(ph*1.1)-.08*loud);
 const rightRaise=(intro==='wave'?-.77:intro==='present'?-.42:intro==='point'?-.61:0)*pulse;
 applyJoint('Shoulder_R','y',-.05+rightRaise+.045*Math.sin(ph*1.25));
 applyJoint('Elbow_R','y',(intro==='point'?.26:intro==='wave'?.22:intro==='present'?.11:0)*pulse);
 applyJoint('Elbow_L','y',-.075*loud);
 applyJoint('Wrist_R','z',intro==='wave'?.35*pulse*Math.sin(ph*9):0);
 // Restored V8 presenting pose. Keep the four fingers relaxed and aligned.
 // Finger movement is small: large X bends made the open palm look claw-like.
 const gestureSoft=(intro==='present'?.035:intro==='point'?.065:intro==='wave'?.047:.008)*pulse;
 for(let k=0;k<4;k++){
   const stagger=(k-1.5)*.012;
   const wave= intro==='wave'?.015*Math.sin(ph*6.1+k*.6)*pulse:0;
   applyJoint('Finger_R_'+k+'_Knuckle','z',gestureSoft+stagger+wave);
   applyJoint('Finger_R_'+k+'_Tip','x',gestureSoft*.18);
   applyJoint('Finger_L_'+k+'_Knuckle','z',-.007+.009*loud);
 }
 applyJoint('Thumb_R_Root','z',-.012+gestureSoft*.22);
 applyJoint('Thumb_L_Root','z',-.012-.008*loud);
 const mouthOn=settings.mouth&&(state.duration?activeSpeech(t):false);
 let shape=state.manualShape!=='AUTO'&&!state.playing?state.manualShape:'REST';
 if(state.manualShape==='AUTO'||state.playing){
  if(state.timingSource==='imported'&&state.duration)shape=shapeAt(state.visemes,t);
  else if(mouthOn)shape=state.visemes.length?shapeAt(state.visemes,t):(loud>.55?'A':loud>.2?'E':'S');
 }
 if(!settings.mouth)shape='REST';
 const blink=settings.blink?blinkAt(ph):0;
 const attentive=state.expression==='ATTENTIVE'?1:state.expression==='FRIENDLY'?0:
  (intro==='wave'||intro==='present'?0:.75);
 for(const mesh of faceMeshes){
  for(const [key,index] of Object.entries(mesh.morphTargetDictionary)){
   const target=key==='BLINK'?blink:key==='ATTENTIVE'?attentive*(1-blink):key==='FRIENDLY'?(state.expression==='FRIENDLY'?.8:0)*(1-blink):key==='SURPRISED'?(state.expression==='SURPRISED'?1:0)*(1-blink):key===shape?1:0;
   mesh.morphTargetInfluences[index]=mix(mesh.morphTargetInfluences[index],target,clamp(dt*24,0,1));
  }
 }
 canvas.dataset.mouthShape=shape;
 canvas.dataset.faceMorphCount=faceMeshes.length;
 canvas.dataset.timingSource=state.timingSource;
 const yaw=state.angle+(settings.camera?.015*Math.sin(ph*.34):0);
 const pitch=state.pitch,dist=state.orbitDistance;
 camera.position.set(Math.sin(yaw)*Math.cos(pitch)*dist,
    1.93+Math.sin(pitch)*dist+Math.sin(ph*.14)*.03,
    Math.cos(yaw)*Math.cos(pitch)*dist);
 camera.lookAt(0,1.93,0);
 // UI-inspectable readout for accessibility and regression testing.
 // Camera settings are preview-only interaction state and not personal data.
 canvas.dataset.cameraYaw=state.angle.toFixed(3);
 canvas.dataset.cameraPitch=state.pitch.toFixed(3);
 canvas.dataset.cameraDistance=state.orbitDistance.toFixed(3);
 $('poseBadge').textContent=intro;
}
function drawPlaceholder(){
 ctx.fillStyle='#d4e9ff';ctx.font='bold 20px system-ui';ctx.textAlign='center';
 ctx.fillText('Loading connected 3D robot…',VW/2,450);ctx.textAlign='left';
}
function render(now){
 requestAnimationFrame(render);
 ctx.setTransform(captureScale,0,0,captureScale,0,0);
 const dt=clamp((now-renderClock)/1000,0,.08);renderClock=now;
 const t=state.duration?clamp(audio.currentTime||0,0,state.duration):0;
 state.t=t;
 const loud=frameAudio(t);
 background(t);
 if(renderer&&rig){animate3D(t,dt,loud);try{renderer.clear();renderer.render(scene,camera);ctx.drawImage(glcanvas,0,0,VW,VH);}catch(e){$('status').textContent='3D drawing issue';}}
 else drawPlaceholder();
 drawStory(t);overlayPanels(t,loud);drawCaptions(t);
 if(!state.uiDrag&&state.duration){$('seek').value=Math.round(t/state.duration*1000);$('clock').textContent=fmt(t)+' / '+fmt(state.duration);}
 state.lastT=t;
}
requestAnimationFrame(render);
function updateControls(){
 $('play').disabled=!state.duration;
 $('seek').disabled=!state.duration;
 $('record').disabled=!(state.ready&&state.duration);
 $('downloadPlan').disabled=!state.duration;
 $('play').textContent=state.playing?'❚❚ Pause':'▶ Play';
}
async function audioContext(){
 if(!state.audioContext)state.audioContext=new (window.AudioContext||window.webkitAudioContext)();
 return state.audioContext;
}
function audioStats(buf){
 const sr=buf.sampleRate,n=buf.length,dur=buf.duration, ch=buf.numberOfChannels;
 const count=Math.min(30*60*FPS,Math.ceil(dur*FPS));
 const env=new Float32Array(count);
 const samples=128;
 for(let f=0;f<count;f++){
  const start=Math.floor(f*sr/FPS),end=Math.min(n,Math.floor((f+1)*sr/FPS)),width=Math.max(1,end-start);
  let sq=0;
  for(let j=0;j<samples;j++){let idx=Math.min(n-1,start+Math.floor(j*width/samples));let v=0;for(let c=0;c<Math.min(ch,2);c++)v+=buf.getChannelData(c)[idx];v/=Math.min(ch,2);sq+=v*v;}
  env[f]=Math.sqrt(sq/samples);
 }
 const arr=[...env].sort((a,b)=>a-b);
 const p85=arr[Math.floor(arr.length*.85)]||.001,p60=arr[Math.floor(arr.length*.6)]||.001;
 const floor=Math.max(.007,Math.min(p85*.20,p60*.85));
 const smoothEnv=[];
 let prev=0;
 for(let i=0;i<env.length;i++){const v=clamp((env[i]-floor)/Math.max(.04,p85*.85-floor),0,1);prev=mix(prev,v,.32);smoothEnv.push(prev);}
 const speech=[],pauses=[],emphasis=[],minSpeech=.16,minPause=.25;
 let flag=false,start=0;
 for(let i=0;i<smoothEnv.length;i++){
  const v=smoothEnv[i],now=i/FPS,yes=flag?(v>.065):(v>.14);
  if(yes!==flag){
    if(flag&&now-start>=minSpeech)speech.push({start,end:now});
    flag=yes;start=now;
  }
 }
 if(flag&&dur-start>=minSpeech)speech.push({start,end:dur});
 for(let i=1;i<speech.length;i++){const gap=speech[i].start-speech[i-1].end;if(gap>minPause)pauses.push({start:speech[i-1].end,end:speech[i].start});}
 for(let i=10;i<smoothEnv.length-10;i+=4){
  const v=smoothEnv[i];
  if(v>.65&&v>smoothEnv[i-6]+.10&&v>=smoothEnv[i+6]&&(!emphasis.length||i/FPS-emphasis.at(-1).t>1.6))emphasis.push({t:i/FPS,v});
 }
 return {env:smoothEnv,speech,pauses,emphasis};
}
function mapWords(script,speech,duration){
 const raw=(script||'').trim().split(/\s+/).filter(Boolean).slice(0,10000);
 if(!raw.length)return [];
 const zones=speech.length?speech:[{start:0,end:duration}];
 const activeDur=zones.reduce((s,z)=>s+(z.end-z.start),0)||duration;
 const weights=raw.map(w=>Math.max(1,Math.sqrt(w.replace(/[^\p{L}\p{N}]/gu,'').length||2)));
 const total=weights.reduce((a,b)=>a+b,0),list=[];let progress=0;
 for(let i=0;i<raw.length;i++){
  const activeTime=activeDur*progress/total;progress+=weights[i];
  let remain=activeTime,t=0;
  for(const zone of zones){const len=zone.end-zone.start;if(remain<=len){t=zone.start+remain;break;}remain-=len;t=zone.end;}
  list.push({word:raw[i],time:Math.min(duration,t)});
 }
 return list;
}
function makeCues(){
 const cues=[{t:0,pose:'wave',title:'Welcome',detail:'Friendly introduction'}];
 for(const p of state.speech){
  const time=p.start+.15;
  if(time>1.9&&time<state.duration-.4&&(!cues.length||time-cues.at(-1).t>2.6)){
   const pose=cues.length%3===0?'wave':cues.length%2===0?'point':'present';
   cues.push({t:time,pose,title:'Speech gesture',detail:'Natural arm movement during speech'});
  }
 }
 for(const p of state.emphasis){
  if(p.t>2&&p.t<state.duration-.4&&cues.every(c=>Math.abs(c.t-p.t)>2.2)){
   cues.push({t:p.t,pose:'point',title:'Emphasis',detail:'Audio energy spike'});
  }
 }
 if(state.story||state.headline)cues.push({t:Math.min(2,Math.max(.4,state.duration*.15)),pose:'present',title:'Introduce story',detail:'Show story visual'});
 cues.sort((a,b)=>a.t-b.t);
 state.cues=cues.filter((c,i)=>i===0||c.t!==cues[i-1].t);
 $('speechCount').textContent=state.speech.length;
 $('pauseCount').textContent=state.pauses.length;
 $('peakCount').textContent=state.emphasis.length;
 $('gestureCount').textContent=state.cues.length;
 $('liveAction').textContent=state.speech.length+' speech sections analyzed. '+state.cues.length+' directed movements; gestures stay connected to 3D shoulder and elbow joints.';
 const el=$('timeline');el.replaceChildren();
 if(!state.cues.length){el.textContent='No gesture cues.';return;}
 for(let c of state.cues){const item=document.createElement('div');item.className='cue';
   const small=document.createElement('small');small.textContent=fmt(c.t);item.append(small);
   const title=document.createElement('strong');title.textContent=c.title+' · '+c.pose;item.append(title);
   const desc=document.createElement('p');desc.textContent=c.detail;item.append(desc);
   item.addEventListener('click',()=>{if(state.duration){audio.currentTime=c.t;audio.pause();state.playing=false;updateControls();$('seek').value=Math.round(c.t/state.duration*1000);}});
   el.append(item);}
}
function drawWave(){
 wctx.fillStyle='#081426';wctx.fillRect(0,0,wave.width,wave.height);
 wctx.strokeStyle='rgba(93,149,205,.3)';wctx.lineWidth=1;
 wctx.beginPath();wctx.moveTo(0,63);wctx.lineTo(900,63);wctx.stroke();
 if(!state.env.length){wctx.fillStyle='#849cb9';wctx.font='19px system-ui';wctx.textAlign='center';wctx.fillText('Audio energy waveform',450,68);wctx.textAlign='left';return;}
 const env=state.env;
 for(let x=0;x<900;x++){
   const a=Math.floor(x/900*env.length),b=Math.min(env.length,Math.max(a+1,Math.floor((x+1)/900*env.length)));
   let m=0;for(let i=a;i<b;i++)m=Math.max(m,env[i]);
   const h=2+m*52;
   wctx.fillStyle='#5ed9ff';wctx.fillRect(x,63-h,1,2*h);
 }
 for(let c of state.cues){let x=c.t/state.duration*900;wctx.fillStyle='#ffb56a';wctx.fillRect(x,0,2,126);}
}
function parseContent(){
 state.script=$('script').value.trim();state.headline=$('headline').value.trim();
 state.words=mapWords(state.script,state.speech,state.duration);
 state.visemes=estimateVisemes(state.words,state.speech,state.duration);
 state.timingSource='estimated';
 $('scriptHint').textContent=state.script?state.words.length+' words scheduled across detected speech sections (approximate timing).':'Audio-only mode; voice drives mouth energy and joints, no word captions.';
 if(state.duration)makeCues();
}
async function loadAudio(blob,name){
 try{
  $('status').textContent='Analyzing audio…';state.analyzing=true;state.playing=false;audio.pause();updateControls();
  if(state.objectURL)URL.revokeObjectURL(state.objectURL);
  state.objectURL=URL.createObjectURL(blob);
  audio.src=state.objectURL;audio.load();
  const ac=await audioContext();
  const arr=await blob.arrayBuffer();
  let decoded=await ac.decodeAudioData(arr.slice(0));
  state.file={name};state.duration=decoded.duration;state.buffer=decoded;
  const analysis=audioStats(decoded);
  state.env=analysis.env;state.speech=analysis.speech;state.pauses=analysis.pauses;state.emphasis=analysis.emphasis;
  state.t=0;state.lastT=0;state.words=[];parseContent();drawWave();
  $('audioName').textContent=name+' · '+fmt(decoded.duration);
  $('status').textContent='Voice analyzed';
  $('exportState').textContent='Ready to record this performance. Start recording from the Export tab. Browser support determines MP4 or WebM.';
  audio.currentTime=0;state.analyzing=false;updateControls();
 }catch(e){state.analyzing=false;$('status').textContent='Audio could not be decoded';$('exportState').textContent=String(e);$('liveAction').textContent='Could not read this audio codec. Try MP3 or WAV.';}
}
$('audioFile').addEventListener('change',e=>{const f=e.target.files?.[0];if(f)loadAudio(f,f.name);});
function createDemo(){
 const sr=22050,dur=10,samples=sr*dur,data=new Float32Array(samples);
 for(let i=0;i<samples;i++){
  const t=i/sr,pause=Math.floor(t*2.2)%5===4||t>8.6?0:1;
  const env=.19*pause*(.5+.5*Math.sin(2*Math.PI*4.2*t)**2);
  data[i]=env*(Math.sin(t*2*Math.PI*(160+25*Math.sin(t*3)))+.18*Math.sin(t*2*Math.PI*360));
 }
 const bytes=new ArrayBuffer(44+samples*2),view=new DataView(bytes);
 const str=(idx,s)=>{for(let i=0;i<s.length;i++)view.setUint8(idx+i,s.charCodeAt(i));};
 str(0,'RIFF');view.setUint32(4,bytes.byteLength-8,true);str(8,'WAVE');str(12,'fmt ');
 view.setUint32(16,16,true);view.setUint16(20,1,true);view.setUint16(22,1,true);view.setUint32(24,sr,true);view.setUint32(28,sr*2,true);view.setUint16(32,2,true);view.setUint16(34,16,true);str(36,'data');view.setUint32(40,samples*2,true);
 for(let i=0;i<samples;i++)view.setInt16(44+i*2,clamp(data[i],-1,1)*32767,true);
 return new Blob([bytes],{type:'audio/wav'});
}
$('demo').addEventListener('click',()=>{state.demo=true;if(!$('script').value.trim())$('script').value='Welcome to Robot Studio. Our new 3D presenter can gesture while audio plays. This sample uses synthetic tones, not a spoken voice.';loadAudio(createDemo(),'Synthetic movement demo.wav');});
$('apply').addEventListener('click',parseContent);
$('clearScript').addEventListener('click',()=>{$('script').value='';parseContent();});
$('headline').addEventListener('change',parseContent);
$('storyFile').addEventListener('change',e=>{
 const f=e.target.files?.[0];if(!f)return;
 if(state.storyURL)URL.revokeObjectURL(state.storyURL);
 const img=new Image();state.storyURL=URL.createObjectURL(f);
 img.onload=()=>{state.story=img;parseContent();};img.onerror=()=>{$('liveAction').textContent='Could not load story photo.';};
 img.src=state.storyURL;
});
$('play').addEventListener('click',async()=>{
 if(!state.duration)return;
 if(audio.paused){
  try{const ac=await audioContext();await ac.resume();await audio.play();state.playing=true;}catch(err){$('liveAction').textContent='Playback blocked: '+String(err.message||err);}
 }else{audio.pause();state.playing=false;}
 updateControls();
});
audio.addEventListener('ended',()=>{state.playing=false;updateControls();if(state.record)stopRecord();});
audio.addEventListener('pause',()=>{state.playing=false;updateControls();});
audio.addEventListener('play',()=>{state.playing=true;updateControls();});
$('seek').addEventListener('pointerdown',()=>{state.uiDrag=true;});
$('seek').addEventListener('input',e=>{if(state.duration){audio.currentTime=e.target.value/1000*state.duration;$('clock').textContent=fmt(audio.currentTime)+' / '+fmt(state.duration);}});
for(let event of ['pointerup','pointercancel','change'])$('seek').addEventListener(event,()=>{state.uiDrag=false;});
// iPhone-first orbit controls. Events are on the preview ONLY: outside it,
// page scrolling and buttons keep working as normal. 1 finger = full 360
// rotation + tilt, 2 fingers = pinch zoom. Also allow wheel / explicit buttons.
const stage=canvas;
const touches=new Map();
let lastGesture=null;
// Update the control readout synchronously. iPhone canvas rendering and
// headless WebGL may draw more slowly than touch / button events arrive.
const writeCameraState=()=>{
 stage.dataset.cameraYaw=state.angle.toFixed(3);
 stage.dataset.cameraPitch=state.pitch.toFixed(3);
 stage.dataset.cameraDistance=state.orbitDistance.toFixed(3);
};
const zoomCamera=amount=>{
 state.orbitDistance=clamp(state.orbitDistance*amount,3.15,14);
 writeCameraState();
};
const resetCamera=()=>{
 state.angle=0;state.pitch=.042;state.orbitDistance=8.35;writeCameraState();
};
writeCameraState();
const gestureSnapshot=()=>{
 const pts=[...touches.values()];
 if(pts.length===1)return {n:1,x:pts[0].x,y:pts[0].y};
 if(pts.length>=2){
  const a=pts[0],b=pts[1];
  return {n:2,x:(a.x+b.x)/2,y:(a.y+b.y)/2,
          spread:Math.max(10,Math.hypot(a.x-b.x,a.y-b.y))};
 }
 return null;
};
stage.addEventListener('pointerdown',e=>{
 if(e.pointerType==='mouse'&&e.button!==0)return;
 e.preventDefault();
 touches.set(e.pointerId,{x:e.clientX,y:e.clientY});
 try{stage.setPointerCapture(e.pointerId)}catch(_){}
 lastGesture=gestureSnapshot();
});
stage.addEventListener('pointermove',e=>{
 if(!touches.has(e.pointerId))return;
 e.preventDefault();
 touches.set(e.pointerId,{x:e.clientX,y:e.clientY});
 const g=gestureSnapshot();
 if(g&&lastGesture&&g.n===lastGesture.n){
  if(g.n===1){
   // Horizontal movement is deliberately unrestricted: full rotations.
   state.angle+=(g.x-lastGesture.x)*.012;
   state.pitch=clamp(state.pitch+(g.y-lastGesture.y)*.0085,-1.535,1.535);
  }else{
   // Pinch out = closer to robot; pinch in = further away.
   zoomCamera(lastGesture.spread/g.spread);
   state.angle+=(g.x-lastGesture.x)*.004;
   state.pitch=clamp(state.pitch+(g.y-lastGesture.y)*.003,-1.535,1.535);
  }
 }
 writeCameraState();
 lastGesture=g;
});
const endGesture=e=>{
 touches.delete(e.pointerId);
 lastGesture=gestureSnapshot();
};
stage.addEventListener('pointerup',endGesture);
stage.addEventListener('pointercancel',endGesture);
stage.addEventListener('lostpointercapture',endGesture);
stage.addEventListener('wheel',e=>{
 e.preventDefault();
 zoomCamera(Math.exp(clamp(e.deltaY,-180,180)*.002));
},{passive:false});
stage.addEventListener('dblclick',e=>{e.preventDefault();resetCamera();});
document.querySelectorAll('[data-camera-control]').forEach(btn=>
 btn.addEventListener('click',()=>{
  switch(btn.dataset.cameraControl){
   case 'left': state.angle-=.34;break;
   case 'right': state.angle+=.34;break;
   case 'in': zoomCamera(.79);break;
   case 'out': zoomCamera(1.27);break;
   case 'top': state.pitch=1.535;state.orbitDistance=6.9;break;
   case 'reset': resetCamera();break;
  }
  writeCameraState();
 }));
$('resetCamera').addEventListener('click',resetCamera);
$('previewPose').addEventListener('click',()=>{const poses=['wave','present','point','neutral'];state.pose=poses[state.poseIndex++%poses.length];state.poseUntil=performance.now()+2500;});
document.querySelectorAll('[data-pose]').forEach(b=>b.addEventListener('click',()=>{state.pose=b.dataset.pose;state.poseUntil=performance.now()+3200;if(state.duration){audio.pause();state.playing=false;updateControls();}}));
for(let name of ['mouth','gestures','captions','blink','float','camera'])$(name).addEventListener('change',e=>settings[name]=e.target.checked);
$('mouthShape').addEventListener('change',e=>state.manualShape=e.target.value);
$('expression').addEventListener('change',e=>state.expression=e.target.value);
$('timingFile').addEventListener('change',async e=>{
 const file=e.target.files?.[0];if(!file)return;
 try{
  if(!state.duration)throw Error('Load the matching voice audio first.');
  if(file.size>2*1024*1024)throw Error('Timing file must be smaller than 2 MB.');
  const timing=validateTiming(JSON.parse(await file.text()),state.duration);
  state.visemes=timing.visemes;if(timing.words.length)state.words=timing.words;
  state.timingSource=timing.source;
  $('scriptHint').textContent='Imported speech timings loaded. Applying a new script returns to estimated timing.';
 }catch(err){$('scriptHint').textContent=err.message;}
 e.target.value='';
});
$('energy').addEventListener('input',e=>{settings.energy=+e.target.value/100;$('energyValue').value=e.target.value+'%';});
document.querySelectorAll('[data-tab]').forEach(b=>b.addEventListener('click',()=>{
 document.querySelectorAll('[data-tab]').forEach(x=>x.classList.toggle('active',x===b));
 document.querySelectorAll('[data-view]').forEach(x=>x.hidden=x.dataset.view!==b.dataset.tab);
}));
function exportJSON(){
 const obj={schema:'robot-studio-performance/v3',version:3,engine:'Robot Studio 3D',fileName:state.file?.name||'',duration:state.duration,
 settings:{...settings,expression:state.expression},transcript:state.script,headline:state.headline,
 visemes:state.visemes,timingSource:state.timingSource,frames:state.env.map((level,i)=>({t:i/FPS,level})),
 speech:state.speech,pauses:state.pauses,emphasis:state.emphasis,cues:state.cues,words:state.words,
 note:'Speech/word timestamps estimated locally from RMS; not a certified transcription or forced alignment.'};
 const blob=new Blob([JSON.stringify(obj,null,2)],{type:'application/json'});saveFile(blob,'robot-director.json');
}
function saveFile(blob,name){
 const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=name;a.rel='noopener';
 document.body.append(a);a.click();a.remove();
 setTimeout(()=>URL.revokeObjectURL(url),60000);
}
$('downloadPlan').addEventListener('click',exportJSON);
function setRecordResolution(scale){
 scale=scale===2?2:1;
 if(captureScale===scale)return;
 captureScale=scale;
 canvas.width=VW*scale;canvas.height=VH*scale;
 ctx.setTransform(scale,0,0,scale,0,0);
 if(renderer)renderer.setSize(VW*scale,VH*scale,false);
}
async function captureAudio(){
 const ac=await audioContext();await ac.resume();
 if(!state.mediaSource){
   state.mediaSource=ac.createMediaElementSource(audio);
   state.destination=ac.createMediaStreamDestination();
   state.mediaSource.connect(state.destination);
   state.mediaSource.connect(ac.destination);
 }
 return state.destination.stream;
}
function preferredMime(){
 if(typeof MediaRecorder==='undefined')return null;
 const all=['video/mp4;codecs=avc1.42E01E,mp4a.40.2','video/mp4','video/webm;codecs=vp9,opus','video/webm;codecs=vp8,opus','video/webm'];
 return all.find(x=>MediaRecorder.isTypeSupported(x))||'';
}
async function beginRecord(){
 if(!state.duration||!state.ready)return;
 const output=$('exportState');
 try{
  if(!canvas.captureStream)throw Error('Canvas video capture is not supported in this browser. Try Chrome on desktop, or export the Director JSON.');
  const mime=preferredMime();
  if(mime===null)throw Error('MediaRecorder is not available on this browser.');
  const input=await captureAudio();
  setRecordResolution(Number($('quality').value));
  audio.pause();state.playing=false;audio.currentTime=0;
  const stream=canvas.captureStream(30);
  const tracks=[...stream.getVideoTracks(),...input.getAudioTracks()];
  if(!tracks.some(x=>x.kind==='video'))throw Error('No video track was captured.');
  const merged=new MediaStream(tracks);
  const chunks=[];
  const opts=mime?{mimeType:mime,videoBitsPerSecond:4_000_000,audioBitsPerSecond:128000}:{videoBitsPerSecond:4_000_000};
  const rec=new MediaRecorder(merged,opts);
  state.record={rec,stream,merged,chunks};state.recordStarted=true;
  rec.addEventListener('dataavailable',e=>{if(e.data?.size)chunks.push(e.data);});
  rec.addEventListener('error',e=>{output.textContent='Recording error: '+String(e.error?.message||'unknown');});
  rec.addEventListener('stop',()=>{
   const blob=new Blob(chunks,{type:rec.mimeType||mime||'video/webm'});
   stream.getVideoTracks().forEach(track=>track.stop());
   setRecordResolution(1);
   state.record=null;state.recordStarted=false;
   $('record').textContent='● Record video';$('record').disabled=false;
   if(blob.size<1024){output.textContent='Recording ended without a usable file. Try another browser.';return;}
   const ext=blob.type.includes('mp4')?'mp4':'webm';
   saveFile(blob,'robot-studio-3d-'+Date.now()+'.'+ext);
   output.textContent='Recording saved ('+(blob.size/1024/1024).toFixed(1)+' MB, '+ext.toUpperCase()+'). If iPhone does not save automatically, use the browser Downloads list.';
  });
  rec.start(300);
  // Once recording begins, start the actual media element. Its audio is connected to the recorder.
  try{await audio.play();}catch(err){rec.stop();throw err;}
  output.textContent='Recording vertical '+canvas.width+'×'+canvas.height+' with linked audio. Let the track finish for a complete video.';
  $('record').textContent='■ Stop recording';
  state.playing=true;updateControls();
 }catch(err){output.textContent='Recording unavailable: '+String(err.message||err);state.record=null;state.recordStarted=false;setRecordResolution(1);$('record').textContent='● Record video';updateControls();}
}
function stopRecord(){const o=state.record;if(!o)return;try{if(o.rec.state!=='inactive'){o.rec.requestData();o.rec.stop();}}catch(err){$('exportState').textContent='Could not stop recorder: '+err.message;}}
$('record').addEventListener('click',()=>{if(state.record){audio.pause();stopRecord();}else beginRecord();});
drawWave();updateControls();
