const {chromium}=require('playwright');
const fs=require('fs');
setTimeout(()=>{console.error('SMOKE TIMEOUT after 210 seconds');process.exit(2);},210000).unref();
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
console.log('PASS suit geometry and no duplicate legacy brows');
for(const side of ['L','R']){
 for(const name of ['Eye pupil ','Eye catch ','Expressive LED brow '])assert(modelNames.includes(name+side),'Missing expressive face '+name+side);
 const eye=gltf.nodes.find(n=>n.name==='Eye emissive LED matrix '+side);
 for(const shape of ['FRIENDLY','SURPRISED','BLINK','LOOK_RIGHT'])assert(gltf.meshes[eye.mesh].extras.targetNames.includes(shape),'Missing eye expression '+shape);
}
console.log('PASS V17 open LED eyes, gaze and expressive brows');
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
// User-preferred presenting hand comes from the verified V8 design.
for(let j=0;j<4;j++){
 for(const item of ['upper white shell','distal ceramic','middle graphite pivot','rounded black pad']){
  assert(modelNames.includes('Finger R '+j+' '+item),'Missing restored V8 presenting finger '+j+' '+item);
 }
 assert(modelNames.includes('Finger_R_'+j+'_Knuckle'),'Missing presenting knuckle '+j);
 assert(modelNames.includes('Finger L '+j+' curled white segment'),'Missing microphone finger '+j);
 assert(modelNames.includes('Finger L '+j+' curved porcelain fingertip'),'Missing clean gripping end '+j);
 assert(modelNames.includes('Finger_L_'+j+'_Knuckle'),'Missing microphone knuckle '+j);
}
assert(modelNames.includes('Thumb R porcelain base'),'Missing restored presenting thumb');
assert(modelNames.includes('Thumb_L_Root'),'Missing opposing microphone thumb');
assert(!modelNames.some(n=>/Finger L [0-3] (proximal porcelain curl|narrow graphite first joint|cyan joint inlay)/.test(n)),'Old duplicated microphone finger layers remain');
assert(modelNames.filter(n=>/^Finger L [0-3] curled white segment$/.test(n)).length===4,
 'Exactly four white gripping fingers must be exported');
assert(modelNames.filter(n=>/^Thumb_L_Root$/.test(n)).length===1,
 'Exactly one microphone thumb must be exported');
console.log('PASS V10 restored presenting hand and four clean microphone fingers plus thumb');
// The V11 thumb is located ABOVE the microphone fingers rather than under
// the little finger. Check its authored position and exported ceramic meshes.
for (const j of [0,1,2,3]){
 assert(modelNames.includes('Finger L '+j+' soft hinge'),'Missing fine ceramic finger hinge '+j);
 assert(modelNames.includes('Finger L '+j+' rounded ceramic pad'),'Missing matching ceramic fingertip '+j);
}
assert(modelNames.includes('Thumb L upward ceramic tip'),'Thumb-up microphone grip was not exported');
assert(modelNames.includes('Thumb L high recessed hinge'),'Microphone thumb is not seated high on the palm');
assert(modelNames.filter(n=>/^Finger L [0-3] recessed graphite root$/.test(n)).length===4,
 'Must have exactly four articulated microphone fingers');
console.log('PASS V11 matched porcelain fingers and high opposable microphone thumb');
assert(modelNames.includes('Hand_almoured_ceramic_palm_L'),'Mirrored gripper porcelain shell missing');
assert(modelNames.includes('Hand_almoured_ceramic_palm_R'),'Original open hand shell missing');
assert(!modelNames.includes('Palm graphite perimeter L'),
 'Mic palm inner black insert is still visible as exterior geometry');
assert(!modelNames.includes('Hand pearlescent knuckle plate L'),
 'Mic palm extra knuckle shell is still layered outside the glove');
assert(modelNames.includes('Palm graphite perimeter R'),
 'Approved open hand inner lining was removed by mistake');
assert(modelNames.includes('Hand pearlescent knuckle plate R'),
 'Approved presenting palm was modified');
