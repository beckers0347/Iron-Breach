"""Garrison interior furniture + decoration kit (Blender, metres, Z up, front faces -Y, origin at floor centre).
Same look as the buildings: dark armour paint, riveted steel, olive fabric, yellow safety paint.
Run:  blender -b -P props_kit.py -- <out_dir>
Writes SM_Prop_<Name>.fbx for every prop plus props.json (bounds + collision box per prop).
"""
import bpy, sys, os, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import akit as K
from akit import Builder, rotz, PREVIEW
from mathutils import Vector, Matrix

PREVIEW.update({
    "Wood": (0.30, 0.19, 0.10, 0.85, 0.0), "Fabric_Olive": (0.09, 0.11, 0.06, 0.95, 0.0),
    "Mattress": (0.34, 0.37, 0.32, 0.95, 0.0), "Screen_Glow": (0.15, 0.8, 0.6, 0.3, 0.0),
    "Blue_Paint": (0.06, 0.16, 0.45, 0.55, 0.0), "Steel_Bright": (0.55, 0.56, 0.58, 0.35, 0.8),
    "Rubber": (0.02, 0.02, 0.02, 0.9, 0.0), "Paper": (0.7, 0.68, 0.6, 0.9, 0.0),
})
AP, DM, PS, CW, YP, WP, RP, LS, BO, GL = ("Armor_Paint", "Door_Metal", "Pipe_Steel", "Concrete_Weathered", "Yellow_Paint",
                                          "White_Paint", "Red_Paint", "Light_Strip", "Black_Opening", "Window_Glass")
WOOD, FAB, MAT, SCR, BLUE, STEEL, RUB, PAPER = "Wood", "Fabric_Olive", "Mattress", "Screen_Glow", "Blue_Paint", "Steel_Bright", "Rubber", "Paper"
PROPS = {}


def prop(fn):
    PROPS[fn.__name__] = fn
    return fn


def bolt_row(B, x0, x1, y, z, n, face=-1):
    for i in range(n):
        B.bolt((x0 + (x1 - x0) * i / max(1, n - 1), y, z), (0, face, 0), 0.025)


@prop
def Bunk(B):
    L, W, H = 2.05, 0.95, 1.75
    for sx in (-1, 1):
        for sy in (-1, 1):
            B.box((sx * (L / 2 - 0.04), sy * (W / 2 - 0.04), H / 2), (0.07, 0.07, H), AP)
    for z, fz in ((0.38, 0.32), (1.18, 0.32)):
        B.box((0, 0, z), (L - 0.04, W - 0.04, 0.05), AP)
        B.box((0, 0, z + 0.14), (L - 0.12, W - 0.14, 0.18), MAT)
        B.box((0.05, 0, z + 0.24), (L * 0.62, W - 0.18, 0.05), FAB)            # folded blanket
        B.box((-L / 2 + 0.3, 0, z + 0.27), (0.42, W * 0.6, 0.1), PAPER)          # pillow
        B.box((0, -W / 2 + 0.02, z + 0.05), (L - 0.04, 0.04, 0.16), AP)         # side rail
    B.box((0, W / 2 - 0.02, 1.18 + 0.1), (L - 0.04, 0.04, 0.22), AP)
    for k in range(4):                                                        # ladder
        B.box((L / 2 - 0.04, -W / 2 - 0.03, 0.25 + k * 0.28), (0.04, 0.05, 0.05), PS)
    B.box((L / 2 - 0.04, -W / 2 - 0.03, 0.9), (0.03, 0.03, 1.5), PS)
    bolt_row(B, -L / 2 + 0.1, L / 2 - 0.1, -W / 2 - 0.01, 0.38, 6)


