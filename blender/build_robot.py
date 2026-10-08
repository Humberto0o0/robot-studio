"""Robot Studio - procedural, editable Blender robot v0.1.
Run: blender --background --python blender/build_robot.py
This is a geometry/rigging proof of concept, not the final art-quality character.
"""
import bpy
import math
from mathutils import Vector
from pathlib import Path

ROOT = Path(bpy.path.abspath("//")).resolve()
OUT = ROOT / "models"
OUT.mkdir(parents=True, exist_ok=True)

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

def mat(name, color, metallic=0.1, roughness=0.35, emission=0.0):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1.0)
    m.use_nodes = True
    p = m.node_tree.nodes.get("Principled BSDF")
    p.inputs["Base Color"].default_value = (*color, 1.0)
    p.inputs["Metallic"].default_value = metallic
    p.inputs["Roughness"].default_value = roughness
    if emission:
        p.inputs["Emission Color"].default_value = (*color, 1)
        p.inputs["Emission Strength"].default_value = emission
    return m

shell = mat("Gloss white shell", (0.90, 0.96, 1.00), 0.16, 0.23)
blue = mat("Cobalt blue jacket", (0.014, 0.11, 0.79), 0.16, 0.38)
navy = mat("Midnight visor", (0.006, 0.013, 0.032), 0.28, 0.13)
orange = mat("Orange tie", (1.0, 0.27, 0.014), 0.06, 0.28)
cyan = mat("Cyan luminous details", (0.08, 0.90, 1.0), 0.05, 0.15, 3.0)
black = mat("Graphite joints", (0.025, 0.035, 0.055), 0.35, 0.25)
steel = mat("Metal microphone grille", (0.17, 0.23, 0.30), 0.58, 0.24)

def finish(obj, material, parent=None):
    obj.data.materials.append(material)
    for p in obj.data.polygons:
        p.use_smooth = True
    if parent is not None:
        obj.parent = parent
        obj.matrix_parent_inverse = parent.matrix_world.inverted()
    return obj

def orb(name, center, radii, material, parent=None, segments=32, rings=20):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, location=center)
    o=bpy.context.object
    o.name=name
    o.scale=radii
    return finish(o,material,parent)

def block(name, center, radii, material, parent=None, bevel=0.10):
    bpy.ops.mesh.primitive_cube_add(size=1, location=center)
    o=bpy.context.object
    o.name=name
    o.dimensions=[2*x for x in radii]
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        mod=o.modifiers.new("soft edges","BEVEL")
        mod.width=bevel
        mod.segments=3
        mod2=o.modifiers.new("weighted normals","WEIGHTED_NORMAL")
    return finish(o,material,parent)

def tube(name, a, b, radius, material, parent=None, vertices=24):
    a,b=Vector(a),Vector(b)
    d=b-a
    mid=(a+b)/2
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=d.length, location=mid)
    o=bpy.context.object
    o.name=name
    o.rotation_euler=d.to_track_quat("Z","Y").to_euler()
    return finish(o,material,parent)

def pivot(name, xyz, parent=None):
    e=bpy.data.objects.new(name,None)
    bpy.context.collection.objects.link(e)
    e.empty_display_size=.13
    e.location=xyz
    if parent:
        e.parent=parent
        e.matrix_parent_inverse=parent.matrix_world.inverted()
    return e

def ring(name, center, major, minor, material, parent=None, rotation=None):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor, major_segments=48, minor_segments=10, location=center)
    o=bpy.context.object
    o.name=name
    if rotation:
        o.rotation_euler=rotation
    return finish(o,material,parent)

root=pivot("Robot_Root",(0,0,0))
orb("Floating rounded body",(0,0,1.27),(.74,.54,.73),shell,root)
orb("Royal blue suit torso",(0,-.095,1.67),(.79,.55,.55),blue,root)
orb("White shirt chest",(0,-.57,1.78),(.29,.08,.40),shell,root)
block("Blue jacket left lapel",(-.34,-.51,1.88),(.28,.10,.30),blue,root,.08)
block("Blue jacket right lapel",(.34,-.51,1.88),(.28,.10,.30),blue,root,.08)
orb("Orange tie knot",(0,-.679,1.98),(.10,.055,.10),orange,root)
orb("Orange tie",(0,-.686,1.73),(.086,.048,.23),orange,root)
orb("Orange pocket square",(.51,-.53,1.86),(.12,.028,.068),orange,root)
orb("Jacket button",(0,-.635,1.43),(.065,.045,.065),black,root)
orb("Jacket button trim",(0,-.678,1.43),(.03,.012,.03),steel,root)

head=pivot("Head_Pivot",(0,0,2.06),root)
orb("Helmet white outer shell",(0,0,2.63),(1.01,.78,.79),shell,head)
orb("Gloss black visor",(0,-.657,2.67),(.82,.235,.45),navy,head)
orb("Cobalt forehead",(0,-.03,3.345),(.35,.66,.13),blue,head)
for sign,label in [(-1,"L"),(1,"R")]:
    orb("Headset "+label,(sign*1.02,0,2.58),(.205,.40,.34),blue,head)
    orb("Headset light "+label,(sign*1.18,-.02,2.58),(.055,.26,.24),cyan,head)
    tube("Antenna "+label,(sign*1.03,0,2.82),(sign*1.03,0,3.38),.045,black,head)
    orb("Antenna tip "+label,(sign*1.03,0,3.40),(.075,.077,.23),cyan,head)

