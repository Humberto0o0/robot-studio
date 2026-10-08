"""Robot Studio - procedural, editable Blender robot v0.2, expressive face.
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

# Robot Studio V2: independent art direction for the HELMET, VISOR and
# EXPRESSION RIG. All geometry below is real Blender mesh data, not an AI image.
# Eye and mouth object names are stable identifiers consumed by studio3d.js.
navy = mat("Black glass / clearcoat visor",(.004,.009,.024),.24,.07)
shell = mat("Ceramic pearl helmet",(.94,.973,1.0),.18,.13)
trim = mat("Deep navy visor gasket",(.009,.025,.059),.43,.20)
edge = mat("Iridescent cobalt anodized trim",(.025,.20,.95),.56,.14)
led_bg = mat("Blue LED diffuser",(.012,.17,.64),.08,.23,.85)
led_px = mat("Cyan LED pixel matrix",(.006,.50,.93),.02,.20,2.35)
mouth_dark = mat("Warm shaded smile cavity",(.095,.004,.012),.10,.27)
tongue = mat("Coral pink mouth tongue",(.99,.13,.14),.06,.29)
mouth_border = mat("Inner mouth rim",(.025,.012,.026),.12,.23)
glass_sheen = mat("Blue glass visor reflection",(.075,.28,.68),.29,.09)
for m in [navy,shell]:
    node=m.node_tree.nodes.get("Principled BSDF")
    if "Coat Weight" in node.inputs: node.inputs["Coat Weight"].default_value=.65
    if "Coat Roughness" in node.inputs: node.inputs["Coat Roughness"].default_value=.10

def poly_mesh(name, xyz, faces, material, parent):
    # Input points are authored in Blender WORLD SPACE for easy visor surface
    # projection. A custom mesh must store LOCAL vertices under its parent:
    # otherwise GLB export applies the parent translation twice (eyes vanish).
    bpy.context.view_layer.update()
    world_to_parent=parent.matrix_world.inverted()
    local_points=[tuple(world_to_parent @ Vector(p)) for p in xyz]
    mesh=bpy.data.meshes.new(name+"_Geometry")
    mesh.from_pydata(local_points, [], faces)
    mesh.update()
    ob=bpy.data.objects.new(name,mesh)
    bpy.context.collection.objects.link(ob)
    ob.data.materials.append(material)
    for face in ob.data.polygons: face.use_smooth=True
    ob.parent=parent
    # Keep matrix_parent_inverse=identity; vertices are already parent-local.
    return ob

head=pivot("Head_Pivot",(0,0,2.06),root)
orb("Helmet / pearl white ceramic",(0,0,2.65),(1.052,.824,.82),shell,head,64,44)
# Three concentric ellipsoids form a thick visible white bezel, a narrow dark
# rubber gasket and the smoothly convex black glass display. They overlap, but
# the visor projects further forward so no black outlines cut across the eyes.
orb("Visor white sculpted surround",(0,-.535,2.72),(.963,.315,.532),shell,head,64,40)
orb("Visor black precision gasket",(0,-.610,2.724),(.917,.282,.488),trim,head,64,40)
orb("Visor curved midnight glass",(0,-.662,2.727),(.876,.259,.461),navy,head,72,48)
# A polished blue crest is integrated with the helmet, rather than a flat block.
orb("Cobalt forehead enamel plate",(0,-.055,3.395),(.367,.655,.105),edge,head,48,28)
orb("Cobalt crest glint",(0,-.18,3.473),(.205,.31,.017),blue,head,48,16)
# Tiny reflective accents high on the curved visor; these sit behind eyes.
orb("Glass upper left reflection",(-.52,-.842,3.01),(.115,.016,.027),glass_sheen,head,32,16)
orb("Glass upper right reflection",(.52,-.842,3.01),(.11,.016,.021),glass_sheen,head,32,16)

for sign,label in [(-1,"L"),(1,"R")]:
    # White/blue layered ear cups, metallic separation ring and cyan light core.
    orb("Headset porcelain housing "+label,(sign*1.018,.012,2.63),(.174,.363,.326),shell,head,48,28)
    orb("Headset deep blue band "+label,(sign*1.078,.008,2.63),(.160,.340,.312),edge,head,48,28)
    orb("Headset polished white stripe "+label,(sign*1.141,.008,2.63),(.067,.290,.257),shell,head,40,24)
    orb("Headset active cyan light "+label,(sign*1.201,-.017,2.63),(.047,.225,.215),cyan,head,40,24)
    tube("Antenna graphite stem "+label,(sign*1.032,.055,2.87),(sign*1.032,.055,3.369),.043,black,head)
    orb("Antenna luminous tube "+label,(sign*1.032,.055,3.390),(.058,.064,.205),cyan,head,30,20)

# Draw LED arcs conforming to a real convex visor. Direct mesh projection keeps
# the face integrated with the glass as the head rotates in Three.js.
def visor_depth(x,z,offset=.026):
    # negative Y is the front of this robot.
    u=(x/.876)**2 + ((z-2.727)/.461)**2
    return -.662-.259*math.sqrt(max(.002,1.0-u))-offset

def curved_strip(name,cx,z0,width,height,thickness,material,parent,yoff=.036,segments=28):
    verts,faces=[],[]
    for i in range(segments+1):
        t=math.pi*i/segments
        xx=cx+width*math.cos(t)
        top=z0+height*math.sin(t)
        bottom=z0-thickness+max(.005,height-thickness*1.08)*math.sin(t)
        for zz in (top,bottom):
            verts.append((xx,visor_depth(xx,zz,yoff),zz))
        if i:
            a=2*(i-1);b=2*i
            faces.extend([(a,b,a+1),(b,b+1,a+1)])
    return poly_mesh(name,verts,faces,material,parent)

def matrix_pixels(name,cx,base,width,outer,inner,parent):
    # Many small separated emissive quads, ONE combined mesh. Efficient on iPhone.
    verts,faces=[],[]
    dx=.024
    for ix in range(-11,12):
        x=cx+ix*dx
        frac=max(0,1-((x-cx)/width)**2)
        arch=math.sqrt(frac)
        zhi=base+outer*arch-.006
        zlo=base-.041+max(.004,inner)*arch+.006
        for k in range(15):
            z=base-.033+k*.019
            if z<zlo or z>zhi:continue
            # Avoid a uniform solid bar: tiny alternating pixel brightness holes.
            if (ix*19+k*7)%23==0:continue
            d=.0066
            four=[]
            for xx,zz in [(x-d,z-d),(x+d,z-d),(x+d,z+d),(x-d,z+d)]:
                four.append((xx,visor_depth(xx,zz,.057),zz))
            q=len(verts);verts.extend(four)
            faces.append((q,q+1,q+2,q+3))
    return poly_mesh(name,verts,faces,led_px,parent)

for sign,label in [(-1,"L"),(1,"R")]:
    cx=sign*.395
    eye=pivot("Eye_"+label,(cx,visor_depth(cx,2.74,.02),2.73),head)
    curved_strip("Eye diffuser arc "+label,cx,2.675,.267,.193,.047,led_bg,eye,.035)
    matrix_pixels("Eye emissive LED matrix "+label,cx,2.675,.265,.193,.145,eye)
    # The two eyebrows are slim bright arcs, separately positioned above the eyes.
    curved_strip("Cute eyebrow "+label,cx,2.975,.154,.068,.014,led_px,head,.048,24)

# Sculpted 3D grin flush with the helmet's lower white ceramic shell.
# Curved face polygons follow its elliptical surface (not flat sphere overlays).
mouth=pivot("Mouth_Display",(0,-.72,2.20),head)
def helmet_front(x,z,offset=.0):
    ratio=(x/1.052)**2+((z-2.65)/.82)**2
    return -.824*math.sqrt(max(.002,1-ratio))-offset

def smile_band(name,width,depth_drop,offset,material,segments=42):
    vertices,faces=[],[]
    for i in range(segments+1):
        u=-1.0+i*2.0/segments
        x=width*u
        # Gentle top lip; corners join a curved lower edge like the reference.
        z_top=2.248+.020*u*u
        z_bottom=2.262-depth_drop*max(0,1-u*u)**.63
        for z in (z_top,z_bottom):
            vertices.append((x,helmet_front(x,z,offset),z))
        if i>0:
            a=2*(i-1); b=2*i
            faces.extend([(a,b,a+1),(b,b+1,a+1)])
    return poly_mesh(name,vertices,faces,material,mouth)

smile_band("Mouth rim precision outline",.311,.195,.041,mouth_border)
smile_band("Mouth open burgundy recess",.289,.181,.053,mouth_dark)
# The pink tongue is a subtly convex U-shaped insert near the lower lip.
def sculpted_tongue():
    verts,faces=[],[]
    count=28
    for i in range(count+1):
        u=-1+i*2/count
        x=.203*u
        u2=max(0,1-u*u)
        ztop=2.142+.027*u2
        zbot=2.092+.022*(1-u2)
        for z in (ztop,zbot):
            verts.append((x,helmet_front(x,z,.069),z))
        if i:
            a=2*(i-1);b=2*i
            faces.extend([(a,b,a+1),(b,b+1,a+1)])
    poly_mesh("Mouth warm coral tongue",verts,faces,tongue,mouth)
sculpted_tongue()
# Wide smiling corner details, not independent oval buttons.
for sign,label in [(-1,"L"),(1,"R")]:
    x=sign*.291
    orb("Smile corner "+label,(x,helmet_front(x,2.264,.061),2.264),
        (.021,.012,.017),mouth_border,mouth,20,12)

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
    mouth.scale=(1,1,.65+mouth_open*.50)
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