@prop
def Locker(B):
    W, D, H = 0.55, 0.5, 1.95
    B.box((0, 0, H / 2), (W, D, H), DM)
    B.box((0, -D / 2 - 0.01, H / 2), (W - 0.06, 0.03, H - 0.1), AP)
    for k in range(5):
        B.box((0, -D / 2 - 0.03, 1.62 + k * 0.06), (W * 0.55, 0.02, 0.025), BO)
    B.box((W / 2 - 0.1, -D / 2 - 0.035, 1.0), (0.04, 0.03, 0.18), STEEL)
    B.box((0, -D / 2 - 0.03, 1.8), (0.16, 0.01, 0.07), PAPER)
    B.box((0, 0, H + 0.015), (W + 0.02, D + 0.02, 0.03), AP)
    bolt_row(B, -W / 2 + 0.06, W / 2 - 0.06, -D / 2 - 0.03, 0.12, 4)


@prop
def Footlocker(B):
    B.box((0, 0, 0.23), (0.9, 0.45, 0.44), AP)
    B.box((0, 0, 0.455), (0.92, 0.47, 0.04), DM)
    for sx in (-1, 1):
        B.box((sx * 0.3, 0, 0.23), (0.05, 0.47, 0.45), YP)
    B.box((0, -0.235, 0.36), (0.12, 0.03, 0.08), STEEL)
    for sx in (-1, 1):
        B.box((sx * 0.46, 0, 0.23), (0.04, 0.12, 0.1), STEEL)


@prop
def Desk(B):
    B.box((0, 0, 0.74), (1.5, 0.75, 0.05), DM)
    for sx in (-1, 1):
        B.box((sx * 0.7, 0, 0.36), (0.06, 0.7, 0.72), AP)
    B.box((0.45, 0, 0.5), (0.5, 0.68, 0.5), AP)
    for k in range(3):
        B.box((0.45, -0.345, 0.68 - k * 0.16), (0.44, 0.02, 0.12), DM)
        B.box((0.45, -0.36, 0.68 - k * 0.16), (0.12, 0.02, 0.02), STEEL)
    B.box((-0.4, 0.15, 0.78), (0.32, 0.22, 0.03), PAPER)                      # paperwork
    B.cyl((-0.55, 0.25, 0.9), 0.015, 0.3, PS, seg=6)                           # desk lamp
    B.box((-0.5, 0.2, 1.05), (0.22, 0.08, 0.05), AP)
    B.box((-0.5, 0.17, 1.03), (0.18, 0.04, 0.02), LS)


@prop
def Chair(B):
    B.cyl((0, 0, 0.25), 0.03, 0.5, PS, seg=6)
    for k in range(5):
        a = math.radians(72 * k)
        B.box((math.cos(a) * 0.17, math.sin(a) * 0.17, 0.05), (0.34, 0.04, 0.03), AP, yaw=math.degrees(a))
        B.cyl((math.cos(a) * 0.3, math.sin(a) * 0.3, 0.025), 0.025, 0.05, RUB, seg=6)
    B.box((0, 0, 0.52), (0.46, 0.44, 0.07), FAB)
    B.box((0, 0.2, 0.8), (0.44, 0.06, 0.5), FAB)
    B.box((0, 0.17, 0.55), (0.06, 0.06, 0.16), AP)
    for sx in (-1, 1):
        B.box((sx * 0.26, 0, 0.66), (0.04, 0.3, 0.04), AP)


@prop
def Stool(B):
    B.cyl((0, 0, 0.3), 0.025, 0.6, PS, seg=6)
    B.cyl((0, 0, 0.62), 0.17, 0.06, FAB, seg=12)
    B.cyl((0, 0, 0.06), 0.22, 0.03, AP, seg=12)


@prop
def MessTable(B):
    L, W, H = 2.4, 0.85, 0.78
    B.box((0, 0, H), (L, W, 0.045), STEEL)
    B.box((0, 0, H - 0.05), (L - 0.04, W - 0.04, 0.05), AP)
    for sx in (-1, 1):
        for sy in (-1, 1):
            B.box((sx * (L / 2 - 0.08), sy * (W / 2 - 0.08), H / 2), (0.06, 0.06, H), AP)
    B.box((0, 0, 0.2), (L - 0.2, 0.05, 0.05), AP)


