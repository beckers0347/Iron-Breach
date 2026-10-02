"""Thornfield Blender kit. Units: meters. Front of buildings faces -Y. Z up.
Run inside bpy (pip module) headless.
"""
import bpy, bmesh, math, os, json, random
from mathutils import Vector, Matrix, noise

TEX_DIR = os.environ.get("TEX_DIR", "out_tex")
MATS = {}
TILES = {"Concrete": 3.0, "ConcreteDark": 3.0, "Steel": 2.0, "MossEarth": 4.0,
         "FloorConcrete": 3.0, "Hazard": 1.0, "Banner": 1.0}


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    MATS.clear()


def _img(name, noncolor=False):
    p = os.path.join(TEX_DIR, name)
    im = bpy.data.images.load(p, check_existing=True)
    if noncolor:
        im.colorspace_settings.name = "Non-Color"
    return im


def tex_mat(key, tint=None, mname=None):
    """PBR material from T_<key>_BC/_N/_ORM."""
    mname = mname or "M_" + key
    if mname in MATS:
        return MATS[mname]
    m = bpy.data.materials.new(mname)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(bsdf.outputs[0], out.inputs[0])
    bc = nt.nodes.new("ShaderNodeTexImage"); bc.image = _img(f"T_{key}_BC.png")
    nm = nt.nodes.new("ShaderNodeTexImage"); nm.image = _img(f"T_{key}_N.png", True)
    orm = nt.nodes.new("ShaderNodeTexImage"); orm.image = _img(f"T_{key}_ORM.png", True)
    col = bc.outputs[0]
    if tint:
        mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"; mix.blend_type = "MULTIPLY"
        mix.inputs[0].default_value = 1.0
        mix.inputs[7].default_value = (*tint, 1)
        nt.links.new(col, mix.inputs[6]); col = mix.outputs[2]
    nt.links.new(col, bsdf.inputs["Base Color"])
    sep = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(orm.outputs[0], sep.inputs[0])
    nt.links.new(sep.outputs[1], bsdf.inputs["Roughness"])
    nt.links.new(sep.outputs[2], bsdf.inputs["Metallic"])
    nmap = nt.nodes.new("ShaderNodeNormalMap")
    nt.links.new(nm.outputs[0], nmap.inputs["Color"])
    nt.links.new(nmap.outputs[0], bsdf.inputs["Normal"])
    m["tile"] = TILES.get(key, 2.0)
    MATS[mname] = m
    return m


def flat_mat(name, color, rough=0.6, metal=0.0, emit=None, emit_strength=0.0):
    if name in MATS:
        return MATS[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = emit_strength
    m["tile"] = 1.0
    MATS[name] = m
    return m


def std_materials():
    d = {}
    d["concrete"] = tex_mat("Concrete")
    d["concrete_dk"] = tex_mat("ConcreteDark")
    d["steel"] = tex_mat("Steel")
    d["olive"] = tex_mat("Steel", tint=(0.55, 0.65, 0.5), mname="M_SteelOlive")
    d["steel_dk"] = tex_mat("Steel", tint=(0.42, 0.46, 0.56), mname="M_SteelDark")
    d["moss"] = tex_mat("MossEarth")
    d["floor"] = tex_mat("FloorConcrete")
    d["hazard"] = tex_mat("Hazard")
    d["banner"] = tex_mat("Banner")
    d["amber"] = flat_mat("M_LightAmber", (1, .5, .1), 0.4, 0, (1, .55, .1), 10)
    d["blue"] = flat_mat("M_LightBlue", (.2, .5, 1), 0.4, 0, (.25, .55, 1), 8)
    d["white"] = flat_mat("M_LightWhite", (1, 1, 1), 0.4, 0, (1, .95, .85), 12)
    d["fabric"] = flat_mat("M_Fabric", (.18, .22, .15), 0.9)
    d["glass"] = flat_mat("M_Glass", (.08, .12, .14), 0.1, 0.0)
    d["glass_amber"] = flat_mat("M_GlassAmber", (.9, .55, .2), 0.2, 0.0, (1, .6, .2), 2.5)
    d["yellow"] = flat_mat("M_SafetyYellow", (.8, .6, .05), 0.5, 0.0)
    d["line"] = flat_mat("M_RoadLine", (.85, .85, .8), 0.7, 0.0)
    d["screen"] = flat_mat("M_Screen", (0.1, 0.3, 0.5), 0.3, 0, (0.2, 0.55, 1.0), 4)
    d["solar"] = flat_mat("M_Solar", (0.04, 0.08, 0.2), 0.25, 0.6)
    return d


# ---------- geometry ----------
def _link(name, bm, mat=None):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    if mat:
        me.materials.append(mat)
    return ob


def box(name, mn, mx, mat=None, bev=0.0, seg=2):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((mn[0] if v.co.x < 0 else mx[0],
                       mn[1] if v.co.y < 0 else mx[1],
                       mn[2] if v.co.z < 0 else mx[2]))
    ob = _link(name, bm, mat)
    if bev:
        bevel(ob, bev, seg)
    return ob


def hull(name, pts, mat=None, bev=0.0, seg=2):
    bm = bmesh.new()
    for p in pts:
        bm.verts.new(p)
    r = bmesh.ops.convex_hull(bm, input=bm.verts[:])
    bmesh.ops.delete(bm, geom=list(set(r["geom_unused"] + r["geom_interior"])), context="VERTS")
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bmesh.ops.dissolve_limit(bm, angle_limit=math.radians(0.5), verts=bm.verts[:], edges=bm.edges[:])
    ob = _link(name, bm, mat)
    if bev:
        bevel(ob, bev, seg)
    return ob


def cylinder(name, center, r, h, mat=None, seg=16):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r, depth=h)
    for v in bm.verts:
        v.co += Vector(center)
    return _link(name, bm, mat)


