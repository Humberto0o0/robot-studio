const {chromium}=require('playwright');
const fs=require('fs');
setTimeout(()=>{console.error('SMOKE TIMEOUT after 85 seconds');process.exit(2);},85000).unref();
const assert=require('assert');
const data=fs.readFileSync('models/robot-prototype.glb');
const jsonSize=data.readUInt32LE(12);
const gltf=JSON.parse(data.toString('utf8',20,20+jsonSize));
const relevant=(gltf.nodes||[]).map(x=>x.name).filter(x=>/eye|mouth|led|helmet|visor|eyebrow|smile/i.test(x));
console.log('GLB face-node diagnostics:',JSON.stringify(relevant));
console.log('GLB bytes',data.length,'nodes',(gltf.nodes||[]).length);
const modelNames=(gltf.nodes||[]).map(x=>x.name||'');
const suitChecks=['Hand-tailored satin lapel L','Hand-tailored satin lapel R','Tailored jacket front L','Tailored jacket front R','Orange necktie diamond knot','Shoulder rounded cobalt fabric cap L','Shoulder rounded cobalt fabric cap R'];
for(const name of suitChecks) assert(modelNames.includes(name),'New Blender suit object absent: '+name);
assert(!modelNames.some(n=>/Cute eyebrow|Glass upper (left|right) reflection/.test(n)),'Duplicate eyebrow-like geometry still present');
assert((gltf.materials||[]).some(m=>/Royal blue woven suit fabric/.test(m.name||'')),'Woven suit fabric material missing');
console.log('PASS NEW SUIT geometry and single LED eye expression');
const handChecks=[
 'Shoulder_L','Shoulder_R','Elbow_L','Elbow_R','Wrist_L','Wrist_R',
 'Tailored upper sleeve L','Tailored upper sleeve R',
 'Tailored forearm L','Tailored forearm R',
 'Hand_almoured_ceramic_palm_L','Hand_almoured_ceramic_palm_R',
 'Thumb_R_Root','Thumb_L_Root',
 'Finger_R_0_Knuckle','Finger_R_1_Knuckle','Finger_R_2_Knuckle','Finger_R_3_Knuckle',
 'Finger_L_0_Knuckle','Finger_L_1_Knuckle','Finger_L_2_Knuckle','Finger_L_3_Knuckle',
 'Microphone steel capsule grille'
];
for(const name of handChecks) assert(modelNames.includes(name),'Missing articulated limb node: '+name);
assert(!modelNames.some(n=>/Finger [LR] [0-9]$/.test(n)),'Old straight rod fingers still visible');
console.log('PASS V4 articulated shoulders, elbows, wrists, 8 finger knuckles and thumbs');
for(const side of ['L','R']){
 for(const suffix of ['Continuous cobalt wrist extension','Cuff seamless cobalt sleeve end','Cuff slim porcelain transition','Cuff thin cobalt trim','Wrist hidden mechanical socket']){
  const name=suffix+' '+side;
  assert(modelNames.includes(name),'Missing V7 seamless sleeve geometry: '+name);
 }
 assert(!modelNames.includes('Wrist under-cuff mechanism '+side),'Exposed old wrist joint remains on '+side);
}
console.log('PASS V7 hidden mechanical wrist joints and continuous cobalt sleeves');
for(const j of [0,1,2,3]){
 for(const segment of ['upper white shell','distal ceramic','middle graphite pivot']){
  assert(modelNames.includes('Finger R '+j+' '+segment),
    'Missing V9 tapered finger '+j+' '+segment);
 }
 assert(modelNames.includes('Finger_R_'+j+'_Tip'),'Missing independent distal pivot '+j);
}
console.log('V9_THUMB_NODES',JSON.stringify(modelNames.filter(n=>/Thumb R|Thumb_R|Finger R 0/i.test(n))));
assert(modelNames.includes('Thumb R ceramic fingertip'),'Missing V9 rounded ceramic thumb');
console.log('PASS V9 hand with individually controlled tapered fingers and sculpted thumb');