@prop
def Bench(B):
    L = 2.4
    B.box((0, 0, 0.45), (L, 0.3, 0.05), AP)
    for sx in (-1, 1):
        B.box((sx * (L / 2 - 0.15), 0, 0.22), (0.05, 0.28, 0.44), AP)
    B.box((0, 0, 0.2), (L - 0.3, 0.04, 0.04), PS)


@prop
def Console(B):
    B.box((0, 0, 0.72), (1.8, 0.8, 0.06), AP)
    for sx in (-1, 1):
        B.box((sx * 0.85, 0, 0.36), (0.07, 0.75, 0.72), AP)
    B.box((0, 0.25, 0.5), (1.6, 0.04, 0.4), AP)
    for k, x in enumerate((-0.55, 0.0, 0.55)):
        B.box((x, 0.18, 1.02), (0.48, 0.05, 0.3), AP)
        B.box((x, 0.145, 1.02), (0.43, 0.01, 0.26), SCR)
        B.box((x, 0.2, 0.84), (0.05, 0.05, 0.16), PS)
    B.box((0, -0.15, 0.76), (0.62, 0.2, 0.025), RUB)                             # keyboard
    B.box((0.75, -0.15, 0.775), (0.1, 0.07, 0.03), RUB)


@prop
def RadioDesk(B):
    B.box((0, 0, 0.74), (1.4, 0.7, 0.05), DM)
    for sx in (-1, 1):
        B.box((sx * 0.65, 0, 0.36), (0.06, 0.65, 0.72), AP)
    B.box((-0.3, 0.1, 0.92), (0.5, 0.3, 0.3), AP)                                # radio set
    B.box((-0.3, -0.055, 0.92), (0.44, 0.02, 0.22), BO)
    for k in range(4):
        B.cyl((-0.48 + k * 0.1, -0.075, 0.84), 0.025, 0.03, YP if k == 0 else PS, seg=8, axis=(0, 1, 0))
    B.box((-0.3, -0.07, 1.0), (0.2, 0.01, 0.06), SCR)
    B.cyl((-0.1, 0.2, 1.35), 0.01, 0.9, PS, seg=6)                              # antenna
    B.box((0.35, 0.0, 0.775), (0.3, 0.22, 0.04), AP)                              # headset base
    B.cyl((0.35, 0.0, 0.85), 0.07, 0.015, RUB, seg=12)
    B.box((0.45, 0.2, 0.78), (0.3, 0.2, 0.03), PAPER)


@prop
def ServerRack(B):
    W, D, H = 0.8, 0.95, 2.05
    B.box((0, 0, H / 2), (W, D, H), AP)
    B.box((0, -D / 2 - 0.01, H / 2), (W - 0.08, 0.03, H - 0.12), BO)
    for k in range(9):
        z = 0.2 + k * 0.2
        B.box((0, -D / 2 - 0.03, z), (W - 0.16, 0.03, 0.15), DM)
        for j in range(5):
            B.box((-0.25 + j * 0.06, -D / 2 - 0.05, z + 0.03), (0.02, 0.01, 0.02), LS if (j + k) % 3 else SCR)
        B.box((0.2, -D / 2 - 0.05, z - 0.03), (0.2, 0.01, 0.03), BO)
    B.box((0, 0, H + 0.02), (W + 0.02, D + 0.02, 0.04), DM)
    for sx in (-1, 1):
        B.box((sx * (W / 2 + 0.01), 0, H / 2), (0.02, D - 0.1, 0.1), YP)


@prop
def MapTable(B):
    L, W, H = 2.8, 1.6, 0.95
    B.box((0, 0, H - 0.05), (L, W, 0.1), AP)
    B.box((0, 0, H + 0.005), (L - 0.2, W - 0.2, 0.02), SCR)
    B.box((0, 0, H + 0.03), (L - 0.2, 0.02, 0.01), AP)
    B.box((0, 0, H + 0.03), (0.02, W - 0.2, 0.01), AP)
    for sx in (-1, 1):
        for sy in (-1, 1):
            B.box((sx * (L / 2 - 0.15), sy * (W / 2 - 0.15), (H - 0.1) / 2), (0.12, 0.12, H - 0.1), AP)
    B.box((0, 0, 0.12), (L - 0.3, 0.1, 0.06), AP)
    B.box((0, 0, 0.12), (0.1, W - 0.3, 0.06), AP)
    B.box((0.5, 0.3, H + 0.045), (0.09, 0.09, 0.06), YP)
    B.box((-0.7, -0.2, H + 0.045), (0.09, 0.09, 0.06), RP)


