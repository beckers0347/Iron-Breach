import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector
import kit
from kit import box, hull, cylinder, quad, cut, uv_box, set_pivot, join
import kit2
from kit2 import Ctx, prism, strut, cyl_axis, blast_leaf, finish, tower

NAME = "SM_GateCheckpoint"
TX = 12.5  # tower centre x


def build(M):
    c = Ctx(NAME); c.M = M; P = c.P
    slab = box("slab", (-34, -10, -0.3), (34, 10, 0), M["floor"], bev=0.03); uv_box(slab); P(slab)
    road = box("road", (-5.5, -10, 0), (5.5, 10, 0.03), M["concrete_dk"]); uv_box(road); P(road)
    for sx in (-1, 1):
        ln = box("ln", (sx * 5.3 - 0.08, -9.5, 0.03), (sx * 5.3 + 0.08, 9.5, 0.04), M["line"]); P(ln)
    for k in range(10):
        dl = box("dl", (-0.08, -9 + k * 2, 0.03), (0.08, -8.0 + k * 2, 0.04), M["yellow"]); P(dl)
    c.uc((-34, -10, -0.3), (34, 10, 0))
    # ---- portal ----
    for s in (-1, 1):
        a, b = sorted((s * 5.5, s * 7.5))
        post = box("post", (a, -1.1, 0), (b, 1.1, 8.6), M["steel_dk"], bev=0.05); uv_box(post); P(post)
        # inner panels + V braces on road-facing side
        ix = s * 5.5
        for z0, z1 in ((0.4, 4.0), (4.2, 8.0)):
            br = strut("br", (ix - s * 0.05, -0.6, z0), (ix - s * 0.05, 0.0, z1), 0.05, M["steel"]); P(br)
            br = strut("br", (ix - s * 0.05, 0.6, z0), (ix - s * 0.05, 0.0, z1), 0.05, M["steel"]); P(br)
        hz = box("hz", (a - 0.02, -1.12, 0.1), (b + 0.02, 1.12, 0.9), M["hazard"]); uv_box(hz); P(hz)
        c.uc((a, -1.1, 0), (b, 1.1, 8.6))
        bl = box("bl", (s * 5.3 - .15, -1.0, 8.3), (s * 5.3 + .15, -0.7, 8.5), M["blue"]); P(bl)
        c.lights.append(("blue", (s * 5.3, -1.1, 8.4)))
    beam = box("beam", (-8.0, -1.3, 8.3), (8.0, 1.3, 11.3), M["steel_dk"], bev=0.06); uv_box(beam); P(beam)
    for s in (-1, 1):
        for (xa, xb) in ((0.6, 3.6), (4.0, 7.2)):
            a, b = sorted((s * xa, s * xb))
            pn = box("pn", (a, -1.36, 9.0), (b, -1.3, 10.6), M["steel"]); uv_box(pn); P(pn)
        for xx in (s * 2.2, s * 5.6):
            lp = box("tl", (xx - .2, -0.3, 11.3), (xx + .2, 0.3, 11.5), M["blue"]); P(lp)
            c.lights.append(("blue", (xx, 0, 11.6)))
    c.uc((-8.0, -1.3, 8.3), (8.0, 1.3, 11.3))
    # ---- towers ----
    for s, n in ((-1, "W"), (1, "E")):
        tower(c, s * TX, 0.0, 6.0, 10.0, f"{NAME}_Tower{n}_")
    # ---- perimeter wall segments ----
    for s in (-1, 1):
        for (xa, xb) in ((15.8, 24.0), (24.0, 32.0)):
            a, b = sorted((s * xa, s * xb))
            wl = box("wall", (a, -0.4, 0), (b, 0.4, 5.4), M["concrete"], bev=0.04); uv_box(wl); P(wl)
            cp = box("cap", (a, -0.55, 5.4), (b, 0.55, 5.65), M["concrete_dk"], bev=0.03); uv_box(cp); P(cp)
            # panel plates with X bracing
            n_ = int(abs(xb - xa) // 4)
            for k in range(n_):
                x0 = a + k * 4.0 + 0.3; x1 = x0 + 3.4
                for yy in (-0.43, 0.43):
                    pl = box("pl", (x0, yy - 0.03 if yy < 0 else yy - 0.0, 0.5), (x1, yy if yy < 0 else yy + 0.03, 5.0), M["steel_dk"]); uv_box(pl); P(pl)
                    st1 = strut("x", (x0, yy * 1.2, 0.6), (x1, yy * 1.2, 4.9), 0.04, M["steel"]); P(st1)
                    st2 = strut("x", (x0, yy * 1.2, 4.9), (x1, yy * 1.2, 0.6), 0.04, M["steel"]); P(st2)
            c.uc((a, -0.4, 0), (b, 0.4, 5.65))
        for xx in (s * 16.4, s * 24.0, s * 31.6):
            pi = box("pil", (xx - 0.4, -0.7, 0), (xx + 0.4, 0.7, 6.0), M["concrete_dk"], bev=0.04); uv_box(pi); P(pi)
    # ---- bollards ----
    for k in range(7):
        for sx in (-1, 1):
            y = -9.0 + k * 1.1
            bo = cylinder("bol", (sx * 6.0, y, 0.55), 0.12, 1.1, M["yellow"]); P(bo)
            c.uc((sx * 6.0 - .12, y - .12, 0), (sx * 6.0 + .12, y + .12, 1.1))
    # ---- boom barrier (animated) ----
    bp = box("bpost", (-6.3, -5.4, 0), (-5.5, -4.6, 1.1), M["steel_dk"], bev=0.03); uv_box(bp); P(bp)
    c.uc((-6.3, -5.4, 0), (-5.5, -4.6, 1.1))
    rest = box("brest", (5.0, -5.2, 0), (5.5, -4.8, 0.9), M["steel_dk"]); uv_box(rest); P(rest)
    arm = []
    for k in range(10):
        a = -5.4 + k * 1.08
        arm.append(box("arm", (a, -5.1, 1.0), (a + 1.08, -4.9, 1.2), M["hazard"] if k % 2 == 0 else M["line"]))
    for o in arm:
        uv_box(o)
    c.add_door("BoomBarrier", arm, (-5.4, -5.0, 1.1), "hinge", (0, 1, 0), -90.0)
    # signs / lamps on portal
    sg = box("sign", (-3.0, -1.4, 8.6), (3.0, -1.3, 9.0), M["amber"]); P(sg)
    c.lights.append(("amber", (0, -1.6, 8.8)))
    return c


def main(outdir):
    kit.reset()
    M = kit.std_materials()
    c = build(M)
    cams = [dict(name="front", loc=(-40, -38, 24), target=(0, 0, 6), lens=32, frame=1),
            dict(name="gate_open", loc=(-4, -24, 3.2), target=(0, 0, 4), lens=28, frame=40),
            dict(name="tower_int", loc=(-12.5, -1.0, 1.5), target=(-12.5, 1.0, 7.0), lens=22, frame=1,
                 pls=[(-12.5, 0, 2.5, 800), (-12.5, 0, 6.0, 800), (-12.5, 0, 9.0, 800)]),
            dict(name="cabin_int", loc=(-12.5, -1.5, 11.6), target=(-12.5, 3.0, 11.8), lens=22, frame=1,
                 pls=[(-12.5, 0, 13.0, 600)])]
    finish(c, outdir, cams)


if __name__ == "__main__":
    main(sys.argv[1])
