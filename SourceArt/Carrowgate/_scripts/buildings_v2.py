"""v2 building definitions: taller, battered skirts, dark fluted columns, heavy louvred door portals, busy roofs.
Imported by build_all.py (which supplies base/finish/grid_lights via `ctx`)."""
import math
from mathutils import Vector
import akit as K
from akit import *


def roof_clutter(B, top, items):
    for it in items:
        k = it[0]
        if k == "vent":
            vent_tower(B, it[1], it[2], top, *it[3:])
        elif k == "tank":
            tank(B, it[1], it[2], top, *it[3:])
        elif k == "grate":
            grate_panel(B, it[1], it[2], top, *it[3:])
        elif k == "fan":
            fan(B, it[1], it[2], top)
        elif k == "mast":
            mast(B, it[1], it[2], top, it[3])
        elif k == "dish":
            dish(B, it[1], it[2], top, it[3], yaw=it[4])


def armory(ctx):
    name, L, W, H, t = "Armory", 24.0, 17.0, 12.0, 0.9
    K.reset()
    B = Builder(name, 3)
    top = ctx.base(B, L, W, H, t)
    front = [(0.0, 6.4, 6.0, 0.0), (-9.0, 1.8, 2.8, 0.0)]
    back = [(6.0, 1.8, 2.8, 0.0)]
    wall(B, L, W, H, t, "front", front)
    wall(B, L, W, H, t, "back", back)
    wall(B, L, W, H, t, "left", [])
    wall(B, L, W, H, t, "right", [])
    for o in front:
        door_frame(B, L, W, H, "front", o[0], o[1], o[2])
    door_frame(B, L, W, H, "back", 6.0, 1.8, 2.8)
    buttresses(B, L, W, H, "front", [-11.4, -6.3, 6.3, 11.4])
    buttresses(B, L, W, H, "back", [-11.4, -5.5, -1.0, 3.0, 11.4])
    buttresses(B, L, W, H, "left", [-5.5, 0.0, 5.5])
    buttresses(B, L, W, H, "right", [-5.5, 0.0, 5.5])
    windows(B, L, W, H, "left", [-2.7, 2.7], 7.6, w=2.4, h=1.3)
    windows(B, L, W, H, "right", [-2.7, 2.7], 7.6, w=2.4, h=1.3)
    pipe_run(B, L, W, "left", -6.5, 6.5, 5.2, count=3)
    pipe_run(B, L, W, "right", -6.5, 6.5, 5.2, count=3)
    digits(B, L, W, "front", "03", 8.85, 9.2, h=2.3)
    chevron(B, L, W, "front", 8.85, 7.6, w=2.4)
    bollards(B, L, W, "front", [-11, -8, -4.8, 4.8, 8, 11], offset=2.3)
    roof_clutter(B, top, [("vent", -7, -3.5, 2.8, 2.6, 3.2), ("vent", -7, 3.5, 2.8, 2.6, 3.2), ("tank", 8, 3.5, 1.3, 4.0),
                          ("tank", 4.5, 4.5, 1.0, 3.2), ("grate", 2, -3, 6.0, 2.0), ("fan", 3, 2.0), ("fan", 6.5, -3.5),
                          ("mast", -10.5, -6, 8.0), ("mast", 10.8, 6.5, 6.0), ("dish", 10.5, -5.5, 1.1, -30)])
    for k in range(7):
        x = -10.0 + k * 1.9
        B.box((x, 6.5, 1.3), (1.5, 0.4, 2.6), "Armor_Paint")
        for zz in (1.0, 1.6, 2.2):
            B.box((x, 6.5, zz), (1.4, 0.45, 0.06), "Pipe_Steel")
        B.box((x, -6.0, 1.3), (1.5, 0.4, 2.6), "Armor_Paint")
    for k in range(6):
        B.box((6 + (k % 3) * 1.5, 1.5 + (k // 3) * 1.3, 0.5), (1.3, 1.0, 1.0), "Door_Metal")
    B.box((-7, 0, 0.45), (6.0, 1.0, 0.9), "Armor_Paint")
    lights_strip_row(B, L, W, H, [-8, -3, 3, 8], [-4, 4])
    doors = [slide_door("Vault", L, W, "front", 0.0, 6.4, 6.0, dirsign=1, leaf_w=7.0, seconds=1.4),
             hinge_door("FrontHatch", L, W, "front", -9.0, 1.8, 2.8, "left"),
             hinge_door("RearHatch", L, W, "back", 6.0, 1.8, 2.8, "left")]
    lights = ctx.grid_lights(L, W, H, 4, 2) + [{"p": (0, -W / 2 - 1.0, 7.6), "kind": "blue"}]
    ctx.finish(name, "03", B, doors, lights, {"footprint": [L, W, H]})


def medical(ctx):
    name, L, W, H, t = "Medical", 20.0, 14.0, 10.5, 0.8
    K.reset()
    B = Builder(name, 5)
    top = ctx.base(B, L, W, H, t)
    wall(B, L, W, H, t, "front", [(0.0, 4.4, 3.8, 0.0)])
    wall(B, L, W, H, t, "back", [(-5.0, 1.8, 2.8, 0.0)])
    wall(B, L, W, H, t, "left", [(0.0, 1.8, 2.8, 0.0)])
    wall(B, L, W, H, t, "right", [])
    door_frame(B, L, W, H, "front", 0.0, 4.4, 3.8)
    door_frame(B, L, W, H, "left", 0.0, 1.8, 2.8)
    door_frame(B, L, W, H, "back", -5.0, 1.8, 2.8)
    buttresses(B, L, W, H, "front", [-8.8, -5.9, 5.9, 8.8], width=0.9, depth=0.9)
    buttresses(B, L, W, H, "back", [-8.8, -2.0, 2.0, 8.8], width=0.9, depth=0.9)
    buttresses(B, L, W, H, "left", [-4.6, 4.6], width=0.9, depth=0.9)
    buttresses(B, L, W, H, "right", [-4.6, 4.6], width=0.9, depth=0.9)
    windows(B, L, W, H, "front", [7.4], 2.4, w=1.4, h=1.3, bars=False)
    windows(B, L, W, H, "front", [-7.4], 2.4, w=1.4, h=1.3, bars=False)
    windows(B, L, W, H, "right", [-2.0, 2.0], 2.4, w=2.0, h=1.3, bars=False)
    cross(B, L, W, "front", 0.0, 8.2, size=2.2)
    cross(B, L, W, "right", 0.0, 6.6, size=2.4)
    digits(B, L, W, "front", "05", 7.4, 6.4, h=1.5)
    pipe_run(B, L, W, "back", 3.0, 8.0, 5.0, count=3)
    bollards(B, L, W, "front", [-9.5, -7.4, -4.4, 4.4, 7.4, 9.5], offset=2.3)
    B.box((-3.0, 0, top - 0.95 + 0.02), (5.5, 1.7, 0.04), "Red_Paint")
    B.box((-3.0, 0, top - 0.95 + 0.02), (1.7, 5.5, 0.04), "Red_Paint")
    roof_clutter(B, top, [("fan", 5.5, -3.2), ("fan", 5.5, 3.2), ("vent", 8.2, 0.0, 2.4, 2.2, 2.8), ("tank", -7.5, 4.0, 1.1, 3.2),
                          ("grate", 4, 0, 4.0, 1.6), ("mast", -9, -5, 7.0), ("dish", 9, 5, 1.0, 20)])
    for k in range(5):
        B.box((-8 + k * 2.0, 4.6, 0.45), (0.9, 2.0, 0.5), "White_Paint")
        B.box((-8 + k * 2.0, 4.6, 0.75), (0.8, 1.9, 0.1), "Concrete_Weathered")
        B.box((-8 + k * 2.0, 1.4, 1.0), (1.2, 0.05, 1.8), "White_Paint")
    B.box((5.0, 3.5, 0.5), (5.0, 1.0, 1.0), "Armor_Paint")
    B.box((5.0, 0.3, 0.45), (1.2, 2.2, 0.9), "White_Paint")
    lights_strip_row(B, L, W, H, [-7, -2, 3, 8], [-3.5, 2.5])
    doors = [slide_door("DoorL", L, W, "front", 0.0, 4.4, 3.8, dirsign=-1, leaf_w=2.5, cu=-1.1, seconds=1.0),
             slide_door("DoorR", L, W, "front", 0.0, 4.4, 3.8, dirsign=1, leaf_w=2.5, cu=1.1, seconds=1.0),
             hinge_door("SideHatch", L, W, "left", 0.0, 1.8, 2.8, "left"),
             hinge_door("RearHatch", L, W, "back", -5.0, 1.8, 2.8, "left")]
    for d in doors[:2]:
        d.vols = dict(doors[0].vols)
    lights = [dict(l, kind="white") for l in ctx.grid_lights(L, W, H, 4, 2)] + [{"p": (0, -W / 2 - 1.0, 5.6), "kind": "red"}]
    ctx.finish(name, "05", B, doors, lights, {"footprint": [L, W, H]})


def command(ctx):
    name, L, W, H, t = "Command", 15.0, 14.0, 12.5, 0.9
    K.reset()
    B = Builder(name, 6)
    top = ctx.base(B, L, W, H, t)
    wall(B, L, W, H, t, "front", [(0.0, 4.2, 4.2, 0.0)])
    wall(B, L, W, H, t, "back", [(-4.0, 1.8, 2.8, 0.0)])
    wall(B, L, W, H, t, "left", [])
    wall(B, L, W, H, t, "right", [(0.0, 1.8, 2.8, 0.0)])
    door_frame(B, L, W, H, "front", 0.0, 4.2, 4.2)
    door_frame(B, L, W, H, "right", 0.0, 1.8, 2.8)
    door_frame(B, L, W, H, "back", -4.0, 1.8, 2.8)
    buttresses(B, L, W, H, "front", [-6.5, -4.9, 4.9, 6.5], width=0.9, depth=0.9)
    buttresses(B, L, W, H, "back", [-6.5, 0.0, 6.5], width=0.9, depth=0.9)
    buttresses(B, L, W, H, "left", [-4.6, 0.0, 4.6], width=0.9, depth=0.9)
    buttresses(B, L, W, H, "right", [-4.6, 4.6], width=0.9, depth=0.9)
    windows(B, L, W, H, "left", [-2.3, 2.3], 6.8, w=1.9, h=1.3)
    windows(B, L, W, H, "right", [-2.3, 2.3], 6.8, w=1.9, h=1.3)
    windows(B, L, W, H, "back", [3.0], 6.8, w=1.6, h=1.3)
    digits(B, L, W, "front", "06", 0.0, 9.6, h=2.3)
    chevron(B, L, W, "front", 0.0, 7.9, w=2.4, count=1)
    pipe_run(B, L, W, "left", -5.5, 5.5, 4.4, count=3)
    bollards(B, L, W, "front", [-6.5, -3.8, 3.8, 6.5], offset=2.3)
    ty, ts = 3.0, 6.0
    cab_z = 19.0
    th = cab_z - top
    B.box((0, ty, top + th / 2), (ts, ts, th), "Concrete_Weathered", hull=True)
    for sgn in (-1, 1):
        for k in range(1, 6):
            z = top + th * k / 6
            B.box((sgn * (ts / 2 + 0.03), ty, z), (0.06, ts - 0.6, th / 7), "Armor_Paint")
            B.box((0, ty + sgn * (ts / 2 + 0.03), z), (ts - 0.6, 0.06, th / 7), "Armor_Paint")
    for sx in (-1, 1):
        for sy in (-1, 1):
            B.box((sx * (ts / 2 - 0.2), ty + sy * (ts / 2 - 0.2), top + th / 2), (0.5, 0.5, th), "Armor_Paint")
    B.box((0, ty, cab_z + 1.2), (ts + 2.6, ts + 2.6, 2.4), "Armor_Paint", hull=True)
    for s_ in (-1, 1):
        B.box((s_ * (ts / 2 + 1.33), ty, cab_z + 1.2), (0.06, ts + 1.8, 1.3), "Window_Glass")
        B.box((0, ty + s_ * (ts / 2 + 1.33), cab_z + 1.2), (ts + 1.8, 0.06, 1.3), "Window_Glass")
    B.box((0, ty, cab_z + 2.55), (ts + 3.4, ts + 3.4, 0.3), "Concrete_Weathered")
    B.box((0, ty, cab_z - 0.15), (ts + 3.4, ts + 3.4, 0.3), "Concrete_Weathered")
    mast(B, 0, ty, cab_z + 2.7, 7.0)
    mast(B, 2.2, ty + 2.2, cab_z + 2.7, 4.0)
    mast(B, -2.2, ty - 2.2, cab_z + 2.7, 5.0)
    dish(B, -2.4, ty + 2.0, cab_z + 2.7, 1.4, yaw=160)
    dish(B, 2.4, ty - 2.0, cab_z + 2.7, 1.1, yaw=-20)
    roof_clutter(B, top, [("vent", -5, -3.5, 2.6, 2.4, 3.0), ("vent", 5, -3.5, 2.6, 2.4, 3.0), ("fan", -4, 1.5), ("fan", 4.5, 1.5),
                          ("tank", -5.2, 3.8, 1.0, 3.0), ("grate", 0, -3.5, 3.0, 1.6)])
    B.box((0, -1.0, 0.55), (4.0, 2.4, 1.1), "Armor_Paint")
    B.box((0, -1.0, 1.12), (3.8, 2.2, 0.06), "Light_Strip")
    for k in range(5):
        B.box((-5.5 + k * 2.75, 5.3, 1.0), (2.0, 0.8, 1.3), "Armor_Paint")
        B.box((-5.5 + k * 2.75, 5.0, 1.75), (1.8, 0.1, 0.9), "Light_Strip")
    lights_strip_row(B, L, W, H, [-4.5, 0, 4.5], [-3, 3])
    doors = [slide_door("Blast", L, W, "front", 0.0, 4.2, 4.2, dirsign=1, leaf_w=4.7, seconds=1.3),
             hinge_door("SideHatch", L, W, "right", 0.0, 1.8, 2.8, "left"),
             hinge_door("RearHatch", L, W, "back", -4.0, 1.8, 2.8, "left")]
    lights = ctx.grid_lights(L, W, H, 3, 2, "white") + [{"p": (0, ty, cab_z + 1.2), "kind": "blue"}]
    ctx.finish(name, "06", B, doors, lights, {"footprint": [L, W, H]})


def mess(ctx):
    name, L, W, H, t = "MessHall", 24.0, 12.0, 9.5, 0.8
    K.reset()
    B = Builder(name, 7)
    top = ctx.base(B, L, W, H, t)
    front = [(-4.0, 3.6, 3.4, 0.0), (7.5, 1.8, 2.8, 0.0)]
    back = [(-6.0, 1.8, 2.8, 0.0), (6.0, 3.0, 3.4, 0.0)]
    wall(B, L, W, H, t, "front", front)
    wall(B, L, W, H, t, "back", back)
    wall(B, L, W, H, t, "left", [])
    wall(B, L, W, H, t, "right", [])
    for o in front:
        door_frame(B, L, W, H, "front", o[0], o[1], o[2])
    for o in back:
        door_frame(B, L, W, H, "back", o[0], o[1], o[2])
    buttresses(B, L, W, H, "front", [-11.1, -8.8, 0.5, 3.4, 11.1], width=0.9, depth=0.9)
    buttresses(B, L, W, H, "back", [-11.1, -9.3, -2.3, 1.0, 10.9], width=0.9, depth=0.9)
    buttresses(B, L, W, H, "left", [0.0], width=0.9, depth=0.9)
    buttresses(B, L, W, H, "right", [0.0], width=0.9, depth=0.9)
    windows(B, L, W, H, "front", [1.95], 3.4, w=1.4, h=1.3)
    windows(B, L, W, H, "left", [-3.0, 3.0], 3.4, w=1.8, h=1.3)
    windows(B, L, W, H, "right", [-3.0, 3.0], 3.4, w=1.8, h=1.3)
    digits(B, L, W, "front", "07", -4.0, 7.4, h=1.6)
    chevron(B, L, W, "front", 9.3, 6.6, w=1.4, count=1)
    pipe_run(B, L, W, "left", -4.5, 4.5, 6.2, count=3)
    pipe_run(B, L, W, "right", -4.5, 4.5, 6.2, count=3)
    bollards(B, L, W, "front", [-10, -7, -1, 2, 5, 10], offset=2.3)
    for x in (3.0, 6.5):
        B.cyl((x, 2.6, top + 2.6), 0.65, 5.2, "Armor_Paint", seg=12)
        B.cyl((x, 2.6, top + 5.3), 0.8, 0.16, "Pipe_Steel", seg=12)
        B.cyl((x, 2.6, top + 2.0), 0.72, 0.2, "Pipe_Steel", seg=12)
    roof_clutter(B, top, [("vent", 10, 2.4, 2.6, 2.4, 3.0), ("vent", -10, -2.0, 2.6, 2.4, 3.0), ("fan", -4, 2.6), ("fan", 0, 2.6),
                          ("fan", -4, -2.2), ("tank", -9, 3.0, 1.1, 3.2), ("grate", 1, -2.4, 4.0, 1.6), ("mast", -10.8, 4.2, 6.0)])
    for k in range(4):
        B.box((-6.5 + k * 3.2, -1.2, 0.45), (2.4, 0.9, 0.08), "Pipe_Steel")
        B.box((-6.5 + k * 3.2, -1.2, 0.22), (2.2, 0.8, 0.44), "Armor_Paint")
        B.box((-6.5 + k * 3.2, -2.3, 0.28), (2.2, 0.35, 0.05), "Door_Metal")
        B.box((-6.5 + k * 3.2, -0.1, 0.28), (2.2, 0.35, 0.05), "Door_Metal")
    B.box((5.5, 3.8, 0.5), (8.0, 1.0, 1.0), "Armor_Paint")
    B.box((5.5, 3.8, 1.02), (7.8, 0.9, 0.05), "Pipe_Steel")
    lights_strip_row(B, L, W, H, [-8, -3, 3, 8], [-2.5, 2.5])
    doors = [hinge_door("FrontL", L, W, "front", -4.9, 1.8, 3.4, "left", seconds=1.0),
             hinge_door("FrontR", L, W, "front", -3.1, 1.8, 3.4, "right", seconds=1.0),
             hinge_door("FrontHatch", L, W, "front", 7.5, 1.8, 2.8, "left"),
             hinge_door("RearHatch", L, W, "back", -6.0, 1.8, 2.8, "left"),
             slide_door("RearRoll", L, W, "back", 6.0, 3.0, 3.4, dirsign=1, leaf_w=3.4, seconds=1.1)]
    lights = ctx.grid_lights(L, W, H, 4, 2) + [{"p": (-4.0, -W / 2 - 1.0, 4.6), "kind": "amber"}]
    ctx.finish(name, "07", B, doors, lights, {"footprint": [L, W, H]})


def gate(ctx):
    name, L, W, H = "MainGate", 29.0, 14.0, 18.0
    K.reset()
    B = Builder(name, 1)
    t = 1.0
    P = 9.0
    TW = (L - P) / 2
    for sgn in (-1, 1):
        B.off = Vector((sgn * (P / 2 + TW / 2), 0, 0))
        B.box((0, 0, -0.15), (TW, W, 0.3), "Concrete_Weathered", inward=Z, mat_in="Interior_Concrete", hull=True)
        B.box((0, 0, -0.2), (TW + 0.3, W + 0.3, 0.7), "Armor_Paint")
        inner = "left" if sgn > 0 else "right"
        wall(B, TW, W, H, t, "front", [], skirt=False)
        wall(B, TW, W, H, t, "back", [(0.0, 1.8, 2.8, 0.0)])
        wall(B, TW, W, H, t, "left", [], skirt=(inner != "left"))
        wall(B, TW, W, H, t, "right", [], skirt=(inner != "right"))
        door_frame(B, TW, W, H, "back", 0.0, 1.8, 2.8)
        buttresses(B, TW, W, H, "front", [sgn * 3.0], width=1.0, depth=1.0)
        buttresses(B, TW, W, H, "back", [-3.0, 3.0], width=1.0, depth=1.0)
        windows(B, TW, W, H, "front", [0.0], 11.4, w=2.8, h=1.6)
        windows(B, TW, W, H, "back", [0.0], 11.4, w=2.8, h=1.6)
        pipe_run(B, TW, W, "back", -3.5, 3.5, 6.0, count=3)
        top = roof(B, TW, W, H)
        B.box((0, 0, top + 1.3), (TW - 2.2, W - 3.8, 2.6), "Armor_Paint", hull=True)
        for s_ in (-1, 1):
            B.box((s_ * ((TW - 2.2) / 2 + 0.03), 0, top + 1.45), (0.06, W - 4.6, 1.3), "Window_Glass")
            B.box((0, s_ * ((W - 3.8) / 2 + 0.03), top + 1.45), (TW - 3.0, 0.06, 1.3), "Window_Glass")
        B.box((0, 0, top + 2.8), (TW - 1.4, W - 3.0, 0.3), "Concrete_Weathered")
        mast(B, 1.5 * sgn, 3, top + 2.9, 6.0)
        B.cyl((0, -W / 2 + 1.0, top + 3.3), 0.4, 0.8, "Light_Strip", seg=10)
        vent_tower(B, -1.5 * sgn, 4.5, top, 2.2, 2.0, 2.4)
        for k in range(3):
            B.box((-1.8 + k * 1.8, 4.8, 1.0), (1.2, 0.6, 2.0), "Armor_Paint")
        B.box((0, -3.0, 0.45), (3.0, 1.2, 0.9), "Door_Metal")
        lights_strip_row(B, TW, W, H, [0], [-3.5, 2.5])
    B.off = Vector((0, 0, 0))
    dz = 10.0
    B.box((0, 0, dz), (P, W, 1.0), "Concrete_Weathered", hull=True)
    B.box((0, 0, dz - 0.65), (P, W - 0.4, 0.3), "Armor_Paint")
    for sy in (-1, 1):
        B.box((0, sy * (W / 2 - 0.2), dz + 0.5 + 0.7), (P, 0.45, 1.4), "Armor_Paint")
    B.box((0, -W / 2 - 0.15, dz - 0.1), (P + 0.2, 0.35, 1.5), "Armor_Paint")
    B.box((0, -W / 2 - 0.34, dz - 0.1), (P - 0.6, 0.04, 0.6), "Hazard_Stripes")
    B.box((0, -W / 2 - 0.15, 0.25), (P, 0.35, 0.5), "Hazard_Stripes")
    for sgn in (-1, 1):
        digits(B, L, W, "front", "01", sgn * (P / 2 + TW / 2), 14.6, h=2.4)
        chevron(B, L, W, "front", sgn * (P / 2 + TW / 2), 12.7, w=2.6, count=2)
    bollards(B, L, W, "front", [-7.5, -3, 3, 7.5], offset=2.4)
    for sgn in (-1, 1):
        B.box((sgn * (P / 2 + 0.06), -W / 2 + 0.4, 7.4), (0.06, 0.12, 1.0), "Light_Strip")
    GH = 9.2
    doors = [slide_door("GateL", L, W, "front", 0.0, P, GH, dirsign=-1, leaf_w=P / 2 + 0.3, cu=-P / 4 - 0.15, seconds=2.0),
             slide_door("GateR", L, W, "front", 0.0, P, GH, dirsign=1, leaf_w=P / 2 + 0.3, cu=P / 4 + 0.15, seconds=2.0),
             hinge_door("TowerWHatch", TW, W, "back", 0.0, 1.8, 2.8, "left", off=(-(P / 2 + TW / 2), 0, 0)),
             hinge_door("TowerEHatch", TW, W, "back", 0.0, 1.8, 2.8, "left", off=((P / 2 + TW / 2), 0, 0))]
    for d in doors[:2]:
        d.vols["sensor_h"] = (6.0, 5.0, 4.5)
        d.vols["sensor_c"] = (0.0, -W / 2 - 5.4, 3.5)
        d.vols["blocker_h"] = (P / 4 - 0.1, 0.4, GH / 2)
    doors[0].vols["blocker_c"] = (-P / 4, -W / 2 + 0.2, GH / 2)
    doors[1].vols["blocker_c"] = (P / 4, -W / 2 + 0.2, GH / 2)
    lights = [{"p": (-(P / 2 + TW / 2), 0.0, 8.0), "kind": "amber"}, {"p": (P / 2 + TW / 2, 0.0, 8.0), "kind": "amber"},
              {"p": (0.0, 0.0, 8.0), "kind": "white"}, {"p": (-(P / 2 + TW / 2), -W / 2 - 1.0, 9.0), "kind": "blue"},
              {"p": (P / 2 + TW / 2, -W / 2 - 1.0, 9.0), "kind": "blue"}]
    ctx.finish(name, "01", B, doors, lights, {"footprint": [L, W, H], "passage_width": P})