@prop
def WallScreen(B):
    B.box((0, 0.06, 1.2), (3.0, 0.12, 1.5), AP)
    B.box((0, 0.0, 1.2), (2.8, 0.02, 1.3), SCR)
    for k in range(5):
        B.box((-1.0 + k * 0.5, -0.015, 1.2), (0.01, 0.01, 1.3), AP)
    B.box((0, -0.015, 1.2), (2.8, 0.01, 0.01), AP)
    B.box((0, 0.1, 0.4), (0.4, 0.2, 0.8), AP)


@prop
def WeaponRack(B):
    W, D, H = 1.9, 0.3, 1.7
    B.box((0, 0.1, H / 2), (W, 0.06, H), AP)
    B.box((0, 0.0, 0.2), (W, D, 0.05), AP)
    B.box((0, -0.1, 1.0), (W, 0.04, 0.05), PS)
    for k in range(6):
        x = -0.78 + k * 0.31
        B.box((x, -0.02, 1.0), (0.05, 0.05, 1.0), BO)                           # barrel + body
        B.box((x, -0.02, 0.62), (0.07, 0.07, 0.3), AP)
        B.box((x, 0.0, 1.55), (0.04, 0.07, 0.12), BO)
    B.box((0, 0.1, 1.68), (W, 0.07, 0.04), YP)


@prop
def AmmoCrate(B):
    B.box((0, 0, 0.17), (0.6, 0.3, 0.32), AP)
    B.box((0, 0, 0.34), (0.62, 0.32, 0.03), DM)
    B.box((0.31, 0, 0.17), (0.02, 0.2, 0.1), YP)
    B.box((0, -0.16, 0.2), (0.3, 0.01, 0.1), PAPER)
    for sx in (-1, 1):
        B.box((sx * 0.31, 0, 0.3), (0.04, 0.1, 0.03), STEEL)


@prop
def CrateStack(B):
    for (x, y, z, s) in ((-0.35, 0.0, 0.0, 1.0), (0.4, 0.05, 0.0, 0.9), (-0.3, 0.0, 0.8, 0.8), (0.4, 0.05, 0.7, 0.55)):
        h = 0.8 * s
        B.box((x, y, z + h / 2), (0.8 * s, 0.8 * s, h), DM)
        B.box((x, y - 0.4 * s - 0.005, z + h / 2), (0.7 * s, 0.01, 0.06), YP)
        for sz in (-1, 1):
            B.box((x, y, z + h / 2 + sz * h * 0.4), (0.82 * s, 0.82 * s, 0.05), AP)
        B.box((x, y - 0.4 * s - 0.01, z + h * 0.3), (0.22 * s, 0.01, 0.12), PAPER)


@prop
def ShelfUnit(B):
    W, D, H = 1.8, 0.5, 2.0
    for sx in (-1, 1):
        for sy in (-1, 1):
            B.box((sx * (W / 2 - 0.03), sy * (D / 2 - 0.03), H / 2), (0.05, 0.05, H), AP)
    for k in range(5):
        z = 0.15 + k * 0.45
        B.box((0, 0, z), (W, D, 0.03), DM)
    for k, (x, w, h) in enumerate(((-0.55, 0.5, 0.3), (0.0, 0.4, 0.25), (0.55, 0.45, 0.35), (-0.4, 0.6, 0.28), (0.35, 0.5, 0.3), (-0.5, 0.45, 0.3), (0.5, 0.5, 0.2))):
        zz = 0.17 + (k % 4) * 0.45
        B.box((x, 0, zz + h / 2), (w, D - 0.12, h), PAPER if k % 3 == 0 else (DM if k % 2 else FAB))
    B.box((0, D / 2, H / 2), (W, 0.02, H), AP)