(async()=>{
 const browser=await chromium.launch({headless:true,channel:'chrome',args:['--no-sandbox','--enable-webgl','--enable-unsafe-swiftshader','--use-gl=angle','--use-angle=swiftshader']});
 const context=await browser.newContext({viewport:{width:390,height:844},deviceScaleFactor:2,isMobile:true,hasTouch:true,acceptDownloads:true});
 const page=await context.newPage();const errors=[];
 page.on('pageerror',error=>{errors.push(String(error));console.log('PAGEERROR',String(error))});
 page.on('console',message=>{if(message.type()==='error')console.log('CONSOLE',message.text())});
 fs.mkdirSync('test-results',{recursive:true});
 console.log('Launching Chrome at 390×844');
 await page.goto('http://127.0.0.1:8765/studio.html',{waitUntil:'domcontentloaded',timeout:30000});
 console.log('Navigation done. status:',await page.locator('#status').innerText());
 await page.waitForFunction(()=>document.getElementById('status').textContent.includes('3D ready'),null,{timeout:20000}).catch(async()=>{console.log('STATUS',await page.locator('#status').innerText());});
 const status=await page.locator('#status').innerText();
 assert(status.includes('3D ready'),'Real glTF model did not load: '+status);
 assert(status.includes('V2 expressive helmet'),'Premium V2 Blender head/visor geometry was not detected: '+status);
 console.log('PASS 3D model loaded',status);
 await page.waitForTimeout(900);
 await page.screenshot({path:'test-results/v2-helmet-iphone.png',fullPage:false});
 console.log('PASS real Blender V2 expressive visor and helmet detected');
 await page.locator('#demo').click();
 await page.waitForFunction(()=>document.getElementById('status').textContent==='Voice analyzed',{timeout:20000});
 console.log('PASS demo audio decoded');
 const speech=await page.locator('#speechCount').innerText();
 await page.locator('[data-tab="direct"]').click();
 const count=await page.locator('#gestureCount').innerText();
 assert(+count>=1,'Missing gesture cues');
 console.log('PASS timeline generated','speech',speech,'gestures',count);
 await page.locator('[data-pose="present"]').click();
 await page.locator('[data-tab="create"]').click();
 await page.screenshot({path:'test-results/robot-studio-iphone.png',fullPage:true});
 await page.locator('#play').click();
 await page.waitForTimeout(700);
 const elapsed=await page.locator('#clock').innerText();
 const audioPosition=await page.locator('#audio').evaluate(el=>el.currentTime);
 assert(audioPosition>0.2,'Audio playback is not running: '+audioPosition+' / '+elapsed);
 console.log('PASS audio playback',audioPosition.toFixed(3)+'s',elapsed);
 await page.locator('#play').click();
 await page.locator('[data-tab="export"]').click();
 await page.locator('#downloadPlan').click();
 console.log('PASS director JSON export');
 await page.locator('#record').click();
 await page.waitForFunction(()=>document.getElementById('record').textContent.includes('Stop recording'),null,{timeout:18000});
 const dims=await page.locator('#stage').evaluate(el=>[el.width,el.height]);
 assert.deepStrictEqual(dims,[1080,1920],'Recording canvas is not Full HD');
 console.log('PASS Full HD recording started',dims.join('x'));
 await page.waitForTimeout(1300);
 await page.locator('#record').click();
 await page.waitForFunction(()=>document.getElementById('exportState').textContent.includes('Recording saved'),null,{timeout:18000});
 const post=await page.locator('#stage').evaluate(el=>[el.width,el.height]);
 assert.deepStrictEqual(post,[540,960],'Preview did not return to light-resolution mode');
 console.log('PASS complete media capture and restoration to preview mode');
 assert(!errors.length,'Browser page exceptions: '+errors.join('; '));
 await browser.close();
 console.log('ALL MOBILE 3D BROWSER SMOKE TESTS PASSED');
})().catch(e=>{console.error('SMOKE FAILED',e.stack||e);process.exit(1);});
