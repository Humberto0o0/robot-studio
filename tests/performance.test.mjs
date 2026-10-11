import assert from 'node:assert/strict';
import {estimateVisemes,validateTiming,shapeAt,blinkAt,presenterMotion,motionBlend} from '../app/performance.mjs';
const cues=estimateVisemes([{word:'Hello',time:0},{word:'Bob',time:1.5}],[{start:.1,end:.7},{start:1.5,end:2.1}],2.5);
assert(cues.length>2);
assert(cues.every(c=>(c.time>=.1&&c.end<=.7)||(c.time>=1.5&&c.end<=2.1)),'Estimated mouth must not speak through pauses');
assert.equal(shapeAt(cues,1),'REST');assert.equal(shapeAt(cues,2.4),'REST');
assert.equal(shapeAt([{time:.5,end:1,shape:'M'}],.6),'M');
assert.throws(()=>validateTiming({schema:'robot-studio-timing/v1',duration:2,visemes:[{time:0,end:1,shape:'A'},{time:.5,end:1.2,shape:'E'}]},2));
assert.throws(()=>validateTiming({schema:'robot-studio-timing/v1',duration:10,visemes:[]},2));
const valid=validateTiming({schema:'robot-studio-timing/v1',duration:2,visemes:[{time:.3,end:.5,shape:'M'}]},2);
assert.equal(valid.source,'imported');assert.equal(valid.visemes[0].shape,'M');
assert(blinkAt(3.45)>0);assert.equal(blinkAt(0),0);
console.log('PASS speech silence, ordered timing imports, closed consonants and deterministic blink');

// Microphone joints must remain stable across gesture types and pulse extremes.
for(const pose of ['neutral','wave','present','point'])for(let i=0;i<240;i++){
 const m=presenterMotion(i/30,pose,(i%2));
 assert(Math.abs(m.micShoulder+m.micElbow+m.micWrist+.018)<1e-10,'Microphone loses orientation during lift');
 assert(Math.abs(m.micElbow)<=.065,'Microphone lift exceeds restrained range');
 assert(Math.abs(m.wrist)<=.15,'Wrist wave exceeds restrained presenter range');
}
const settle=fps=>{let x=0;for(let i=0;i<fps;i++)x+=(1-x)*motionBlend(1/fps);return x;};
assert(Math.abs(settle(30)-settle(60))<1e-9,'Motion easing depends on frame rate');
console.log('PASS stable microphone chain and frame-rate-independent easing');