@prop
def HospitalBed(B):
    L, W = 2.0, 0.9
    B.box((0, 0, 0.55), (L, W, 0.06), AP)
    B.box((0, 0, 0.64), (L - 0.06, W - 0.06, 0.14), WP)
    B.box((-L / 2 + 0.3, 0, 0.78), (0.45, W * 0.55, 0.1), WP)
    B.box((0.1, 0, 0.74), (L * 0.55, W - 0.1, 0.05), BLUE)
    for sy in (-1, 1):
        B.box((0.1, sy * (W / 2 + 0.02), 0.8), (L * 0.55, 0.03, 0.22), STEEL)
    for sx in (-1, 1):
        B.box((sx * (L / 2 - 0.02), 0, 0.85), (0.04, W, 0.5), AP)
        for sy in (-1, 1):
            B.cyl((sx * (L / 2 - 0.2), sy * (W / 2 - 0.1), 0.12), 0.06, 0.1, RUB, seg=10)
            B.box((sx * (L / 2 - 0.2), sy * (W / 2 - 0.1), 0.3), (0.05, 0.05, 0.3), PS)


@prop
def IVStand(B):
    B.cyl((0, 0, 0.9), 0.012, 1.8, STEEL, seg=6)
    for k in range(4):
        a = math.radians(90 * k)
        B.box((math.cos(a) * 0.2, math.sin(a) * 0.2, 0.04), (0.4, 0.03, 0.03), STEEL, yaw=math.degrees(a))
    B.box((0, 0, 1.78), (0.4, 0.02, 0.02), STEEL)
    for sx in (-1, 1):
        B.box((sx * 0.15, 0, 1.6), (0.1, 0.03, 0.2), WP)
        B.box((sx * 0.15, 0, 1.66), (0.05, 0.03, 0.04), RP)


@prop
def MedCabinet(B):
    W, D, H = 0.9, 0.45, 1.8
    B.box((0, 0, H / 2), (W, D, H), WP)
    B.box((0, -D / 2 - 0.01, 1.35), (W - 0.1, 0.02, 0.6), GL)
    B.box((0, -D / 2 - 0.01, 0.55), (W - 0.1, 0.02, 0.9), AP)
    B.box((0, -D / 2 - 0.025, 1.65), (0.2, 0.01, 0.2), WP)
    B.box((0, -D / 2 - 0.03, 1.65), (0.16, 0.01, 0.05), RP)
    B.box((0, -D / 2 - 0.03, 1.65), (0.05, 0.01, 0.16), RP)
    for k in range(3):
        B.box((0, -D / 2 - 0.03, 1.1 + k * 0.2), (W - 0.2, 0.02, 0.03), PAPER)


@prop
def Curtain(B):
    B.box((0, 0, 1.95), (1.9, 0.04, 0.04), PS)
    for sx in (-1, 1):
        B.box((sx * 0.94, 0, 1.0), (0.04, 0.04, 2.0), PS)
        B.box((sx * 0.94, 0, 0.03), (0.3, 0.3, 0.05), AP)
    B.box((0, 0, 1.0), (1.8, 0.02, 1.7), WP)
    for k in range(10):
        B.box((-0.85 + k * 0.19, -0.012, 1.0), (0.02, 0.01, 1.7), PAPER)


@prop
def Counter(B):
    L, D, H = 3.0, 0.75, 0.95
    B.box((0, 0, H / 2 - 0.02), (L, D, H - 0.06), AP)
    B.box((0, 0, H), (L + 0.04, D + 0.04, 0.05), STEEL)
    for k in range(5):
        B.box((-1.2 + k * 0.6, -D / 2 - 0.008, 0.45), (0.5, 0.01, 0.7), DM)
        B.box((-1.2 + k * 0.6 + 0.2, -D / 2 - 0.02, 0.7), (0.1, 0.02, 0.02), STEEL)
    B.box((0, D / 2 - 0.08, H + 0.4), (L, 0.04, 0.6), STEEL)
    B.box((0.6, 0.0, H + 0.04), (0.5, 0.35, 0.05), STEEL)