console.log('PASS single ceramic microphone palm with no duplicate layers');
for(let j=0;j<4;j++){
 for(const suffix of ['middle ceramic phalanx','distal graphite hinge'])
  assert(modelNames.includes('Finger L '+j+' '+suffix),'Missing three-segment grip: '+suffix);
 assert(modelNames.includes('Finger_L_'+j+'_Middle'),'Missing middle articulation pivot');
}
console.log('PASS V15 three phalanges and two hinge seams per gripping finger');
for(const name of ['Mouth rim precision outline','Mouth open burgundy recess','Mouth warm coral tongue','Mouth upper ivory smile']){
 const node=gltf.nodes.find(n=>n.name===name),mesh=gltf.meshes[node.mesh];
 for(const shape of ['A','E','O','U','M','F','S','SMILE'])
  assert(mesh.extras?.targetNames?.includes(shape),'Missing exported speech shape '+name+' / '+shape);
}
assert(gltf.meshes.some(m=>m.extras?.targetNames?.includes('BLINK')),'Blink morph not exported');
assert(modelNames.includes('Microphone unified woven grille'),'Static microphone grille is not batched');
console.log('PASS exported speech and eye morph targets, batched microphone grille');


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
 assert(status.includes('Speech & expressions'),'Premium V2 Blender head/visor geometry was not detected: '+status);
 console.log('PASS 3D model loaded',status);
 await page.waitForTimeout(900);
 await page.screenshot({path:'test-results/v2-helmet-iphone.png',fullPage:false});
 console.log('PASS real Blender V2 expressive visor and helmet detected');
 // Mobile 3D camera: verify actual orbit/zoom state, not decorative buttons.
 const stage=page.locator('#stage');
 assert.strictEqual(await stage.evaluate(el=>getComputedStyle(el).touchAction),'none',
  'Safari may intercept preview touch gestures');
 const readCamera=async()=>stage.evaluate(el=>({
  yaw:Number(el.dataset.cameraYaw),pitch:Number(el.dataset.cameraPitch),
  distance:Number(el.dataset.cameraDistance)
 }));
 const initial=await readCamera();
 assert(Math.abs(initial.distance-8.35)<.1,'Initial camera distance is incorrect');
 await page.locator('[data-camera-control="right"]').click();
 await page.waitForTimeout(120);
 let current=await readCamera();
 assert(current.yaw>initial.yaw+.3,'Right turn button does not orbit the robot');
 await page.locator('[data-camera-control="in"]').click();
 await page.waitForTimeout(120);
 current=await readCamera();
 console.log('CAMERA ZOOM DIAGNOSTIC',JSON.stringify({initial,current,markup:await page.locator('[data-camera-control="in"]').evaluate(el=>({value:el.dataset.cameraControl,html:el.outerHTML}))}));
 assert(current.distance<initial.distance-1,'Zoom-in button did not move camera closer: '+JSON.stringify({initial,current}));
 await page.locator('[data-camera-control="reset"]').click();
 await page.waitForTimeout(100);
 current=await readCamera();
 assert(Math.abs(current.yaw)<.02 && Math.abs(current.distance-8.35)<.1,
  'Camera reset did not restore original zoom/orbit');
 const gesture=await stage.evaluate(el=>{
  const touch=(event,id,x,y)=>el.dispatchEvent(new PointerEvent(event,{
   bubbles:true,cancelable:true,pointerId:id,pointerType:'touch',
   isPrimary:id===1,clientX:x,clientY:y,button:0,buttons:1}));
  touch('pointerdown',1,90,220);
  touch('pointermove',1,180,275); // drag horizontally and vertically
  touch('pointerup',1,180,275);
  return true;
 });
 await page.waitForTimeout(110);
 current=await readCamera();
 assert(current.yaw>.9 && current.pitch>.4,'Touch drag did not turn and tilt the camera');
 await page.locator('[data-camera-control="reset"]').click();
 await stage.evaluate(el=>{
  const touch=(event,id,x,y)=>el.dispatchEvent(new PointerEvent(event,{
   bubbles:true,cancelable:true,pointerId:id,pointerType:'touch',
   isPrimary:id===1,clientX:x,clientY:y,button:0,buttons:1}));
  touch('pointerdown',1,120,300);
  touch('pointerdown',2,220,300);
  touch('pointermove',2,290,300); // fingers separate = pinch zoom in
  touch('pointerup',2,290,300);
  touch('pointerup',1,120,300);
 });
 await page.waitForTimeout(110);
 current=await readCamera();
 assert(current.distance<6,'Pinch gesture did not zoom in: '+current.distance);
 await page.locator('[data-camera-control="reset"]').click();
 await page.waitForTimeout(90);
 // Vertical overhead inspection is a separate requirement, not satisfied by
 // the previous 64-degree orbit cap.
 await page.locator('[data-camera-control="top"]').click();
 await page.waitForTimeout(350);
 current=await readCamera();
 assert(current.pitch>1.49 && current.pitch<1.56,
   'Top View did not reach an overhead angle: '+JSON.stringify(current));
 assert(current.distance<=7,'Top View should move close enough to inspect helmet top');
 await page.screenshot({path:'test-results/top-view-iphone.png',fullPage:false});
 await page.locator('[data-camera-control="reset"]').click();
 await page.waitForTimeout(100);
 current=await readCamera();
 assert(Math.abs(current.pitch-.042)<.02 && Math.abs(current.distance-8.35)<.1,
   'Top View reset failed: '+JSON.stringify(current));
 // Long upward orbit gestures must now reach almost vertically overhead.
 await stage.evaluate(el=>{
  const p=(event,x,y)=>el.dispatchEvent(new PointerEvent(event,
   {bubbles:true,cancelable:true,pointerId:1,pointerType:'touch',
    isPrimary:true,clientX:x,clientY:y,button:0,buttons:1}));
  p('pointerdown',100,180);
  p('pointermove',100,580);
  p('pointerup',100,580);
 });
 await page.waitForTimeout(110);
 current=await readCamera();
 assert(current.pitch>1.48,'Drag pitch still prevents viewing the top: '+current.pitch);
 await page.locator('[data-camera-control="reset"]').click();
 await page.waitForTimeout(90);
 console.log('PASS top-down iPhone camera angle, top button, vertical drag and reset');
 console.log('PASS iPhone drag rotate, vertical tilt, pinch zoom, zoom buttons and reset');
 // Compare the NEW microphone hand under the exact same virtual camera
 // at front and a three-quarter side angle. Save both full-resolution images.
 for(let k=0;k<3;k++) await page.locator('[data-camera-control="in"]').click();
 await page.waitForTimeout(400);
 await page.screenshot({path:'test-results/v15-mic-front-closeup.png',fullPage:false});
 await page.locator('[data-camera-control="left"]').click();
 await page.locator('[data-camera-control="left"]').click();
 await page.waitForTimeout(400);
 await page.screenshot({path:'test-results/v15-mic-three-quarter-closeup.png',fullPage:false});
 // Pull back before profile inspection so the grip stays inside 9:16.
 await page.locator('[data-camera-control="out"]').click();
 await page.locator('[data-camera-control="out"]').click();
 for(let k=0;k<3;k++) await page.locator('[data-camera-control="left"]').click();
 await page.waitForTimeout(400);
 await page.screenshot({path:'test-results/v15-mic-side-closeup.png',fullPage:false});
 await page.locator('[data-camera-control="reset"]').click();
 console.log('PASS V15 front, three-quarter and side grip screenshots captured');
 await page.locator('[data-tab="direct"]').click();
 await page.locator('details').evaluate(el=>el.open=true);
 for(const shape of ['REST','A','O','M','SMILE']){
  await page.locator('#mouthShape').selectOption(shape);
  await page.waitForFunction(s=>document.getElementById('stage').dataset.mouthShape===s,shape);
  assert(Number(await stage.getAttribute('data-face-morph-count'))>=7,'Face rig not connected');
  await page.waitForTimeout(180);
  await stage.screenshot({path:'test-results/v16-face-'+shape+'.png'});
 }
 await page.locator('#mouthShape').selectOption('AUTO');
 await page.locator('[data-tab="create"]').click();
 console.log('PASS browser speech shape controls and morph rig');

 await page.locator('#demo').click();
 await page.waitForFunction(()=>document.getElementById('status').textContent==='Voice analyzed',{timeout:20000});
 console.log('PASS demo audio decoded');
 await page.locator('#timingFile').setInputFiles({name:'timing.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify({
  schema:'robot-studio-timing/v1',duration:10,visemes:[{time:0,end:1,shape:'M'},{time:1,end:2,shape:'O'}]
 }))});
 await page.waitForFunction(()=>document.getElementById('stage').dataset.timingSource==='imported');
 console.log('PASS matching speech timing file imported');

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
