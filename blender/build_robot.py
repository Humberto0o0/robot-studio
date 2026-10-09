"""Robot Studio - procedural, editable Blender robot v1.5, articulated ceramic microphone power grip.
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
steel = mat("Metal microphone grille", (0.27, 0.34, 0.41), 0.82, 0.16)

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
# Robot Studio V2: independent art direction for the HELMET, VISOR and
# EXPRESSION RIG. All geometry below is real Blender mesh data, not an AI image.
# Eye and mouth object names are stable identifiers consumed by studio3d.js.
navy = mat("Black glass / clearcoat visor",(.004,.009,.024),.24,.07)
shell = mat("Ceramic pearl helmet",(.94,.973,1.0),.18,.13)
trim = mat("Deep navy visor gasket",(.009,.025,.059),.43,.20)
edge = mat("Iridescent cobalt anodized trim",(.025,.20,.95),.56,.14)
led_bg = mat("Blue LED diffuser",(.012,.17,.64),.08,.23,.85)
led_px = mat("Cyan LED pixel matrix",(.005,.32,.95),.02,.20,1.25)
mouth_dark = mat("Warm shaded smile cavity",(.022,.004,.009),.03,.42)
tongue = mat("Coral pink mouth tongue",(.53,.075,.095),.02,.38)
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


# V3 tailor-made cobalt jacket. Geometry and tiny woven material detail export as
# authentic glTF textures; no flat reference PNGs or box-shaped lapel primitives.
shirt=mat("Silky ivory shirt",(.94,.975,1),.025,.30)
suit_lining=mat("Jacket navy shadow piping",(.008,.025,.10),.11,.45)
suit_highlight=mat("Cobalt satin lapel facing",(.012,.10,.48),.06,.44)
fabric_shadow=mat("Blue jacket edge shadow",(.014,.078,.43),.13,.53)
metal_button=mat("Antique graphite metal button",(.12,.15,.21),.82,.19)
button_glint=mat("Button champagne rim",(.54,.35,.14),.65,.19)
tie_facet=mat("Orange silk dark facet",(.65,.10,.015),.10,.32)
tie_highlight=mat("Orange silk highlight",(.87,.24,.017),.11,.34)

def weave_image(name, normal=False, size=256):
    # Generated native Blender image, embedded into GLB and packed into .blend.
    # Small seamless basket weave instead of a GPU-expensive shader.
    img=bpy.data.images.new(name,width=size,height=size,alpha=True)
    pixels=[]
    for iy in range(size):
        for ix in range(size):
            u=(ix%4)/4.0;v=(iy%4)/4.0
            warp=.5+.5*math.cos(2*math.pi*u)
            weft=.5+.5*math.cos(2*math.pi*v)
            vstripe=math.sin(2*math.pi*ix/6)
            hstripe=math.sin(2*math.pi*iy/6)
            checker=(1 if (ix//2+iy//2)%2==0 else -1)
            if normal:
                # Tangent-space micro-normal for visible light-catching weave.
                pixels.extend((.5+.012*vstripe,.5+.012*hstripe,.9994,1))
            else:
                gain=.980+.012*warp+.009*weft+.005*checker
                pixels.extend((.020*gain,.245*gain,.94*gain,1))
    img.pixels[:]=pixels
    img.pack()
    return img

fabric_color=weave_image("Cobalt basket weave albedo")
fabric_normal=weave_image("Cobalt basket weave tangent normal",True)
woven=mat("Royal blue woven suit fabric",(.021,.25,.92),.03,.49)
fabric_bsdf=woven.node_tree.nodes.get("Principled BSDF")
# Soft cloth response distinguishes the jacket from the ceramic helmet.
if "Anisotropic IOR Level" in fabric_bsdf.inputs:
    fabric_bsdf.inputs["Anisotropic IOR Level"].default_value=.17
if "Coat Weight" in fabric_bsdf.inputs: fabric_bsdf.inputs["Coat Weight"].default_value=.08
if "Coat Roughness" in fabric_bsdf.inputs: fabric_bsdf.inputs["Coat Roughness"].default_value=.12
tex=woven.node_tree.nodes.new("ShaderNodeTexImage")
tex.name="PBR Fabric Base Color"
tex.image=fabric_color
tex.interpolation="Linear"
woven.node_tree.links.new(tex.outputs["Color"],fabric_bsdf.inputs["Base Color"])
ntex=woven.node_tree.nodes.new("ShaderNodeTexImage")
ntex.name="PBR Micro Weave Normal"
ntex.image=fabric_normal
ntex.image.colorspace_settings.name="Non-Color"
nm=woven.node_tree.nodes.new("ShaderNodeNormalMap")
nm.inputs["Strength"].default_value=.031
woven.node_tree.links.new(ntex.outputs["Color"],nm.inputs["Color"])
woven.node_tree.links.new(nm.outputs["Normal"],fabric_bsdf.inputs["Normal"])

# Silhouette: rounded shoulders, clean fitted jacket with tapered waist.
# White floating base stays; suit jacket covers the old spherical shirt outline.
orb("Suit tailored rounded base",(0,-.085,1.69),(.798,.554,.536),woven,root,64,40)
orb("Suit lower curved hem",(0,-.12,1.40),(.665,.457,.268),woven,root,48,28)

def suit_surface(x,z,offset=.018):
    # The outer suit is ellipsoidal; shift front polygons toward -Y to prevent
    # z-fighting and stiff-looking square overlays.
    u=(x/.798)**2+((z-1.69)/.536)**2
    return -.085-.554*math.sqrt(max(.07,1-u))-offset

def front_patch(name,outline,material,offset=.05,bevel=None):
    """Surface-conforming, triangulated tailor panel.

    Earlier these patches were single twisted N-gons placed over a convex
    ellipsoid. GPU triangulation cut across the body, so the white shirt and
    collar pierced the blue jacket as random bright shards. Tessellate the
    2D silhouette first, then project small triangles onto the actual 3D suit
    curve. This also gives consistent overlap on mobile WebGL.
    """
    from mathutils.geometry import tessellate_polygon
    shape=list(outline)
    area=sum(shape[i][0]*shape[(i+1)%len(shape)][1]-
             shape[(i+1)%len(shape)][0]*shape[i][1] for i in range(len(shape)))
    if area<0: shape.reverse()
    triangles=tessellate_polygon([[Vector((x,z,0)) for x,z in shape]])
    if not triangles:
        raise RuntimeError("Cannot triangulate garment panel "+name)
    coords=[];faces=[];lookup={}
    subdivisions=9
    def get_vertex(x,z):
        key=(round(x,6),round(z,6))
        if key not in lookup:
            lookup[key]=len(coords)
            coords.append((x,suit_surface(x,z,offset),z))
        return lookup[key]
    for original in triangles:
        # Blender 4.0 returns triangle vertex indices, whereas some versions
        # return Vector objects. Support both so a sculpted collar can actually
        # be tessellated instead of silently retaining a stale .glb.
        a,b,c=[Vector((shape[p][0],shape[p][1])) if isinstance(p,int)
               else Vector((p.x,p.y)) for p in original]
        cross=(b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x)
        if cross<0:b,c=c,b
        def point(i,j):
            q=a+(b-a)*(i/subdivisions)+(c-a)*(j/subdivisions)
            return get_vertex(q.x,q.y)
        for i in range(subdivisions):
            for j in range(subdivisions-i):
                faces.append((point(i,j),point(i+1,j),point(i,j+1)))
                if j<subdivisions-i-1:
                    faces.append((point(i+1,j),point(i+1,j+1),point(i,j+1)))
    obj=poly_mesh(name,coords,faces,material,root)
    # Explicit UVs keep fine jacket texture from getting stretched on the
    # lapel and front panels. Give all surface triangles stable stitch scale.
    uv=obj.data.uv_layers.new(name="Tailoring surface UV")
    for poly in obj.data.polygons:
        for loop_index in poly.loop_indices:
            p=obj.data.vertices[obj.data.loops[loop_index].vertex_index].co
            uv.data[loop_index].uv=(p.x*1.35+.5,p.z*1.35)
    if bevel:
        solid=obj.modifiers.new("Tailored panel thickness","SOLIDIFY")
        solid.thickness=min(bevel,.016)
        solid.offset=-1.0
    return obj

def stitched_line(name,pts,material=None,r=.007):
    # Object follows the true suit curve; actual cylindrical stitching is
    # portable to GLB (not a nonexportable Blender-only line overlay).
    if material is None:material=suit_lining
    for n in range(len(pts)-1):
        x,z=pts[n];xx,zz=pts[n+1]
        a=(x,suit_surface(x,z,.09),z)
        b=(xx,suit_surface(xx,zz,.09),zz)
        tube(name+" "+str(n),a,b,r,material,root,10)

# A deliberately narrow, centered shirt bib stays INSIDE the tailored V.
# Never let a white polygon cross out under the shoulder or pocket area.
front_patch("White shirt V front",
 [(-.207,2.028),(-.170,1.923),(-.087,1.739),(0,1.519),
  (.087,1.739),(.170,1.923),(.207,2.028)],
 shirt,.067)
# Clean, symmetric pointed collar triangles frame the orange knot. The outer
# edges tuck BEHIND both blue lapels, rather than piercing the jacket.
for sign,label in [(-1,"L"),(1,"R")]:
    front_patch("Folded ivory collar "+label,
     [(sign*.082,2.039),(sign*.244,2.054),
      (sign*.203,1.944),(sign*.115,1.884)],
     shirt,.112,.006)
    stitched_line("Collar stitch "+label,
     [(sign*.088,2.026),(sign*.200,1.943)],suit_lining,.005)

# Two tailored lapel wings (not cubes). Five-vertex profiles converge into
# a narrow deep V over the tie, using satin fabric contrast and seam piping.
for sign,label in [(-1,"L"),(1,"R")]:
    front_patch("Hand-tailored satin lapel "+label,
     [(sign*.615,2.025),(sign*.321,2.066),(sign*.205,1.881),
      (sign*.095,1.716),(sign*.475,1.838)],
     suit_highlight,.156,.012)
    # Dark inward lapel seam follows the cloth edge.
    stitched_line("Lapel navy rolled edge "+label,
     [(sign*.319,2.058),(sign*.204,1.881),(sign*.095,1.716)],
     suit_lining,.010)
    stitched_line("Lapel cobalt top stitch "+label,
     [(sign*.606,2.013),(sign*.474,1.834),(sign*.096,1.712)],
     woven,.006)
    # Lower jacket fronts taper into a visually clean center closure.
    front_patch("Tailored jacket front "+label,
     [(sign*.72,1.83),(sign*.54,1.74),(sign*.102,1.485),
      (sign*.041,1.321),(sign*.48,1.325),(sign*.715,1.5)],
     woven,.079)
    stitched_line("Jacket outer curved hem "+label,
     [(sign*.68,1.49),(sign*.47,1.324),(sign*.07,1.318)],
     fabric_shadow,.009)

# Folded silk tie: sculpted diamond blade with two-sided relief, not yellow
# ellipsoid shapes. Tip sits above the center jacket closure.
orb("Silk tie double knot shadow",(0,-.708,1.960),(.108,.056,.093),tie_facet,root,32,22)
front_patch("Orange necktie diamond knot",
 [(-.103,1.973),(0,2.032),(.103,1.973),(.078,1.909),(0,1.876),(-.078,1.909)],
 orange,.208,.011)
front_patch("Tailored orange silk blade",
 [(-.069,1.889),(.068,1.889),(.097,1.630),(0,1.523),(-.097,1.630)],
 orange,.220,.011)
front_patch("Tie diagonal satin highlight",
 [(-.054,1.870),(-.012,1.864),(.020,1.635),(-.027,1.667)],
 tie_highlight,.235)
stitched_line("Fine necktie silk edge",[(-.075,1.85),(-.090,1.64),(0,1.530)],
 tie_facet,.006)

# Chest welt, triangular silk pocket square and matching jacket pocket seams.
for sign,label in [(-1,"L"),(1,"R")]:
    front_patch("Decorative hip pocket "+label,
     [(sign*.39,1.535),(sign*.661,1.55),(sign*.623,1.487),(sign*.385,1.481)],
     suit_highlight,.104)
    stitched_line("Pocket dark welt "+label,
     [(sign*.39,1.531),(sign*.660,1.545)],suit_lining,.009)
front_patch("Suit breast pocket welt",
 [(.401,1.881),(.632,1.882),(.629,1.838),(.407,1.835)],
 fabric_shadow,.127)
front_patch("Orange silk pocket fold 1",
 [(.431,1.868),(.464,1.925),(.518,1.874)],orange,.157)
front_patch("Orange silk pocket fold 2",
 [(.498,1.868),(.568,1.915),(.610,1.864)],tie_highlight,.163)
stitched_line("Chest welt seam",[(.398,1.838),(.63,1.837)],suit_lining,.010)

# One engraved metal button in a recessed metal trim, near the crossing panels.
orb("Jacket button dark seat",(0,-.740,1.391),(.076,.028,.075),suit_lining,root,32,20)
orb("Jacket button brushed graphite",(0,-.766,1.391),(.060,.017,.061),metal_button,root,32,20)
ring("Jacket button champagne metal lip",(0,-.789,1.391),.045,.006,button_glint,root,rotation=(math.pi/2,0,0))

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
# Keep the upper visor uncluttered: the cyan smile-eyes are the only brows.

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

# V17 open LED eyes: projected annular irises, inset pupils, catchlights and
# independent brows. All parts remain real geometry with identical morph topology.
pupil_mat=mat("LED pupil deep ink",(.001,.004,.010),0,.65)
catch_mat=mat("LED eye catchlight",(.30,.88,1),0,.4,1.4)
def eye_mesh(name,points,faces,material,eye,cx,part):
    obj=poly_mesh(name,points,faces,material,eye)
    obj.shape_key_add(name="Basis")
    inv=eye.matrix_world.inverted()
    for expression in ("ATTENTIVE","FRIENDLY","SURPRISED","BLINK","LOOK_LEFT","LOOK_RIGHT"):
        key=obj.shape_key_add(name=expression)
        for dest,xyz in zip(key.data,points):
            x,y,z=xyz
            offset=visor_depth(x,z,0)-y
            if part=="brow":
                if expression=="FRIENDLY":z+=.025
                elif expression=="SURPRISED":z+=.040
                elif expression=="ATTENTIVE":z-=.012
                elif expression=="BLINK":z-=.012
            else:
                if expression=="FRIENDLY":z=2.71+(z-2.71)*.72
                elif expression=="ATTENTIVE":z=2.71+(z-2.71)*.91
                elif expression=="SURPRISED":z=2.71+(z-2.71)*1.09
                elif expression=="BLINK":z=2.71+(z-2.71)*.035
                elif expression in ("LOOK_LEFT","LOOK_RIGHT"):
                    x+=-.035 if expression=="LOOK_LEFT" else .035
            dest.co=inv @ Vector((x,visor_depth(x,z,offset),z))
    return obj

for sign,label in [(-1,"L"),(1,"R")]:
    cx=sign*.355;zc=2.71
    eye=pivot("Eye_"+label,(cx,visor_depth(cx,zc,.02),zc),head)
    points=[];faces=[];count=64
    for i in range(count):
        a=2*math.pi*i/count
        for rx,rz in ((.231,.207),(.119,.128)):
            x=cx+rx*math.cos(a);z=zc+rz*math.sin(a)
            points.append((x,visor_depth(x,z,.006),z))
        j=2*i;k=2*((i+1)%count);faces.append((j,k,k+1,j+1))
    eye_mesh("Eye diffuser arc "+label,points,faces,led_bg,eye,cx,"iris")
    points=[];faces=[]
    for ix in range(-16,17):
        for iz in range(-15,16):
            x=ix*.014;z=iz*.014
            if (x/.224)**2+(z/.201)**2>1 or (x/.124)**2+(z/.133)**2<1:continue
            q=len(points);d=.0046
            for dx,dz in ((-d,-d),(d,-d),(d,d),(-d,d)):
                xx=cx+x+dx;zz=zc+z+dz;points.append((xx,visor_depth(xx,zz,.010),zz))
            faces.append((q,q+1,q+2,q+3))
    eye_mesh("Eye emissive LED matrix "+label,points,faces,led_px,eye,cx,"iris")
    for part,rx,rz,ox,oz,material in (("pupil",.116,.125,0,0,pupil_mat),("catch",.031,.030,.043,.065,catch_mat)):
        points=[(cx+ox,visor_depth(cx+ox,zc+oz,.012 if part=="pupil" else .016),zc+oz)]
        for i in range(count):
            a=2*math.pi*i/count;x=cx+ox+rx*math.cos(a);z=zc+oz+rz*math.sin(a)
            points.append((x,visor_depth(x,z,.012 if part=="pupil" else .016),z))
        faces=[(0,1+i,1+(i+1)%count) for i in range(count)]
        eye_mesh("Eye "+part+" "+label,points,faces,material,eye,cx,part)
    points=[];faces=[]
    for i in range(25):
        u=i/24;x=cx+(u-.5)*.34
        for z in (2.989+.028*math.sin(u*math.pi),2.955+.028*math.sin(u*math.pi)):
            points.append((x,visor_depth(x,z,.010),z))
        if i:faces.append((2*i-2,2*i,2*i+1,2*i-1))
    eye_mesh("Expressive LED brow "+label,points,faces,led_px,eye,cx,"brow")

# V16 continuous-topology speech rig. Basis is a closed, friendly smile.
# Shape keys export as named glTF morph targets and are shared by the browser
# and the offline Blender renderer. The hand geometry is untouched.
mouth=pivot("Mouth_Display",(0,-.72,2.20),head)
def helmet_front(x,z,offset=.0):
    ratio=(x/1.052)**2+((z-2.65)/.82)**2
    return -.824*math.sqrt(max(.002,1-ratio))-offset

VISEMES={
    "REST":(.235,.006,.027), "A":(.205,.093,.014),
    "E":(.260,.047,.016), "O":(.115,.090,.004),
    "U":(.093,.061,.004), "M":(.222,.003,.018),
    "F":(.215,.021,.012), "S":(.225,.036,.012),
    "SMILE":(.265,.042,.042),
}

def mouth_points(shape,part):
    width,height,smile=VISEMES[shape]
    verts=[]; count=64
    if part=="tongue":
        # A small rounded tongue stays within the lower interior, collapsing
        # entirely for silence/closed consonants instead of a permanent pink bar.
        visible=shape in {"A","E","S","SMILE"}
        for i in range(count):
            t=2*math.pi*i/count
            x=width*.57*math.cos(t) if visible else 0
            z=2.204-height*.52+height*.19*math.sin(t) if visible else 2.204
            verts.append((x,helmet_front(x,z,.046),z))
        verts.append((0,helmet_front(0,2.204-height*.52,.047),2.204-height*.52) if visible
                     else (0,helmet_front(0,2.204,.046),2.204))
        return verts
    # Two rings form a beveled rim; the cavity uses an outer ring + center.
    for r in range(2 if part=="rim" else 1):
        w=width+(.014 if r==0 and part=="rim" else 0)
        h=height+(.012 if r==0 and part=="rim" else 0)
        off=(.038 if r==0 else .057) if part=="rim" else .036
        for i in range(count):
            t=2*math.pi*i/count;x=w*math.cos(t)
            z=2.204+h*math.sin(t)+smile*math.cos(t)**2
            verts.append((x,helmet_front(x,z,off),z))
    if part=="cavity": verts.append((0,helmet_front(0,2.204,.035),2.204))
    return verts

for part,name,material in [
        ("rim","Mouth rim precision outline",mouth_border),
        ("cavity","Mouth open burgundy recess",mouth_dark),
        ("tongue","Mouth warm coral tongue",tongue)]:
    count=64
    faces=[(i,(i+1)%count,(i+1)%count+count,i+count) for i in range(count)] if part=="rim" else [
        (count,i,(i+1)%count) for i in range(count)]
    obj=poly_mesh(name,mouth_points("REST",part),faces,material,mouth)
    obj.shape_key_add(name="Basis")
    inv=mouth.matrix_world.inverted()
    for shape in VISEMES:
        if shape=="REST":continue
        key=obj.shape_key_add(name=shape)
        for point,xyz in zip(key.data,mouth_points(shape,part)):
            point.co=inv @ Vector(xyz)

# V4: sculpted sleeves and articulated robot hands.
# Everything is true 3D and follows named shoulder / elbow / wrist bones.
# The glossy fingers have separate dark phalanx joints and ceramic fingertip caps.
hand_shell=mat("Pearl white hand ceramic",(.95,.97,1),.38,.15)
knuckle_dark=mat("Graphite finger articulation",(.017,.024,.042),.51,.24)
hand_liner=mat("Flexible navy palm underglove",(.014,.027,.070),.20,.39)
finger_cyan=mat("Electric cyan joint fillet",(.012,.51,.75),.22,.18,.48)
cuff_white=mat("Premium porcelain cuff",(.95,.97,1),.32,.17)
cuff_dark=mat("Cuff dark recessed seal",(.008,.025,.078),.44,.26)
cuff_blue=mat("Cuff anodized cobalt rim",(.017,.24,.91),.75,.13)
button_material=mat("Jacket micro button",(.14,.20,.29),.75,.19)

def rot_link(name, p, q, radius, material, parent, spherical=True):
    """Smooth-ended oriented 3D mechanical element; stays in correct joint."""
    p=Vector(p);q=Vector(q)
    mid=(p+q)/2
    obj=orb(name,mid,(radius,radius,(q-p).length/2+radius*.32),
            material,parent,32,18)
    obj.rotation_euler=(q-p).to_track_quat("Z","Y").to_euler()
    if not spherical: obj.scale.z*=.92
    return obj

def sleeve_mesh(name,p,q,r0,r1,parent,material):
    """Tailored organic tapered tube, overlap at pivots to eliminate gaps."""
    v=(Vector(q)-Vector(p));axis=v.normalized()
    tangent=axis.cross(Vector((0,1,0))).normalized()
    if tangent.length<.01:tangent=axis.cross(Vector((0,0,1))).normalized()
    bitangent=axis.cross(tangent).normalized()
    verts=[]; faces=[];num=28
    profiles=[(-.045,.66),(.035,.96),(.16,1.05),(.42,1.06),(.73,1.01),(.94,.91),(1.045,.67)]
    for t,r in profiles:
        cen=Vector(p)+v*t
        rr=r0+(r1-r0)*max(0,min(1,t))
        for k in range(num):
            th=2*math.pi*k/num
            pt=cen+rr*r*(tangent*math.cos(th)+bitangent*math.sin(th))
            verts.append(tuple(pt))
    for j in range(len(profiles)-1):
        for k in range(num):
            a=j*num+k;b=j*num+(k+1)%num
            faces.append((a,b,b+num,a+num))
    faces.append(tuple(reversed(tuple(range(num)))))
    faces.append(tuple((len(profiles)-1)*num+k for k in range(num)))
    obj=poly_mesh(name,verts,faces,material,parent)
    # UV map for the woven blue cloth (Blender glTF includes the micro-weave).
    uv=obj.data.uv_layers.new(name="Fabric Weave UV")
    for pgn in obj.data.polygons:
        for li in pgn.loop_indices:
            idx=obj.data.loops[li].vertex_index
            layer=idx//num;k=idx%num
            uv.data[li].uv=(k/num*1.5,layer/(len(profiles)-1)*1.65)
    return obj

def wrist_detail(side,center,hand_position,elbow):
    """A fitted, continuous suit sleeve right up to each moving ceramic palm.

    The visible wrist is cobalt fabric with just a narrow white cuff seam.
    Graphite mechanics stay INSIDE the overlapping sleeves; no dark donut,
    dangling blue washer or exposed black ball before the hand.
    """
    c=Vector(center)
    h=Vector(hand_position)
    travel=h-c
    # Blend the sleeve through the former visible gap, even on raised poses.
    bridge_end=c+travel*.82
    sleeve_mesh("Continuous cobalt wrist extension "+side,
                tuple(c),tuple(bridge_end),.160,.133,elbow,woven)
    # Keep blue fabric behind the mic palm. The previous end-cap sphere
    # reached under and THROUGH its white shell during close-up rotation.
    sleeve_t=.36 if side=="L" else .70
    sleeve_dims=(.135,.123,.130) if side=="L" else (.145,.135,.138)
    orb("Cuff seamless cobalt sleeve end "+side,
        tuple(c+travel*sleeve_t),sleeve_dims,woven,elbow,40,26)
    # Fine porcelain shirt cuff lip: mostly hidden by overlapping outer sleeve
    # and by the hand, visible only as a clean narrow line.
    cuff_t=.65 if side=="L" else .87
    cuff_dims=(.112,.105,.106) if side=="L" else (.119,.110,.110)
    orb("Cuff slim porcelain transition "+side,
        tuple(c+travel*cuff_t),cuff_dims,cuff_white,elbow,36,22)
    # On the microphone wrist the previous oversized blue trim projected
    # directly THROUGH the white palm. Recess it inside the sleeve.
    trim_t=.47 if side=="L" else .77
    trim_dims=(.082,.076,.082) if side=="L" else (.128,.114,.115)
    orb("Cuff thin cobalt trim "+side,
        tuple(c+travel*trim_t),trim_dims,cuff_blue,elbow,36,22)
    # This small socket is wholly behind the white wrist; it preserves the
    # believable robotic joint without displaying a large black gap.
    orb("Wrist hidden mechanical socket "+side,
        tuple(c+travel*.90),(.071,.076,.074),cuff_dark,elbow,28,18)

def tapered_finger_segment(name,start,end,radius_a,radius_b,material,parent):
    """Gentle tapered phalanx with a rounded bevel, no sausage-shaped balls."""
    start,end=Vector(start),Vector(end)
    length=(end-start).length
    mid=(start+end)*.5
    bpy.ops.mesh.primitive_cone_add(
        vertices=24, radius1=radius_a,radius2=radius_b,
        depth=length, location=mid, end_fill_type="NGON")
    obj=bpy.context.object
    obj.name=name
    # The cone's +Z end is the fingertip, narrower than the knuckle end.
    obj.rotation_euler=(end-start).to_track_quat("Z","Y").to_euler()
    bevel=obj.modifiers.new("Soft tapered ceramic edges","BEVEL")
    bevel.width=.008
    bevel.segments=3
    obj.modifiers.new("Rounded highlights","WEIGHTED_NORMAL")
    return finish(obj,material,parent)

def matching_ceramic_palm(side,center,parent,show_badge=False,gripping=False):
    """Preserve the approved presenting shell; use one slim gripping shell.

    The microphone palm has its own metacarpal profile to leave clearance
    for the opposing thumb and the three-segment fingers around the shaft.
    No duplicate palm liner or knuckle plate is used on the microphone side.
    """
    h=Vector(center)
    if gripping:
        # A slim metacarpal shell on the OUTSIDE of the handle. The old
        # sideways ellipsoid extended .220 along Y and buried the thumb.
        shell=orb("Hand_almoured_ceramic_palm_"+side,tuple(h),
                  (.085,.116,.177),hand_shell,parent,48,32)
        return shell

    orb("Hand_almoured_ceramic_palm_"+side,tuple(h),
        (.220,.111,.184),hand_shell,parent,48,32)
    orb("Palm graphite perimeter "+side,
        tuple(h+Vector((0,.053,0))),(.202,.081,.162),
        knuckle_dark,parent,40,28)
    orb("Hand pearlescent knuckle plate "+side,
        tuple(h+Vector((0,-.086,.045))),(.194,.032,.111),
        hand_shell,parent,44,24)
    if show_badge:
        orb("Palm small engraved cobalt badge "+side,
            tuple(h+Vector((0,-.117,-.025))),(.063,.009,.033),
            cuff_blue,parent,32,18)

shoulders={}
elbows={}
wrists={}
knuckle_pivots={}
thumbs={}
for side,sign in [("L",-1),("R",1)]:
    # Keep a continuous shoulder silhouette, consistent left and right.
    pos=(sign*.76,-.042,1.884)
    shoulder=pivot("Shoulder_"+side,pos,root)
    shoulders[side]=shoulder
    orb("Shoulder nested graphite ball "+side,pos,(.201,.207,.215),knuckle_dark,root,40,26)
    # The upper sleeve's dome rotates WITH the shoulder; shoulder ball is hidden.
    orb("Shoulder rounded cobalt fabric cap "+side,
        (sign*.802,-.092,1.865),(.295,.263,.260),woven,shoulder,48,30)

    a=(sign*.84,-.091,1.848)
    b=(sign*1.132,-.198,1.557)
    sleeve_mesh("Tailored upper sleeve "+side,a,b,.217,.188,shoulder,woven)
    orb("Elbow gathered fabric seam "+side,b,(.198,.191,.192),woven,shoulder,38,22)
    elbow=pivot("Elbow_"+side,b,shoulder)
    elbows[side]=elbow
    orb("Elbow flexible inner graphite joint "+side,b,(.112,.122,.116),knuckle_dark,elbow,30,20)

    # Right arm stays inside the 9:16 frame; left bends to hold the microphone.
    c=(sign*1.285,-.404,1.572) if side=="R" else (-.654,-.682,1.637)
    sleeve_mesh("Tailored forearm "+side,b,c,.189,.159,elbow,woven)
    orb("Forearm fitted sleeve edge "+side,c,(.170,.161,.158),woven,elbow,36,22)
    # Physical stitching on cloth at the elbow, not a disconnected floating arc.
    for k in (-1,1):
        seam_z=b[2]+.082*k
        tube("Elbow seam "+side+" "+str(k),
             (b[0]-.072,b[1]-.08,seam_z),
             (b[0]+.074,b[1]-.080,seam_z),
             .006,suit_highlight,shoulder,10)
    hand_anchor=(1.425,-.552,1.691) if side=="R" else (-.560,-.738,1.701)
    wrist_detail(side,c,hand_anchor,elbow)
    wrist=pivot("Wrist_"+side,c,elbow)
    wrists[side]=wrist

    # 3D wrist-to-hand geometry stays correctly connected to the cuff:
    # anatomy is different for a microphone-gripping hand and open presenting palm.
    if side=="R":
        # Open palm faces viewer (-Y). Knuckles project UP rather than sideways.
        # The four fingers are spread across X, tips at upper Z, thumb points inward.
        hand=(1.425,-.552,1.691)
        matching_ceramic_palm(side,hand,wrist,show_badge=True)

        for j in range(4):
            # Leftmost finger leans in, rightmost angles out, as a natural wave.
            spread=(j-1.5)
            base=(1.425+spread*.092,-.559,1.808-abs(spread)*.022)
            kn=pivot("Finger_R_"+str(j)+"_Knuckle",base,wrist)
            knuckle_pivots["R_"+str(j)]=kn
            orb("Finger R "+str(j)+" graphite root",base,(.051,.051,.053),
                knuckle_dark,wrist,28,18)
            middle=(base[0]+spread*.033,base[1]-.065,
                    base[2]+.160-abs(spread)*.014)
            distal=(middle[0]+spread*.026,middle[1]-.045,
                    middle[2]+.120-abs(spread)*.018)
            rot_link("Finger R "+str(j)+" upper white shell",
                     base,middle,.044,hand_shell,kn)
            orb("Finger R "+str(j)+" middle graphite pivot",middle,
                (.046,.043,.046),knuckle_dark,kn,24,16)
            tip=pivot("Finger_R_"+str(j)+"_Tip",middle,kn)
            rot_link("Finger R "+str(j)+" distal ceramic",
                     middle,distal,.038,hand_shell,tip)
            orb("Finger R "+str(j)+" rounded black pad",distal,
                (.039,.036,.041),knuckle_dark,tip,24,16)
            orb("Finger R "+str(j)+" cyan knuckle bead",
                (base[0],base[1]-.052,base[2]+.013),
                (.024,.012,.018),finger_cyan,kn,18,12)
        thumb=pivot("Thumb_R_Root",(1.224,-.566,1.633),wrist)
        thumbs[side]=thumb
        t0=(1.224,-.566,1.633)
        t1=(1.154,-.677,1.658)
        t2=(1.200,-.728,1.710)
        orb("Thumb R black basal hinge",t0,(.060,.058,.060),
            knuckle_dark,wrist,28,18)
        rot_link("Thumb R porcelain base",t0,t1,.057,hand_shell,thumb)
        orb("Thumb R black knuckle",t1,(.048,.048,.049),
            knuckle_dark,thumb,26,18)
        rot_link("Thumb R tip ceramic",t1,t2,.043,hand_shell,thumb)
        orb("Thumb R dark contact pad",t2,(.041,.041,.040),
            knuckle_dark,thumb,24,16)
    else:
        # V15: front-readable power grip. Negative Y faces the camera.
        # One slim palm sits to the left/rear of the shaft. Each finger has
        # three phalanges and two visible graphite hinge seams. Distal links
        # turn BACK toward the handle, instead of terminating as straight rods.
        palm=(-.605,-.792,1.710)
        matching_ceramic_palm(side,palm,wrist,gripping=True)

        for j,(z,radius,reach) in enumerate([
                (1.829,.039,1.00), (1.750,.041,1.04),
                (1.671,.038,.98), (1.595,.034,.88)]):
            # Follow the tilted shaft centre at each finger height.
            cx=-.480+(z-1.442)*(.039/.552)
            cy=-.932+(z-1.442)*(-.012/.552)
            points=[Vector((cx-.174,cy+.065,z)),
                    Vector((cx-.103,cy-.059,z+.006-j*.004)),
                    Vector((cx-.005,cy-.107,z-.009-j*.006)),
                    Vector((cx+.067*reach,cy-.059,z-.026-j*.008))]
            base,bend,dip,final=points
            kn=pivot("Finger_L_"+str(j)+"_Knuckle",base,wrist)
            knuckle_pivots["L_"+str(j)]=kn
            orb("Finger L "+str(j)+" recessed graphite root",base,
                (radius*.70,)*3,knuckle_dark,kn,24,16)
            middle=pivot("Finger_L_"+str(j)+"_Middle",bend,kn)
            tip=pivot("Finger_L_"+str(j)+"_Tip",dip,middle)
            for name,pt,r,owner in [
                    ("soft hinge",bend,radius*.65,middle),
                    ("distal graphite hinge",dip,radius*.60,tip)]:
                orb("Finger L "+str(j)+" "+name,pt,(r,)*3,
                    knuckle_dark,owner,24,16)
            for k,(name,owner) in enumerate([
                    ("curled white segment",kn),
                    ("middle ceramic phalanx",middle),
                    ("curved porcelain fingertip",tip)]):
                start,end=points[k],points[k+1]
                direction=(end-start).normalized()
                # Recessed graphite bridges these small seam gaps, so there
                # is articulation without disconnected ceramic pieces.
                tapered_finger_segment("Finger L "+str(j)+" "+name,
                    start+direction*.004,end-direction*.004,
                    radius*(1-.10*k),radius*(.91-.10*k),hand_shell,owner)
            orb("Finger L "+str(j)+" rounded ceramic pad",final,
                (radius*.73,)*3,hand_shell,tip,24,16)

        # Thumb emerges from the upper/rear edge of the single palm shell,
        # crosses above the index and opposes it on the BACK of the handle.
        # Its base is connected, but neither phalanx is buried inside a palm
        # overlay. The tip contacts the shaft's positive-Y surface.
        t0=Vector((-.605,-.750,1.815))
        t1=Vector((-.521,-.783,1.872))
        t2=Vector((-.449,-.839,1.827))
        thumb=pivot("Thumb_L_Root",t0,wrist)
        thumbs[side]=thumb
        orb("Thumb L high recessed hinge",t0,(.043,.043,.043),
            hand_shell,thumb,28,18)
        orb("Thumb L upper knuckle",t1,(.035,.035,.035),
            knuckle_dark,thumb,26,18)
        for name,start,end,ra,rb in [
                ("ceramic gripping segment",t0,t1,.046,.040),
                ("gripping end",t1,t2,.039,.033)]:
            direction=(end-start).normalized()
            tapered_finger_segment("Thumb L "+name,
                start+direction*.008,end-direction*.009,
                ra,rb,hand_shell,thumb)
        orb("Thumb L upward ceramic tip",t2,(.033,.034,.034),
            hand_shell,thumb,28,18)

# A metallic satin-black microphone with a knitted-wire capsule. The handle
# passes physically between fingers and palm; headset blue lighting matches the robot.
mic_grip=mat("Mic satin-metal black handle",(.045,.061,.080),.86,.17)
mic_wire=mat("Mic interwoven graphite grille mesh",(.21,.28,.34),.88,.20)
mic_gap=mat("Mic perforation shadows",(.011,.018,.027),.18,.44)
mic_trim=mat("Mic polished stainless gunmetal bands",(.20,.35,.46),.87,.12)
mic_cyan=mat("Mic cobalt cyan illuminated accent",(.015,.52,.96),.22,.18,1.25)

tube("Microphone sculpted satin graphite grip",
     (-.480,-.932,1.442),(-.441,-.944,1.994),.064,mic_grip,wrists["L"],32)
for k in range(5):
    z=1.495+k*.089
    orb("Microphone grip fine machine-turned rings "+str(k),
        (-.476+.005*k,-.934,z),(.073,.070,.006),mic_trim,wrists["L"],36,14)
orb("Microphone polished blue neck",
    (-.442,-.943,1.973),(.107,.101,.030),cuff_blue,wrists["L"],40,22)
orb("Microphone blue illuminated collar",
    (-.440,-.943,2.002),(.110,.105,.017),mic_cyan,wrists["L"],40,20)
orb("Microphone steel capsule grille",
    (-.438,-.944,2.087),(.164,.162,.188),mic_gap,wrists["L"],48,32)
# Woven steel latitude and meridian arcs create genuine mesh lines,
# yet remain light enough for Safari/WebGL.
for k in range(11):
    z=1.958+k*.0235
    frac=(z-2.087)/.188
    rr=.163*math.sqrt(max(.025,1-frac*frac))
    ring("Microphone woven latitude "+str(k),
        (-.438,-.944,z),rr,.0037,mic_wire,wrists["L"])
for k in range(16):
    theta=2*math.pi*k/16
    vertices=[]
    for i in range(17):
        z=1.934+i*.0188
        frac=(z-2.087)/.188
        rr=.163*math.sqrt(max(.018,1-frac*frac))
        vertices.append((-.438+rr*math.cos(theta),
                         -.944+rr*math.sin(theta),z))
    for i in range(len(vertices)-1):
        tube("Microphone woven meridian "+str(k)+" "+str(i),
             vertices[i],vertices[i+1],.0032,mic_wire,wrists["L"],8)
orb("Microphone thin cobalt lower capsule seam",
    (-.438,-.943,1.947),(.130,.128,.011),mic_trim,wrists["L"],36,16)

# All woven-wire pieces are rigidly attached to the same wrist. Join only
# those static meshes, preserving the editable hand rig and the capsule body.
# This replaces hundreds of tiny draw calls with one material batch.
wire_parts=[o for o in bpy.context.scene.objects if o.name.startswith(
    ("Microphone woven latitude ","Microphone woven meridian "))]
if wire_parts:
    bpy.ops.object.select_all(action="DESELECT")
    for o in wire_parts:o.select_set(True)
    bpy.context.view_layer.objects.active=wire_parts[0]
    bpy.ops.object.join()
    bpy.context.object.name="Microphone unified woven grille"
    bpy.ops.object.select_all(action="DESELECT")

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

    for obj in [shoulders["L"],shoulders["R"],elbows["R"],head,root]:
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
for obj in [root, head, shoulders["L"], shoulders["R"], elbows["R"]]:
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
