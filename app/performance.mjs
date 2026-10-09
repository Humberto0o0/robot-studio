// Portable timeline contract; no DOM, network or model dependencies.
export const SPEECH_SHAPES=['A','E','O','U','M','F','S','SMILE'];
const clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
export function soundShapes(word){
 const pairs={sh:'S',ch:'S',th:'S',ee:'E',ea:'E',oo:'U',ou:'O',ow:'O',ai:'E'};
 const letters=word.toLowerCase().replace(/[^a-z]/g,'');const out=[];
 for(let i=0;i<letters.length;i++){
  let shape=pairs[letters.slice(i,i+2)];
  if(shape)i++;else{const c=letters[i];shape=/[mbp]/.test(c)?'M':/[fv]/.test(c)?'F':/[ouqw]/.test(c)?'O':/[eiy]/.test(c)?'E':c==='a'?'A':'S';}
  if(shape!==out.at(-1))out.push(shape);
 }
 return out.length?out:['S'];
}
export function estimateVisemes(words,speech,duration){
 const result=[];
 words.forEach((word,i)=>{
  const start=word.time??word.start;
  const end=word.end??words[i+1]?.time??words[i+1]?.start??duration;
  const spans=speech.map(s=>({start:Math.max(start,s.start),end:Math.min(end,s.end)})).filter(s=>s.end>s.start);
  const total=spans.reduce((a,s)=>a+s.end-s.start,0);if(!total)return;
  const shapes=soundShapes(word.word??word.text??'');let progress=0;
  for(const span of spans){
   const spanStart=progress;progress+=span.end-span.start;
   shapes.forEach((shape,j)=>{
    const a=Math.max(spanStart,total*j/shapes.length),b=Math.min(progress,total*(j+1)/shapes.length);
    if(b>a)result.push({time:span.start+a-spanStart,end:span.start+b-spanStart,shape});
   });
  }
 });return result.sort((a,b)=>a.time-b.time);
}
export function validateTiming(input,duration){
 if(input?.schema!=='robot-studio-timing/v1')throw Error('Expected robot-studio-timing/v1 timing file.');
 if(!Number.isFinite(input.duration)||Math.abs(input.duration-duration)>.25)throw Error('Timing duration does not match this audio.');
 if(!Array.isArray(input.visemes)||input.visemes.length>30000)throw Error('Invalid speech cues.');
 let last=0;
 const visemes=input.visemes.map(v=>{
  if(!SPEECH_SHAPES.includes(v.shape)||!Number.isFinite(v.time)||!Number.isFinite(v.end)||v.time<last||v.end<=v.time||v.end>duration+.025)throw Error('Speech cues must be ordered, non-overlapping and inside the audio.');
  last=v.end;return {time:v.time,end:Math.min(v.end,duration),shape:v.shape};
 });
 let previous=0;
 const words=(input.words??[]).map(w=>{
  if(typeof w.text!=='string'||w.text.length>200||!Number.isFinite(w.start)||!Number.isFinite(w.end)||w.start<previous||w.end<=w.start||w.end>duration+.025)throw Error('Invalid word timings.');
  previous=w.end;return {word:w.text,time:w.start,end:w.end};
 });
 return {visemes,words,source:'imported'};
}
export function shapeAt(cues,t){
 let lo=0,hi=cues.length-1;
 while(lo<=hi){const m=(lo+hi)>>1;if(cues[m].time<=t)lo=m+1;else hi=m-1;}
 const c=cues[hi];return c&&t<c.end?c.shape:'REST';
}
export function blinkAt(t){
 // Fixed, reproducible beats. Brief eyelid closure + slower reopening.
 const phase=((t+1.2)%4.6);
 if(phase>.19)return 0;
 return phase<.065?phase/.065:clamp(1-(phase-.065)/.125,0,1);
}
