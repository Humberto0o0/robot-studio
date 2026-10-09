"""Render the actual editable robot from a validated performance JSON.

blender --background --python-exit-code 1 --python blender/render_performance.py -- \
  --plan plan.json --audio voice.wav --output video.mp4 --width 540 --height 960
Use xvfb-run on headless Linux for software EEVEE. No uploaded Python is run.
"""
import argparse,json,math,sys
from pathlib import Path
import bpy
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from performance import normalize,shape_at,pose_at,blink_at,SHAPES

args=argparse.ArgumentParser()
args.add_argument('--plan',required=True);args.add_argument('--audio',required=True)
args.add_argument('--output',required=True);args.add_argument('--model',default=str(Path(__file__).resolve().parents[1]/'models/robot-prototype.blend'))
args.add_argument('--width',type=int,default=540);args.add_argument('--height',type=int,default=960)
args.add_argument('--fps',type=int,default=24);args.add_argument('--samples',type=int,default=16)
args.add_argument('--still',type=float,default=None)
opt=args.parse_args(sys.argv[sys.argv.index('--')+1:])
plan=normalize(json.loads(Path(opt.plan).read_text()))
if (opt.width,opt.height) not in {(360,640),(540,960),(1080,1920)}:raise ValueError('Unsupported resolution')
if opt.fps not in (12,24,30):raise ValueError('Unsupported frame rate')
bpy.ops.wm.open_mainfile(filepath=opt.model)
scene=bpy.context.scene
scene.frame_set(1);bpy.context.view_layer.update()
for obj in bpy.data.objects:
    # Use the saved model as a rest pose, then author one deterministic take.
    obj.animation_data_clear()
    if obj.type=='MESH' and obj.data.shape_keys:obj.data.shape_keys.animation_data_clear()
root=bpy.data.objects['Robot_Root'];head=bpy.data.objects['Head_Pivot']
base={n:tuple(bpy.data.objects[n].rotation_euler) for n in ['Head_Pivot','Shoulder_R','Elbow_R','Shoulder_L','Elbow_L','Wrist_R']}
base_root=tuple(root.location)
face=[o for o in bpy.data.objects if o.type=='MESH' and o.data.shape_keys]
weights={name:0. for name in SHAPES}
fps=opt.fps;num=math.ceil(plan['duration']*fps)
for frame in range(1,num+1):
    t=(frame-1)/fps;shape=shape_at(plan,t) if plan['settings']['mouth'] else 'REST';pose,pulse=pose_at(plan,t)
    if not plan['settings']['gestures']:pose,pulse='neutral',0
    for name in SHAPES:weights[name]+=(float(name==shape)-weights[name])*(1-math.exp(-24/fps))
    blink=blink_at(t) if plan['settings']['blink'] else 0
    expression=plan['settings']['expression']
    attentive=1 if expression=='ATTENTIVE' else 0 if expression=='FRIENDLY' else 0 if pose in ('wave','present','open-hand') else .75
    for obj in face:
        for key in obj.data.shape_keys.key_blocks:
            if key.name=='Basis':continue
            key.value=blink if key.name=='BLINK' else attentive*(1-blink) if key.name=='ATTENTIVE' else weights.get(key.name,0)
            key.keyframe_insert('value',frame=frame)
    raised={'wave':-.72,'present':-.40,'open-hand':-.40,'point':-.56,'emphasis':-.30,'excited':-.40}.get(pose,0)*pulse*plan['settings']['energy']
    rotations={
        'Head_Pivot':(0,.018*math.sin(t*1.1),.021*math.sin(t*.8)),
        'Shoulder_R':(0,raised,0), 'Elbow_R':(0,.10*pulse,0),
        'Shoulder_L':(0,.015*math.sin(t*.8),0), 'Elbow_L':(0,0,0),
        'Wrist_R':(0,0,.13*pulse*math.sin(t*7) if pose=='wave' else 0),
    }
    if pose in ('nod','emphasis'):rotations['Head_Pivot']=(.05*math.sin(t*6)*pulse,0,0)
    for name,delta in rotations.items():
        obj=bpy.data.objects[name];obj.rotation_euler=tuple(a+b for a,b in zip(base[name],delta));obj.keyframe_insert('rotation_euler',frame=frame)
    root.location=(base_root[0],base_root[1],base_root[2]+(.015*math.sin(t*1.65) if plan['settings']['float'] else 0));root.keyframe_insert('location',frame=frame)
# Linear keyframes preserve the sampled plan, no spline overshoot at lip closure.
for obj in list(bpy.data.objects)+[o.data.shape_keys for o in face]:
    if obj.animation_data and obj.animation_data.action:
        for fc in obj.animation_data.action.fcurves:
            for k in fc.keyframe_points:k.interpolation='LINEAR'

world=bpy.data.worlds.new('News studio world');scene.world=world;world.use_nodes=True
world.node_tree.nodes['Background'].inputs[0].default_value=(.055,.085,.15,1)
world.node_tree.nodes['Background'].inputs[1].default_value=.45

def area(name,loc,power,size,color):
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size;data.color=color
    data.specular_factor=.12  # Keep softbox reflections from obscuring the LED eyes.
    o=bpy.data.objects.new(name,data);scene.collection.objects.link(o);o.location=loc
    o.rotation_euler=(Vector((0,0,1.8))-o.location).to_track_quat('-Z','Y').to_euler()
area('Large soft key',(-3,-4,6),500,5,(.85,.93,1))
area('Warm soft fill',(3,-3,3),280,4,(1,.88,.78))
area('Cobalt rim',(1,2,4),450,3,(.22,.47,1))
camdata=bpy.data.cameras.new('News portrait camera');cam=bpy.data.objects.new('News portrait camera',camdata);scene.collection.objects.link(cam)
cam.location=(.15,-8.2,2.55);target=Vector((.15,-.05,1.85));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
camdata.type='ORTHO';camdata.ortho_scale=6.8;scene.camera=cam
scene.render.engine='BLENDER_EEVEE_NEXT' if bpy.app.version>=(4,2,0) else 'BLENDER_EEVEE'
if hasattr(scene,'eevee'):
    scene.eevee.taa_render_samples=opt.samples
    scene.eevee.use_gtao=True;scene.eevee.gtao_distance=3;scene.eevee.gtao_factor=1.1
scene.render.resolution_x=opt.width;scene.render.resolution_y=opt.height;scene.render.resolution_percentage=100
scene.render.fps=fps;scene.frame_start=1;scene.frame_end=num
scene.render.film_transparent=False
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast'
scene.render.image_settings.color_mode='RGB'
# Output the robot pass; the server/CLI compositor adds captions and audio with
# FFmpeg, using fixed arguments and paths rather than shell interpolation.
scene.render.filepath=str(Path(opt.output).resolve())
if opt.still is not None:
    scene.frame_set(1+min(num-1,max(0,int(opt.still*fps))))
    scene.render.image_settings.file_format='PNG';bpy.ops.render.render(write_still=True)
else:
    scene.render.image_settings.file_format='FFMPEG'
    scene.render.ffmpeg.format='MPEG4';scene.render.ffmpeg.codec='H264'
    scene.render.ffmpeg.constant_rate_factor='MEDIUM';scene.render.ffmpeg.ffmpeg_preset='GOOD'
    bpy.ops.render.render(animation=True)
print('ROBOT_RENDER_OK',opt.output,flush=True)