# Emissive expression objects, parented to the head so eye/mouth registration never drifts.
eyes=[]
for sign,label in [(-1,"L"),(1,"R")]:
    eye=orb("Eye_"+label,(sign*.38,-.868,2.78),(.14,.035,.045),cyan,head)
    eyes.append(eye)
mouth=ring("Mouth_Display",(0,-.895,2.47),.086,.018,cyan,head,rotation=(math.pi/2,0,0))

# Shoulder and elbow pivots remain physically attached at any rotation.
shoulders={}
elbows={}
wrists={}
for side,sign in [("L",-1),("R",1)]:
    shoulder=pivot("Shoulder_"+side,(sign*.77,-.03,1.87),root)
    shoulders[side]=shoulder
    orb("Shoulder socket "+side,(sign*.77,-.03,1.87),(.23,.22,.25),black,root)
    orb("Shoulder glowing rim "+side,(sign*.80,-.045,1.87),(.175,.24,.18),cyan,root)
    a=(sign*.84,-.055,1.85)
    b=(sign*1.23,-.16,1.53)
    tube("Jacket upper arm "+side,a,b,.21,blue,shoulder)
    orb("Elbow sleeve "+side,b,(.22,.23,.22),blue,shoulder)
    el=pivot("Elbow_"+side,b,shoulder)
    elbows[side]=el
    # Both forearms are shortened and visually thick; no gaps between the segments.
    c=(sign*1.49,-.43,1.50) if side=="R" else (-.64,-.73,1.61)
    tube("Jacket forearm "+side,b,c,.195,blue,el)
    orb("Wrist ring "+side,c,(.21,.21,.17),cyan,el)
    wrist=pivot("Wrist_"+side,c,el)
    wrists[side]=wrist
    hand=(sign*1.61,-.46,1.52) if side=="R" else (-.56,-.81,1.65)
    orb("White robot palm "+side,hand,(.17,.16,.15),shell,wrist)
    for j in range(4):
        signmul=1 if side=="R" else -1
        f0=(hand[0]+signmul*.075,hand[1]-.05+(j-1.5)*.05,hand[2]+(j-1.5)*.054)
        f1=(hand[0]+signmul*.22,hand[1]-.06+(j-1.5)*.061,hand[2]+(j-1.5)*.071)
        tube("Finger "+side+" "+str(j),f0,f1,.034,shell,wrist,12)

# Built-in microphone remains part of left-hand geometry and rotates with the wrist.
tube("Microphone handle",(-.48,-.92,1.46),(-.44,-.94,2.02),.072,black,wrists["L"])
orb("Microphone head",(-.44,-.94,2.09),(.18,.18,.18),steel,wrists["L"])
ring("Microphone cyan band",(-.445,-.94,1.98),.091,.020,cyan,wrists["L"])

ring("Hover ground ring",(0,0,.36),.74,.044,cyan,root)
orb("Hover core",(0,0,.51),(.26,.26,.09),cyan,root)

# Distinct animated nodes produce a reusable animation track in glTF.
keys=[
  (1,  -.1,  0.0, 0.0,  0.0, 0.0, .6),
  (22, -.1, -0.2, 0.10, -.06, 0.04, 1.1),
  (40, -.1, -0.75,0.16, -.05, 0.02, .65), # raise right arm
  (58, -.1, -0.12,0.0, 0.0, 0.0, 1.0),
  (77, -.1, -0.37,-0.12,0.08,0.03, .3),  # present
  (96, -.1, 0.0, 0.0, 0.0, 0.0, 1.0),
  (120,-.1, -0.1, 0.0, 0.0,0.0, .5),
]
for frame,left,right,elbow,tilt,bob,mouth_open in keys:
    bpy.context.scene.frame_set(frame)
    shoulders["L"].rotation_euler=(0, left, 0)
    shoulders["R"].rotation_euler=(0, right, 0)
    elbows["R"].rotation_euler=(0,elbow,0)
    head.rotation_euler=(0,tilt*.4,tilt)
    root.location.z=bob
    mouth.scale=(1,.48+mouth_open*.55,1)
    for obj in [shoulders["L"],shoulders["R"],elbows["R"],head,root,mouth]:
        if obj == mouth:
            obj.keyframe_insert(data_path="scale",frame=frame)
        elif obj == root:
            obj.keyframe_insert(data_path="location",frame=frame)
        else:
            obj.keyframe_insert(data_path="rotation_euler",frame=frame)

scene=bpy.context.scene
scene.frame_start=1
scene.frame_end=120
scene.render.fps=30
scene.render.engine='BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items.keys() else 'BLENDER_EEVEE'

# Share one named NLA track across all animated pieces, so glTF exports a
# single synchronized gesture clip instead of one animation per body part.
for obj in [root, head, shoulders["L"], shoulders["R"], elbows["R"], mouth]:
    anim = obj.animation_data
    if anim and anim.action:
        action = anim.action
        track = anim.nla_tracks.new()
        track.name = "Robot_Performance"
        track.strips.new("Robot_Performance", 1, action)
        anim.action = None

# Save editable source and web-ready GLB.
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"robot-prototype.blend"))
bpy.ops.export_scene.gltf(filepath=str(OUT/"robot-prototype.glb"),export_format="GLB",export_animations=True)
print("ROBOT_BUILD_OK: "+str(OUT/"robot-prototype.glb"))
