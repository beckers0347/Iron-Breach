"""Build the Carrowgate garrison buildings (Armory 03, Medical 05, Command 06, Mess Hall 07, Main Gate 01).
Run:  blender -b -P build_all.py -- <out_root> [Name ...]
Writes <out_root>/<Name>/SM_<Name>.fbx (+UCX hulls), SK_<Name>_Door_<key>.fbx (1-bone skeletal + open anim),
<Name>.json (doors, sensor volumes, lights) and a Workbench preview PNG.
"""
import sys, os, json, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import importlib
import bpy
import akit as K
importlib.reload(K)
from akit import *
from mathutils import Vector, Matrix

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[0] if argv else os.path.join(HERE, "..")
ONLY = set(argv[1:])


def base(B, L, W, H, t, plinth=True):
    """Floor slab, plinth, roof slab. Returns roof top z."""
    B.box((0, 0, -0.15), (L, W, 0.3), "Concrete_Weathered", inward=Z, mat_in="Interior_Concrete", hull=True)
    if plinth:
        B.box((0, 0, -0.2), (L + 0.3, W + 0.3, 0.7), "Armor_Paint")
    return roof(B, L, W, H)


def grid_lights(L, W, H, nx, ny, kind="amber"):
    pts = []
    for i in range(nx):
        for j in range(ny):
            x = -L / 2 + L * (i + 0.5) / nx
            y = -W / 2 + W * (j + 0.5) / ny
            pts.append({"p": (round(x, 2), round(y, 2), round(H - 0.5, 2)), "kind": kind})
    return pts


def finish(name, code, B, doors, lights, meta):
    out_dir = os.path.join(OUT, name)
    os.makedirs(out_dir, exist_ok=True)
    ob = B.to_object("SM_" + name)
    hulls = B.hull_objects("UCX_SM_" + name)
    K.export_fbx(os.path.join(out_dir, "SM_%s.fbx" % name), [ob] + hulls)
    info = {"name": name, "code": code, "front": "-Y local (Blender); UE local +Y", "doors": {}, "lights": lights, "tris": 0}
    info["n_hulls"] = len(hulls)
    info["hull_boxes"] = [[[round(v, 3) for v in c], [round(v, 3) for v in sz], round(yaw, 2)] for c, sz, yaw in B.hulls]
    info["tris"] = sum(len(p.vertices) - 2 for p in ob.data.polygons)
    info.update(meta)
    # bounds
    bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    info["bounds_min"] = [round(min(v[i] for v in bb), 2) for i in range(3)]
    info["bounds_max"] = [round(max(v[i] for v in bb), 2) for i in range(3)]
    for d in doors:
        fname = K.export_door(d, out_dir, name)
        v = dict(d.vols)
        v.update({"fbx": fname, "kind": d.kind, "pivot": [round(x, 3) for x in d.pivot], "seconds": d.seconds})
        info["doors"][d.key] = v
    json.dump(info, open(os.path.join(out_dir, name + ".json"), "w"), indent=1)
    preview(os.path.join(out_dir, "prev_front.png"), name, ob, info)
    print("BUILT", name, "tris", info["tris"], "hulls", len(hulls), "bounds", info["bounds_min"], info["bounds_max"], "doors", list(info["doors"]))


def preview(path, name, building, info):
    scn = bpy.context.scene
    # show doors closed + open copies are skipped; render building and doors in rest pose
    scn.render.engine = "BLENDER_WORKBENCH"
    scn.display.shading.light = "STUDIO"
    scn.display.shading.color_type = "MATERIAL"
    scn.render.resolution_x, scn.render.resolution_y = 1100, 700
    for o in list(bpy.data.objects):
        if o.name.startswith("UCX_"):
            o.hide_render = True
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    scn.collection.objects.link(cam)
    scn.camera = cam
    mn, mx = Vector(info["bounds_min"]), Vector(info["bounds_max"])
    c, d = (mn + mx) / 2, (mx - mn).length
    for tag, vec in (("front", Vector((-0.75, -1.25, 0.55))), ("rear", Vector((0.8, 1.2, 0.6)))):
        cam.location = c + vec * d * 1.25
        cam.rotation_euler = (c - cam.location).to_track_quat("-Z", "Y").to_euler()
        scn.render.filepath = path.replace("prev_front", "prev_" + tag)
        bpy.ops.render.render(write_still=True)


