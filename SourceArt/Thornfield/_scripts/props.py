"""Thornfield prop kit. Run: TEX_DIR=out_tex2k NOPREVIEW=1 python3 props.py <outdir>
One FBX per prop (single joined mesh + UCX boxes), origin at bottom centre, front -Y, metres."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector, Matrix, Euler
import kit
from kit import box, cylinder, hull, uv_box, join, finalize_static
import kit2
from kit2 import cyl_axis

OUT = sys.argv[-1]
os.makedirs(OUT, exist_ok=True)


def rotated(ob, euler):
    ob.data.transform(Euler(euler).to_matrix().to_4x4())
    return ob


def wood():
    return kit.flat_mat("M_Wood", (0.35, 0.24, 0.14), 0.85)


def export(name, parts, ucx):
    kit.finalize_static
    for p in parts:
        uv_box(p)
    ob = join(name, parts)
    finalize_static(ob)
    cols = []
    for i, (mn, mx) in enumerate(ucx):
        cols.append(box("UCX_%s_%02d" % (name, i), mn, mx))
    kit.export_fbx(os.path.join(OUT, name + ".fbx"), [ob] + cols)
    tris = sum(len(p.vertices) - 2 for p in ob.data.polygons)
    print("PROP", name, "tris", tris, "ucx", len(cols), "slots", [m.name for m in ob.data.materials])


def start():
    kit.reset()
    return kit.std_materials()


# 1 perimeter wall segment 4 m long, 2.6 m concrete + 0.6 m wire arms
def perimeter_wall():
    M = start(); P = []
    P.append(box("w", (-2, -0.15, 0), (2, 0.15, 2.6), M["concrete"], bev=0.03))
    P.append(box("cap", (-2.05, -0.2, 2.6), (2.05, 0.2, 2.75), M["concrete_dk"], bev=0.02))
    for x in (-2.0, 0.0, 2.0):
        P.append(box("post", (x - 0.15, -0.22, 0), (x + 0.15, 0.22, 2.8), M["concrete_dk"], bev=0.03))
    for s in (-1, 1):                       # outward-leaning wire arms
        P.append(box("arm", (-2, s * 0.15 - 0.03, 2.75), (2, s * 0.15 + 0.03, 2.82), M["steel_dk"]))
    for z in (2.9, 3.1, 3.3):
        P.append(cyl_axis("wire", (0, 0, z), 0.02, 4.0, "x", M["steel"], 6))
    P.append(box("strip", (-2, -0.16, 0.0), (2, 0.16, 0.25), M["hazard"]))
    export("SM_PerimeterWall", P, [((-2.05, -0.22, 0), (2.05, 0.22, 3.4))])


def jersey():
    M = start()
    pts = [(-1.5, -0.3, 0), (1.5, -0.3, 0), (1.5, 0.3, 0), (-1.5, 0.3, 0),
           (-1.5, -0.2, 0.35), (1.5, -0.2, 0.35), (1.5, 0.2, 0.35), (-1.5, 0.2, 0.35),
           (-1.5, -0.1, 0.8), (1.5, -0.1, 0.8), (1.5, 0.1, 0.8), (-1.5, 0.1, 0.8)]
    h = hull("jb", pts, M["concrete"], bev=0.02)
    export("SM_JerseyBarrier", [h], [((-1.5, -0.3, 0), (1.5, 0.3, 0.8))])


def tanktrap():
    M = start(); P = []
    for e in ((0, 0, 0), (math.radians(90), 0, math.radians(45)), (0, math.radians(90), math.radians(45))):
        b = box("beam", (-0.7, -0.07, -0.07), (0.7, 0.07, 0.07), M["steel_dk"], bev=0.01)
        rotated(b, e)
        b.data.transform(Matrix.Translation((0, 0, 0.5)))
        P.append(b)
    export("SM_TankTrap", P, [((-0.55, -0.55, 0.0), (0.55, 0.55, 1.0))])


def container():
    M = start(); P = []
    L, W, H = 6.06, 2.44, 2.59
    P.append(box("body", (-L / 2, -W / 2, 0.1), (L / 2, W / 2, H), M["olive"], bev=0.02))
    P.append(box("base", (-L / 2, -W / 2, 0), (L / 2, W / 2, 0.15), M["steel_dk"]))
    n = int(L / 0.3)
    for i in range(n):
        x = -L / 2 + 0.15 + i * (L - 0.3) / (n - 1)
        for s in (-1, 1):
            P.append(box("rib", (x - 0.05, s * W / 2 - (0.02 if s > 0 else 0.0) - (0.03 if s < 0 else 0.0), 0.25), (x + 0.05, s * W / 2 + (0.03 if s > 0 else 0.0), H - 0.15), M["olive"]))
    for z in (0.5, 2.0):                    # door locking bars on the -Y... end (front is the door end, +X)
        P.append(box("bar", (L / 2, -0.9, z), (L / 2 + 0.06, 0.9, z + 0.05), M["steel"]))
    for sx in (-1, 1):
        for sy in (-1, 1):
            P.append(box("corner", (sx * (L / 2 - 0.08) - 0.08, sy * (W / 2 - 0.08) - 0.08, 0), (sx * (L / 2 - 0.08) + 0.08, sy * (W / 2 - 0.08) + 0.08, H), M["steel_dk"]))
    P.append(box("stripe", (-0.7, -W / 2 - 0.035, 1.0), (0.7, -W / 2, 1.5), M["hazard"]))
    export("SM_CargoContainer", P, [((-L / 2, -W / 2, 0), (L / 2 + 0.06, W / 2, H))])


def crate():
    M = start(); P = []
    P.append(box("c", (-0.5, -0.5, 0), (0.5, 0.5, 0.9), M["steel_dk"], bev=0.03))
    for z in (0.15, 0.7):
        P.append(box("band", (-0.52, -0.52, z), (0.52, 0.52, z + 0.08), M["hazard"]))
    P.append(box("lid", (-0.45, -0.45, 0.9), (0.45, 0.45, 0.95), M["steel"]))
    export("SM_Crate", P, [((-0.52, -0.52, 0), (0.52, 0.52, 0.95))])


def pallet():
    M = start(); P = []; W = wood()
    for x in (-0.55, 0.0, 0.55):
        P.append(box("s", (x - 0.06, -0.5, 0), (x + 0.06, 0.5, 0.1), W))
    for i in range(5):
        y = -0.46 + i * 0.23
        P.append(box("d", (-0.6, y - 0.05, 0.1), (0.6, y + 0.05, 0.12), W))
    export("SM_Pallet", P, [((-0.6, -0.5, 0), (0.6, 0.5, 0.12))])


def fueltank():
    M = start(); P = []
    P.append(cyl_axis("tank", (0, 0, 1.3), 0.85, 4.0, "x", M["olive"], 24))
    for x in (-1.3, 1.3):
        P.append(box("saddle", (x - 0.15, -0.8, 0), (x + 0.15, 0.8, 0.6), M["concrete_dk"], bev=0.02))
    P.append(cyl_axis("band", (0, 0, 1.3), 0.87, 0.3, "x", M["hazard"], 24))
    P.append(cylinder("dome", (0.6, 0, 2.2), 0.25, 0.2, M["steel"], 12))
    P.append(box("gauge", (1.9, -0.1, 0.9), (2.05, 0.1, 1.5), M["steel_dk"]))
    export("SM_FuelTank", P, [((-2.1, -0.87, 0), (2.1, 0.87, 2.4))])


def generator():
    M = start(); P = []
    P.append(box("b", (-1.0, -0.45, 0.1), (1.0, 0.45, 1.2), M["steel_dk"], bev=0.03))
    P.append(box("skid", (-1.1, -0.5, 0), (1.1, 0.5, 0.12), M["steel"]))
    P.append(box("panel", (-0.5, -0.47, 0.5), (0.5, -0.45, 1.0), M["yellow"]))
    P.append(box("led", (0.3, -0.48, 0.9), (0.4, -0.45, 0.95), M["amber"]))
    P.append(cylinder("exh", (0.7, 0.2, 1.5), 0.06, 0.6, M["steel"], 10))
    P.append(box("vent", (-0.9, -0.46, 0.3), (-0.2, -0.45, 1.0), M["steel"]))
    export("SM_Generator", P, [((-1.1, -0.5, 0), (1.1, 0.5, 1.8))])


def lightpole():
    M = start(); P = []
    P.append(cylinder("base", (0, 0, 0.15), 0.25, 0.3, M["concrete_dk"], 12))
    P.append(cylinder("pole", (0, 0, 3.8), 0.1, 7.0, M["steel_dk"], 10))
    P.append(box("arm", (0, -0.05, 7.0), (1.6, 0.05, 7.1), M["steel_dk"]))
    P.append(box("lamp", (1.1, -0.2, 6.9), (1.8, 0.2, 7.0), M["steel"]))
    P.append(box("lens", (1.15, -0.17, 6.86), (1.75, 0.17, 6.9), M["white"]))
    export("SM_LightPole", P, [((-0.25, -0.25, 0), (0.25, 0.25, 7.1))])


def sign():
    M = start(); P = []
    P.append(cylinder("post", (0, 0, 1.1), 0.04, 2.2, M["steel_dk"], 8))
    P.append(box("back", (-0.6, -0.03, 1.5), (0.6, 0.03, 2.3), M["steel"], bev=0.01))
    P.append(box("face", (-0.57, -0.045, 1.53), (0.57, -0.03, 2.27), M["banner"]))
    P.append(box("strip", (-0.57, -0.05, 1.53), (0.57, -0.045, 1.65), M["hazard"]))
    export("SM_Sign", P, [((-0.6, -0.06, 0), (0.6, 0.06, 2.3))])


for fn in (perimeter_wall, jersey, tanktrap, container, crate, pallet, fueltank, generator, lightpole, sign):
    fn()