@prop
def Stove(B):
    B.box((0, 0, 0.47), (1.2, 0.8, 0.94), STEEL)
    B.box((0, -0.401, 0.4), (1.0, 0.01, 0.55), AP)
    B.box((0, -0.41, 0.6), (0.7, 0.01, 0.05), PS)
    for sx in (-1, 1):
        for sy in (-1, 1):
            B.cyl((sx * 0.28, sy * 0.18, 0.955), 0.12, 0.02, BO, seg=14)
    B.box((0, 0.33, 1.18), (1.2, 0.14, 0.48), STEEL)
    B.box((0, 0.1, 1.9), (0.7, 0.5, 0.2), STEEL)
    B.box((0, 0.3, 2.3), (0.3, 0.3, 0.6), STEEL)


@prop
def Fridge(B):
    B.box((0, 0, 0.95), (0.9, 0.8, 1.9), STEEL)
    B.box((0, -0.401, 1.3), (0.88, 0.01, 1.1), AP)
    B.box((0, -0.401, 0.45), (0.88, 0.01, 0.8), AP)
    B.box((0.35, -0.42, 1.3), (0.03, 0.03, 0.4), PS)
    B.box((0.35, -0.42, 0.45), (0.03, 0.03, 0.4), PS)


@prop
def Barrel(B):
    B.cyl((0, 0, 0.45), 0.29, 0.9, AP, seg=14)
    for z in (0.15, 0.45, 0.75):
        B.cyl((0, 0, z), 0.3, 0.04, PS, seg=14)
    B.cyl((0, 0, 0.91), 0.25, 0.03, YP, seg=14)


@prop
def TrashBin(B):
    B.cyl((0, 0, 0.35), 0.25, 0.7, DM, seg=12)
    B.cyl((0, 0, 0.72), 0.27, 0.05, AP, seg=12)
    B.box((0, -0.26, 0.55), (0.1, 0.01, 0.1), YP)


@prop
def Workbench(B):
    L, D, H = 2.2, 0.8, 0.95
    B.box((0, 0, H), (L, D, 0.07), WOOD)
    B.box((0, 0, 0.45), (L - 0.1, D - 0.1, 0.04), AP)
    for sx in (-1, 1):
        for sy in (-1, 1):
            B.box((sx * (L / 2 - 0.06), sy * (D / 2 - 0.06), H / 2), (0.08, 0.08, H), AP)
    B.box((0.6, -0.3, H + 0.1), (0.1, 0.2, 0.15), PS)                           # vise
    B.box((0.6, -0.4, H + 0.12), (0.12, 0.04, 0.1), AP)
    B.box((0, D / 2 - 0.02, 1.55), (L, 0.04, 1.0), AP)                          # pegboard
    for k in range(7):
        B.box((-0.9 + k * 0.3, D / 2 - 0.05, 1.7 - (k % 3) * 0.2), (0.04, 0.05, 0.22 + (k % 2) * 0.1), PS if k % 2 else YP)
    B.box((-0.6, 0.0, H + 0.06), (0.4, 0.3, 0.05), RP)


@prop
def ToolChest(B):
    B.box((0, 0, 0.55), (0.85, 0.55, 1.1), RP)
    B.box((0, 0, 1.12), (0.87, 0.57, 0.04), AP)
    for k in range(5):
        B.box((0, -0.28, 0.2 + k * 0.19), (0.78, 0.015, 0.16), AP)
        B.box((0, -0.295, 0.2 + k * 0.19), (0.3, 0.02, 0.025), STEEL)
    for sx in (-1, 1):
        B.cyl((sx * 0.36, 0, 0.05), 0.05, 0.06, RUB, seg=8, axis=(0, 1, 0))