# =============================================================================================
def build_armory():
    name, L, W, H, t = "Armory", 24.0, 17.0, 8.0, 0.8
    K.reset()
    B = Builder(name, 3)
    top = base(B, L, W, H, t)
    front = [(0.0, 6.0, 4.6, 0.0), (-8.5, 1.5, 2.3, 0.0)]
    back = [(6.0, 1.5, 2.3, 0.0)]
    wall(B, L, W, H, t, "front", front)
    wall(B, L, W, H, t, "back", back)
    wall(B, L, W, H, t, "left", [])
    wall(B, L, W, H, t, "right", [])
    for o in front:
        door_frame(B, L, W, H, "front", o[0], o[1], o[2], hazard=True)
    door_frame(B, L, W, H, "back", 6.0, 1.5, 2.3)
    buttresses(B, L, W, H, "front", [-11.2, -5.2, 5.2, 11.2])
    buttresses(B, L, W, H, "back", [-11.2, -4.0, 0.0, 4.0 + 2.5, 11.2])
    buttresses(B, L, W, H, "left", [-5.0, 0.0, 5.0])
    buttresses(B, L, W, H, "right", [-5.0, 0.0, 5.0])
    windows(B, L, W, H, "left", [-2.8, 2.8], 4.4, w=1.4, h=0.7)
    windows(B, L, W, H, "right", [-2.8, 2.8], 4.4, w=1.4, h=0.7)
    digits(B, L, W, "front", "03", 8.2, 6.4, h=1.5)
    chevron(B, L, W, "front", 8.2, 5.2, w=1.8)
    bollards(B, L, W, "front", [-11, -6.5, -3.8, 3.8, 6.5, 11])
    # rooftop plant
    vent(B, -7, -3, top, 2.2, 1.6, 1.4)
    vent(B, -7, 3, top, 2.2, 1.6, 1.4)
    fan(B, 2, -2.5, top)
    fan(B, 5, -2.5, top)
    fan(B, 2, 3.0, top)
    B.cyl((8, 3, top + 1.6), 0.9, 3.2, "Armor_Paint", seg=14)
    B.cyl((8, 3, top + 3.28), 1.0, 0.16, "Pipe_Steel", seg=14)
    mast(B, -10.5, -6, top, 7.0)
    dish(B, 10.5, -5.5, top, 1.0, yaw=-30)
    # interior: weapon racks, crates, benches
    for k in range(6):
        x = -9.5 + k * 1.9
        B.box((x, 6.6, 1.1), (1.5, 0.4, 2.2), "Armor_Paint")
        B.box((x, 6.6, 1.3), (1.4, 0.45, 0.06), "Pipe_Steel")
        B.box((x, 6.6, 1.7), (1.4, 0.45, 0.06), "Pipe_Steel")
        B.box((x, -6.0, 1.1), (1.5, 0.4, 2.2), "Armor_Paint")
    for k in range(4):
        B.box((6 + (k % 2) * 1.5, 1.5 + (k // 2) * 1.3, 0.5), (1.3, 1.0, 1.0), "Door_Metal")
    B.box((-7, 0, 0.45), (6.0, 1.0, 0.9), "Armor_Paint")
    lights_strip_row(B, L, W, H, [-8, -3, 3, 8], [-4, 4])
    doors = [slide_door("Vault", L, W, "front", 0.0, 6.0, 4.6, dirsign=1, leaf_w=6.6, seconds=1.4),
             hinge_door("FrontHatch", L, W, "front", -8.5, 1.5, 2.3, "left"),
             hinge_door("RearHatch", L, W, "back", 6.0, 1.5, 2.3, "left")]
    lights = grid_lights(L, W, H, 4, 2) + [{"p": (0, -W / 2 - 1.0, 5.6), "kind": "blue"}]
    finish(name, "03", B, doors, lights, {"footprint": [L, W, H]})


def build_medical():
    name, L, W, H, t = "Medical", 20.0, 14.0, 7.0, 0.7
    K.reset()
    B = Builder(name, 5)
    top = base(B, L, W, H, t)
    front = [(0.0, 3.6, 3.0, 0.0)]
    left = [(0.0, 1.5, 2.3, 0.0)]
    back = [(-5.0, 1.5, 2.3, 0.0)]
    wall(B, L, W, H, t, "front", front)
    wall(B, L, W, H, t, "back", back)
    wall(B, L, W, H, t, "left", left)
    wall(B, L, W, H, t, "right", [])
    door_frame(B, L, W, H, "front", 0.0, 3.6, 3.0)
    door_frame(B, L, W, H, "left", 0.0, 1.5, 2.3)
    door_frame(B, L, W, H, "back", -5.0, 1.5, 2.3)
    buttresses(B, L, W, H, "front", [-8.6, -6.0, 6.0, 8.6], width=0.8, depth=0.8)
    buttresses(B, L, W, H, "back", [-8.6, -2.0, 2.0, 8.6], width=0.8, depth=0.8)
    buttresses(B, L, W, H, "left", [-4.5, 4.5], width=0.8, depth=0.8)
    buttresses(B, L, W, H, "right", [-4.5, 4.5], width=0.8, depth=0.8)
    windows(B, L, W, H, "front", [-3.9, 3.9], 1.7, w=1.6, h=1.1, bars=False)
    windows(B, L, W, H, "right", [-2.0, 2.0], 1.7, w=1.6, h=1.1, bars=False)
    cross(B, L, W, "front", 0.0, 5.55, size=1.5)
    cross(B, L, W, "right", 0.0, 4.6, size=1.8)
    digits(B, L, W, "front", "05", 7.3, 5.3, h=1.3)
    bollards(B, L, W, "front", [-9, -6, 6, 9])
    # roof cross (painted flat on the roof)
    B.box((-3.0, 0, top - 0.69 + 0.02), (5.0, 1.5, 0.04), "Red_Paint")
    B.box((-3.0, 0, top - 0.69 + 0.02), (1.5, 5.0, 0.04), "Red_Paint")
    fan(B, 5.5, -3, top)
    fan(B, 5.5, 3, top)
    vent(B, 8, 0, top, 1.6, 1.4, 1.2)
    mast(B, -9, -5, top, 6.0)
    dish(B, 9, 5, top, 0.9, yaw=20)
    # interior: beds, curtains, counters
    for k in range(5):
        B.box((-8 + k * 2.0, 4.6, 0.45), (0.9, 2.0, 0.5), "White_Paint")
        B.box((-8 + k * 2.0, 4.6, 0.75), (0.8, 1.9, 0.1), "Concrete_Weathered")
    for k in range(5):
        B.box((-8 + k * 2.0, 1.4, 1.0), (1.2, 0.05, 1.8), "White_Paint")
    B.box((5.0, 3.5, 0.5), (5.0, 1.0, 1.0), "Armor_Paint")
    B.box((5.0, 0.3, 0.45), (1.2, 2.2, 0.9), "White_Paint")
    lights_strip_row(B, L, W, H, [-7, -2, 3, 8], [-3.5, 2.5])
    doors = [slide_door("DoorL", L, W, "front", 0.0, 3.6, 3.0, dirsign=-1, leaf_w=2.0, cu=-0.9, seconds=1.0),
             slide_door("DoorR", L, W, "front", 0.0, 3.6, 3.0, dirsign=1, leaf_w=2.0, cu=0.9, seconds=1.0),
             hinge_door("SideHatch", L, W, "left", 0.0, 1.5, 2.3, "left"),
             hinge_door("RearHatch", L, W, "back", -5.0, 1.5, 2.3, "left")]
    for d in doors[:2]:
        d.vols = dict(doors[0].vols)
    lights = [dict(l, kind="white") for l in grid_lights(L, W, H, 4, 2)] + [{"p": (0, -W / 2 - 1.0, 4.6), "kind": "red"}]
    finish(name, "05", B, doors, lights, {"footprint": [L, W, H]})


def build_command():
    name, L, W, H, t = "Command", 15.0, 14.0, 8.5, 0.8
    K.reset()
    B = Builder(name, 6)
    top = base(B, L, W, H, t)
    front = [(0.0, 3.8, 3.6, 0.0)]
    right = [(0.0, 1.5, 2.3, 0.0)]
    back = [(-4.0, 1.5, 2.3, 0.0)]
    wall(B, L, W, H, t, "front", front)
    wall(B, L, W, H, t, "back", back)
    wall(B, L, W, H, t, "left", [])
    wall(B, L, W, H, t, "right", right)
    door_frame(B, L, W, H, "front", 0.0, 3.8, 3.6)
    door_frame(B, L, W, H, "right", 0.0, 1.5, 2.3)
    door_frame(B, L, W, H, "back", -4.0, 1.5, 2.3)
    buttresses(B, L, W, H, "front", [-6.8, -5.0, 5.0, 6.8], width=0.8, depth=0.85)
    buttresses(B, L, W, H, "back", [-6.8, 0.0, 6.8], width=0.8, depth=0.85)
    buttresses(B, L, W, H, "left", [-4.5, 0.0, 4.5], width=0.8, depth=0.85)
    buttresses(B, L, W, H, "right", [-4.5, 4.5], width=0.8, depth=0.85)
    windows(B, L, W, H, "left", [-3.0, 0.0, 3.0], 3.9, w=1.6, h=0.8)
    windows(B, L, W, H, "right", [-3.0, 3.0], 3.9, w=1.6, h=0.8)
    digits(B, L, W, "front", "06", 0.0, 6.8, h=1.5)
    chevron(B, L, W, "front", 0.0, 5.9, w=2.0, count=1)
    bollards(B, L, W, "front", [-6.5, -3.8, 3.8, 6.5])
    # tower rising from the rear of the roof
    ty, ts, th = 3.0, 5.2, 24.0 - top
    B.box((0, ty, top + th / 2), (ts, ts, th), "Concrete_Weathered", hull=True)
    for sgn in (-1, 1):
        for k in range(1, 6):
            z = top + th * k / 6
            B.box((sgn * (ts / 2 + 0.03), ty, z), (0.06, ts - 0.6, th / 7), "Armor_Paint")
            B.box((0, ty + sgn * (ts / 2 + 0.03), z), (ts - 0.6, 0.06, th / 7), "Armor_Paint")
    # glazed operations cab at the top of the tower
    cab_z = 19.4
    B.box((0, ty, cab_z + 1.1), (ts + 2.4, ts + 2.4, 2.2), "Armor_Paint", hull=True)
    for s in (-1, 1):
        B.box((s * (ts / 2 + 1.23), ty, cab_z + 1.1), (0.06, ts + 1.6, 1.1), "Window_Glass")
        B.box((0, ty + s * (ts / 2 + 1.23), cab_z + 1.1), (ts + 1.6, 0.06, 1.1), "Window_Glass")
    B.box((0, ty, cab_z + 2.35), (ts + 3.2, ts + 3.2, 0.3), "Concrete_Weathered")
    B.box((0, ty, cab_z - 0.15), (ts + 3.2, ts + 3.2, 0.3), "Concrete_Weathered")
    mast(B, 0, ty, cab_z + 2.5, 8.0)
    mast(B, 2.0, ty + 2.0, cab_z + 2.5, 4.5)
    mast(B, -2.0, ty - 2.0, cab_z + 2.5, 5.5)
    dish(B, -2.2, ty + 1.8, cab_z + 2.5, 1.3, yaw=160)
    dish(B, 2.2, ty - 1.8, cab_z + 2.5, 1.0, yaw=-20)
    # roof plant on the front half
    fan(B, -4, -3, top)
    fan(B, 0, -3, top)
    fan(B, 4, -3, top)
    vent(B, -5, 2.0, top, 1.6, 1.4, 1.2)
    # interior: consoles around a map table
    B.box((0, -1.0, 0.55), (4.0, 2.4, 1.1), "Armor_Paint")
    B.box((0, -1.0, 1.12), (3.8, 2.2, 0.06), "Light_Strip")
    for k in range(5):
        B.box((-5.5 + k * 2.75, 5.3, 1.0), (2.0, 0.8, 1.3), "Armor_Paint")
        B.box((-5.5 + k * 2.75, 5.0, 1.75), (1.8, 0.1, 0.9), "Light_Strip")
    lights_strip_row(B, L, W, H, [-4.5, 0, 4.5], [-3, 3])
    doors = [slide_door("Blast", L, W, "front", 0.0, 3.8, 3.6, dirsign=1, leaf_w=4.2, seconds=1.3),
             hinge_door("SideHatch", L, W, "right", 0.0, 1.5, 2.3, "left"),
             hinge_door("RearHatch", L, W, "back", -4.0, 1.5, 2.3, "left")]
    lights = grid_lights(L, W, H, 3, 2, "white") + [{"p": (0, ty, cab_z + 1.1), "kind": "blue"}]
    finish(name, "06", B, doors, lights, {"footprint": [L, W, H]})


def build_mess():
    name, L, W, H, t = "MessHall", 24.0, 12.0, 6.2, 0.7
    K.reset()
    B = Builder(name, 7)
    top = base(B, L, W, H, t)
    front = [(-4.0, 3.2, 2.8, 0.0), (7.5, 1.4, 2.3, 0.0)]
    back = [(-6.0, 1.6, 2.3, 0.0), (6.0, 2.6, 2.8, 0.0)]
    wall(B, L, W, H, t, "front", front)
    wall(B, L, W, H, t, "back", back)
    wall(B, L, W, H, t, "left", [])
    wall(B, L, W, H, t, "right", [])
    for o in front:
        door_frame(B, L, W, H, "front", o[0], o[1], o[2])
    for o in back:
        door_frame(B, L, W, H, "back", o[0], o[1], o[2])
    buttresses(B, L, W, H, "front", [-11.0, -7.0, -1.0, 4.0, 11.0], width=0.8, depth=0.8)
    buttresses(B, L, W, H, "back", [-11.0, -9.0, 0.0, 10.0, 11.0 - 0.0], width=0.8, depth=0.8)
    buttresses(B, L, W, H, "left", [0.0], width=0.8, depth=0.8)
    buttresses(B, L, W, H, "right", [0.0], width=0.8, depth=0.8)
    windows(B, L, W, H, "front", [-9.0, 1.5], 1.6, w=1.5, h=1.0)
    windows(B, L, W, H, "left", [-3.0, 3.0], 1.6, w=1.5, h=1.0)
    windows(B, L, W, H, "right", [-3.0, 3.0], 1.6, w=1.5, h=1.0)
    digits(B, L, W, "front", "07", -4.0, 4.9, h=1.1)
    chevron(B, L, W, "front", 8.9, 4.2, w=1.5, count=1)
    bollards(B, L, W, "front", [-9, -1.5, 3, 10])
    # roof: kitchen exhaust stacks, AC fans, vents
    for x in (3, 6.5):
        B.cyl((x, 2.8, top + 1.7), 0.55, 3.4, "Armor_Paint", seg=12)
        B.cyl((x, 2.8, top + 3.45), 0.68, 0.14, "Pipe_Steel", seg=12)
    vent(B, 10, 2.5, top, 1.8, 1.4, 1.3)
    vent(B, -10, -2.0, top, 1.8, 1.4, 1.3)
    fan(B, -4, 2.8, top)
    fan(B, 0, 2.8, top)
    fan(B, -4, -2.2, top)
    mast(B, -10.5, 4.2, top, 5.0)
    # interior: long tables and a serving counter
    for k in range(4):
        B.box((-6.5 + k * 3.2, -1.2, 0.45), (2.4, 0.9, 0.08), "Pipe_Steel")
        B.box((-6.5 + k * 3.2, -1.2, 0.22), (2.2, 0.8, 0.44), "Armor_Paint")
        B.box((-6.5 + k * 3.2, -2.3, 0.28), (2.2, 0.35, 0.05), "Door_Metal")
        B.box((-6.5 + k * 3.2, -0.1, 0.28), (2.2, 0.35, 0.05), "Door_Metal")
    B.box((5.5, 3.8, 0.5), (8.0, 1.0, 1.0), "Armor_Paint")
    B.box((5.5, 3.8, 1.02), (7.8, 0.9, 0.05), "Pipe_Steel")
    lights_strip_row(B, L, W, H, [-8, -3, 3, 8], [-2.5, 2.5])
    doors = [hinge_door("FrontL", L, W, "front", -4.8, 1.6, 2.8, "left", seconds=1.0),
             hinge_door("FrontR", L, W, "front", -3.2, 1.6, 2.8, "right", seconds=1.0),
             hinge_door("FrontHatch", L, W, "front", 7.5, 1.4, 2.3, "left"),
             hinge_door("RearHatch", L, W, "back", -6.0, 1.6, 2.3, "left"),
             slide_door("RearRoll", L, W, "back", 6.0, 2.6, 2.8, dirsign=1, leaf_w=3.0, seconds=1.1)]
    # the two front leaves share one doorway: move leaf centres/hinges to the two jambs of the 3.2 m opening
    lights = grid_lights(L, W, H, 4, 2) + [{"p": (-4.0, -W / 2 - 1.0, 3.6), "kind": "amber"}]
    finish(name, "07", B, doors, lights, {"footprint": [L, W, H]})


def build_gate():
    name, L, W, H = "MainGate", 29.0, 14.0, 15.0
    K.reset()
    B = Builder(name, 1)
    t = 0.9
    P = 9.0                                # passage width
    TW = (L - P) / 2                       # tower width
    # two towers
    for sgn in (-1, 1):
        B.off = Vector((sgn * (P / 2 + TW / 2), 0, 0))
        B.box((0, 0, -0.15), (TW, W, 0.3), "Concrete_Weathered", inward=Z, mat_in="Interior_Concrete", hull=True)
        B.box((0, 0, -0.2), (TW + 0.3, W + 0.3, 0.7), "Armor_Paint")
        back = [(0.0, 1.5, 2.3, 0.0)]
        wall(B, TW, W, H, t, "front", [])
        wall(B, TW, W, H, t, "back", back)
        wall(B, TW, W, H, t, "left", [])
        wall(B, TW, W, H, t, "right", [])
        door_frame(B, TW, W, H, "back", 0.0, 1.5, 2.3)
        buttresses(B, TW, W, H, "front", [sgn * 3.0], width=0.9, depth=0.9)
        buttresses(B, TW, W, H, "back", [-3.0, 3.0], width=0.9, depth=0.9)
        windows(B, TW, W, H, "front", [0.0], 8.0, w=2.2, h=1.0)
        windows(B, TW, W, H, "back", [0.0], 8.0, w=2.2, h=1.0)
        top = roof(B, TW, W, H)
        # glazed watch cab on the roof
        B.box((0, 0, top + 1.1), (TW - 2.4, W - 4.0, 2.2), "Armor_Paint", hull=True)
        for s in (-1, 1):
            B.box((s * ((TW - 2.4) / 2 + 0.03), 0, top + 1.25), (0.06, W - 4.8, 1.0), "Window_Glass")
            B.box((0, s * ((W - 4.0) / 2 + 0.03), top + 1.25), (TW - 3.2, 0.06, 1.0), "Window_Glass")
        B.box((0, 0, top + 2.4), (TW - 1.6, W - 3.2, 0.3), "Concrete_Weathered")
        mast(B, 1.5 * sgn, 3, top + 2.5, 5.0)
        B.cyl((0, -W / 2 + 1.0, top + 2.9), 0.35, 0.7, "Light_Strip", seg=10)
        # interior: two floors worth of lockers, stair mass
        for k in range(3):
            B.box((-1.8 + k * 1.8, 4.8, 1.0), (1.2, 0.6, 2.0), "Armor_Paint")
        B.box((0, -3.0, 0.45), (3.0, 1.2, 0.9), "Door_Metal")
        lights_strip_row(B, TW, W, H, [0], [-3.5, 2.5])
    B.off = Vector((0, 0, 0))
    # bridge deck over the passage, with parapet and rails
    dz = 8.4
    B.box((0, 0, dz), (P, W, 1.0), "Concrete_Weathered", hull=True)
    B.box((0, 0, dz - 0.65), (P, W - 0.4, 0.3), "Armor_Paint")
    for sy in (-1, 1):
        B.box((0, sy * (W / 2 - 0.2), dz + 0.5 + 0.55), (P, 0.4, 1.1), "Armor_Paint")
    # hazard band + gate frame beams across the front
    B.box((0, -W / 2 - 0.12, dz - 0.1), (P + 0.2, 0.25, 1.3), "Armor_Paint")
    B.box((0, -W / 2 - 0.26, dz - 0.1), (P - 0.6, 0.04, 0.5), "Hazard_Stripes")
    B.box((0, -W / 2 - 0.12, 0.2), (P, 0.25, 0.4), "Hazard_Stripes")
    # numbers + chevrons on the outer faces of both towers
    for sgn in (-1, 1):
        digits(B, L, W, "front", "01", sgn * (P / 2 + TW / 2), 10.8, h=1.7)
        chevron(B, L, W, "front", sgn * (P / 2 + TW / 2), 9.6, w=2.0, count=2)
    bollards(B, L, W, "front", [-7.5, -3, 3, 7.5], offset=2.2)
    # light bars either side of the passage
    for sgn in (-1, 1):
        B.box((sgn * (P / 2 + 0.06), -W / 2 + 0.4, 6.8), (0.06, 0.12, 0.9), "Light_Strip")
    # gate leaves: bi-parting in the front plane of the passage
    doors = [slide_door("GateL", L, W, "front", 0.0, P, 7.0, dirsign=-1, leaf_w=P / 2 + 0.3, cu=-P / 4 - 0.15, seconds=2.0),
             slide_door("GateR", L, W, "front", 0.0, P, 7.0, dirsign=1, leaf_w=P / 2 + 0.3, cu=P / 4 + 0.15, seconds=2.0),
             hinge_door("TowerWHatch", TW, W, "back", 0.0, 1.5, 2.3, "left", off=(-(P / 2 + TW / 2), 0, 0)),
             hinge_door("TowerEHatch", TW, W, "back", 0.0, 1.5, 2.3, "left", off=((P / 2 + TW / 2), 0, 0))]
    for d in doors[:2]:
        d.vols["sensor_h"] = (6.0, 5.0, 3.6)
        d.vols["sensor_c"] = (0.0, -W / 2 - 5.2, 3.0)
        d.vols["blocker_c"] = (d.vols["blocker_c"][0], -W / 2 + 0.2, 3.5)
        d.vols["blocker_h"] = (P / 4 - 0.1, 0.4, 3.5)
    doors[0].vols["blocker_c"] = (-P / 4, -W / 2 + 0.2, 3.5)
    doors[1].vols["blocker_c"] = (P / 4, -W / 2 + 0.2, 3.5)
    lights = [{"p": (-(P / 2 + TW / 2), 0.0, 6.0), "kind": "amber"}, {"p": (P / 2 + TW / 2, 0.0, 6.0), "kind": "amber"},
              {"p": (0.0, 0.0, 6.4), "kind": "white"}, {"p": (-(P / 2 + TW / 2), -W / 2 - 1.0, 7.0), "kind": "blue"},
              {"p": (P / 2 + TW / 2, -W / 2 - 1.0, 7.0), "kind": "blue"}]
    finish(name, "01", B, doors, lights, {"footprint": [L, W, H], "passage_width": P})


import types
import buildings_v2 as V2
importlib.reload(V2)
_ctx = types.SimpleNamespace(base=base, grid_lights=grid_lights, finish=finish)
BUILDERS = {"Armory": lambda: V2.armory(_ctx), "Medical": lambda: V2.medical(_ctx), "Command": lambda: V2.command(_ctx),
            "MessHall": lambda: V2.mess(_ctx), "MainGate": lambda: V2.gate(_ctx)}
for key, fn in BUILDERS.items():
    if ONLY and key not in ONLY:
        continue
    fn()
print("ALL DONE")