def quad(name, p0, p1, p2, p3, mat=None, uv=((0, 0), (1, 0), (1, 1), (0, 1))):
    bm = bmesh.new()
    vs = [bm.verts.new(p) for p in (p0, p1, p2, p3)]
    f = bm.faces.new(vs)
    l = bm.loops.layers.uv.verify()
    for lp, u in zip(f.loops, uv):
        lp[l].uv = u
    return _link(name, bm, mat)


def bevel(ob, w=0.04, seg=2, angle=35):
    m = ob.modifiers.new("Bevel", "BEVEL")
    m.width = w
    m.segments = seg
    m.limit_method = "ANGLE"
    m.angle_limit = math.radians(angle)
    apply_mods(ob)


def apply_mods(ob):
    bpy.context.view_layer.objects.active = ob
    for md in list(ob.modifiers):
        with bpy.context.temp_override(object=ob, active_object=ob, selected_objects=[ob]):
            bpy.ops.object.modifier_apply(modifier=md.name)


def cut(ob, *cutters):
    for c in cutters:
        m = ob.modifiers.new("Cut", "BOOLEAN")
        m.operation = "DIFFERENCE"
        m.solver = "EXACT"
        m.object = c
        apply_mods(ob)
        bpy.data.objects.remove(c, do_unlink=True)


def uv_box(ob, tile=None):
    me = ob.data
    def tile_of(idx):
        if tile is not None:
            return tile
        if idx < len(me.materials) and me.materials[idx] is not None and "tile" in me.materials[idx]:
            return me.materials[idx]["tile"]
        return 2.0
    bm = bmesh.new()
    bm.from_mesh(me)
    uv = bm.loops.layers.uv.verify()
    mw = ob.matrix_world
    for f in bm.faces:
        n = mw.to_3x3() @ f.normal
        a = max(range(3), key=lambda i: abs(n[i]))
        tl = tile_of(f.material_index)
        for lp in f.loops:
            p = mw @ lp.vert.co
            if a == 2:
                u, v = p.x, p.y
            elif a == 1:
                u, v = p.x, p.z
            else:
                u, v = p.y, p.z
            lp[uv].uv = (u / tl, v / tl)
    bm.to_mesh(me)
    bm.free()


def set_pivot(ob, pivot):
    pv = Vector(pivot)
    for v in ob.data.vertices:
        v.co -= pv
    ob.location = pv


def smooth(ob, angle=40):
    for p in ob.data.polygons:
        p.use_smooth = True
    try:
        ob.data.set_sharp_from_angle(angle=math.radians(angle))
    except Exception:
        pass


def join(name, objs):
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    with bpy.context.temp_override(active_object=objs[0], selected_editable_objects=objs, selected_objects=objs):
        bpy.ops.object.join()
    ob = objs[0]
    ob.name = name
    ob.data.name = name
    return ob


def finalize_static(ob):
    """Recalc normals consistently, set auto smooth by angle."""
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(ob.data)
    bm.free()
    smooth(ob, 40)


# ---------- export / preview ----------
def export_fbx(path, objs):
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    for o in objs:
        o.select_set(True)
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True, object_types={"MESH"},
                             axis_forward="-Y", axis_up="Z", global_scale=1.0,
                             apply_unit_scale=True, apply_scale_options="FBX_SCALE_NONE",
                             mesh_smooth_type="FACE", add_leaf_bones=False,
                             bake_anim=False, path_mode="STRIP")


def setup_render(res=(1280, 720), samples=48, cycles=True):
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.engine = "CYCLES"
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.cycles.device = "CPU"
    sc.view_settings.view_transform = "AgX"
    w = bpy.data.worlds.new("W")
    sc.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.62, 0.66, 0.72, 1)
    bg.inputs[1].default_value = 1.0


def sun(rot=(math.radians(50), 0, math.radians(35)), energy=4.0):
    d = bpy.data.lights.new("Sun", "SUN")
    d.energy = energy
    d.angle = math.radians(3)
    o = bpy.data.objects.new("Sun", d)
    bpy.context.scene.collection.objects.link(o)
    o.rotation_euler = rot
    return o


def camera(loc, target, lens=35, name="Cam"):
    c = bpy.data.cameras.new(name)
    c.lens = lens
    c.clip_end = 500
    o = bpy.data.objects.new(name, c)
    bpy.context.scene.collection.objects.link(o)
    o.location = loc
    d = Vector(target) - Vector(loc)
    o.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    return o


def render(cam, path):
    bpy.context.scene.camera = cam
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