@prop
def PartsCrate(B):
    B.box((0, 0, 0.5), (1.5, 1.0, 1.0), DM)
    for k in range(4):
        B.box((-0.55 + k * 0.37, -0.505, 0.5), (0.05, 0.01, 0.95), AP)
    for sz in (0.04, 0.96):
        B.box((0, 0, sz), (1.52, 1.02, 0.08), AP)
    B.box((0, -0.51, 0.7), (0.6, 0.01, 0.2), YP)
    B.box((0, -0.515, 0.7), (0.5, 0.01, 0.06), BO)


@prop
def GasCylinders(B):
    B.box((0, 0, 0.1), (1.0, 0.45, 0.2), AP)
    for k, c in enumerate((BLUE, RP, YP)):
        B.cyl((-0.3 + k * 0.3, 0, 0.75), 0.11, 1.1, c, seg=12)
        B.cyl((-0.3 + k * 0.3, 0, 1.35), 0.06, 0.1, PS, seg=8)
    B.box((0, 0.2, 0.8), (0.9, 0.03, 0.05), PS)


@prop
def WorkLight(B):
    for k in range(3):
        a = math.radians(120 * k)
        B.box((math.cos(a) * 0.3, math.sin(a) * 0.3, 0.5), (0.04, 0.04, 1.0), PS, rot=Matrix.Rotation(math.radians(12), 4, "Z"))
    B.cyl((0, 0, 1.0), 0.03, 1.0, PS, seg=6)
    B.box((0, 0, 1.95), (0.5, 0.15, 0.3), AP)
    B.box((0, -0.08, 1.95), (0.44, 0.01, 0.24), LS)
    B.cyl((0, 0, 0.1), 0.35, 0.04, AP, seg=3)


@prop
def FloorMat(B):
    B.box((0, 0, 0.012), (1.6, 1.0, 0.025), RUB)
    B.box((0, 0, 0.026), (1.52, 0.92, 0.004), YP)
    B.box((0, 0, 0.03), (1.46, 0.86, 0.004), RUB)


@prop
def Cot(B):
    L, W = 1.9, 0.65
    B.box((0, 0, 0.35), (L, W, 0.04), FAB)
    for sx in (-1, 1):
        for sy in (-1, 1):
            B.box((sx * (L / 2 - 0.06), sy * (W / 2 - 0.04), 0.17), (0.04, 0.04, 0.34), PS, rot=Matrix.Rotation(math.radians(sx * 0), 4, "Y"))
    for sy in (-1, 1):
        B.box((0, sy * W / 2, 0.33), (L, 0.04, 0.05), PS)


def export_all(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    info = {}
    for name, fn in PROPS.items():
        K.reset()
        B = Builder("Prop_" + name, hash(name) % 997)
        fn(B)
        ob = B.to_object("SM_Prop_" + name)
        bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
        mn = [round(min(v[i] for v in bb), 3) for i in range(3)]
        mx = [round(max(v[i] for v in bb), 3) for i in range(3)]
        hull = bpy.data.objects.new("UCX_SM_Prop_" + name + "_01", bpy.data.meshes.new("h"))
        import bmesh
        hb = bmesh.new()
        r = bmesh.ops.create_cube(hb, size=1.0)
        c = [(mn[i] + mx[i]) / 2 for i in range(3)]
        s = [mx[i] - mn[i] for i in range(3)]
        bmesh.ops.transform(hb, matrix=Matrix.Translation(c) @ Matrix.Diagonal((s[0], s[1], s[2], 1)), verts=r["verts"])
        hb.to_mesh(hull.data)
        hb.free()
        bpy.context.scene.collection.objects.link(hull)
        K.export_fbx(os.path.join(out_dir, "SM_Prop_%s.fbx" % name), [ob, hull])
        tris = sum(len(p.vertices) - 2 for p in ob.data.polygons)
        info[name] = {"min": mn, "max": mx, "tris": tris}
        print("PROP", name, "size", [round(s[i], 2) for i in range(3)], "tris", tris)
    json.dump(info, open(os.path.join(out_dir, "props.json"), "w"), indent=1)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    export_all(argv[0] if argv else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Props"))
    print("PROPS DONE", len(PROPS))
