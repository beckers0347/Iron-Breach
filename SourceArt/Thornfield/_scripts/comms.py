import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
import kit
from kit import box, cylinder, uv_box, hull, cut
import kit2
from kit2 import Ctx, finish, strut, cyl_axis

NAME = "SM_CommsTower"
MAST_H = 40.0


def hw_at(z):  # mast half-width
    t = (z - 4.0) / (MAST_H - 4.0)
    return 1.6 - 1.0 * t


def build(M):
    c = Ctx(NAME); c.M = M; P = c.P
    red = kit.flat_mat("M_LightRed", (1, .1, .1), 0.4, 0, (1, .1, .1), 12)
    slab = box("slab", (-9, -9, -0.3), (9, 9, 0), M["floor"], bev=0.03); uv_box(slab); P(slab)
    c.uc((-9, -9, -0.3), (9, 9, 0))
    # building 8x8x4 hollow
    h = box("bld", (-4, -4, 0), (4, 4, 4.0), M["concrete"], bev=0.05)
    cut(h, box("v", (-3.6, -3.6, -0.1), (3.6, 3.6, 3.6)), box("dc", (-0.7, -5, -0.1), (0.7, -3.0, 2.4)))
    uv_box(h); P(h)
    par = box("par", (-4.15, -4.15, 4.0), (4.15, 4.15, 4.4), M["concrete_dk"], bev=0.03)
    cut(par, box("v", (-3.7, -3.7, 3.9), (3.7, 3.7, 4.5))); uv_box(par); P(par)
    for s in (-1, 1):
        a, b = sorted((s * 0.7, s * 0.85))
        fr = box("df", (a, -4.05, 0), (b, -3.5, 2.4), M["steel"]); uv_box(fr); P(fr)
    fh = box("dfh", (-0.85, -4.05, 2.4), (0.85, -3.5, 2.55), M["steel"]); uv_box(fh); P(fh)
    lf = [box("lf", (-0.68, -3.85, 0.03), (0.68, -3.75, 2.37), M["steel"], bev=0.01, seg=1),
          box("hd", (0.35, -3.9, 1.0), (0.55, -3.85, 1.2), M["steel"])]
    for q in lf:
        uv_box(q)
    c.add_door("Door", lf, (-0.68, -3.8, 0), "hinge", (0, 0, 1), 95.0)
    hz = box("hz", (-4.02, -4.02, 0.1), (4.02, -3.98, 0.5), M["hazard"]); uv_box(hz); P(hz)
    # wall collision
    c.uc((-4, -4, 0), (-3.6, 4, 4.0)); c.uc((3.6, -4, 0), (4, 4, 4.0)); c.uc((-4, 3.6, 0), (4, 4, 4.0))
    c.uc((-4, -4, 0), (-0.7, -3.6, 4.0)); c.uc((0.7, -4, 0), (4, -3.6, 4.0)); c.uc((-0.7, -4, 2.4), (0.7, -3.6, 4.0))
    c.uc((-4, -4, 3.6), (4, 4, 4.4))
    # interior: racks, desk, lamps
    for r in range(4):
        x = -2.7 + r * 1.8
        rk = box("rack", (x - .45, 2.4, 0), (x + .45, 3.5, 2.2), M["olive"], bev=0.01, seg=1); uv_box(rk); P(rk)
        led = box("led", (x - .4, 2.38, 1.7), (x + .4, 2.4, 1.8), M["blue"]); P(led)
        c.uc((x - .45, 2.4, 0), (x + .45, 3.5, 2.2))
    dk = box("desk", (-3.4, -2.5, 0.72), (-1.4, -1.5, 0.8), M["olive"]); uv_box(dk); P(dk)
    for lx in (-3.3, -1.5):
        for ly in (-2.4, -1.6):
            lg = box("lg", (lx - .04, ly - .04, 0), (lx + .04, ly + .04, .72), M["steel"]); P(lg)
    sc = box("scr", (-3.0, -1.55, 0.8), (-1.8, -1.5, 1.4), M["screen"]); P(sc)
    c.uc((-3.4, -2.5, 0), (-1.4, -1.5, 0.8))
    for xc in (-2, 2):
        lt = box("lt", (xc - 0.6, -0.1, 3.5), (xc + 0.6, 0.1, 3.6), M["white"]); P(lt)
        c.lights.append(("white", (xc, 0, 3.4)))
    # roof hatch + cable tray
    # ---- lattice mast ----
    zs = [4.0 + i * 4.0 for i in range(10)] + [MAST_H]
    for i in range(len(zs) - 1):
        z0, z1 = zs[i], zs[i + 1]
        a0, a1 = hw_at(z0), hw_at(z1)
        cs0 = [(-a0, -a0), (a0, -a0), (a0, a0), (-a0, a0)]
        cs1 = [(-a1, -a1), (a1, -a1), (a1, a1), (-a1, a1)]
        for k in range(4):
            P(strut("leg", (*cs0[k], z0), (*cs1[k], z1), 0.09, M["steel"]))
            k2 = (k + 1) % 4
            P(strut("ring", (*cs1[k], z1), (*cs1[k2], z1), 0.05, M["steel"]))
            P(strut("dx", (*cs0[k], z0), (*cs1[k2], z1), 0.04, M["steel"]))
            P(strut("dx", (*cs0[k2], z0), (*cs1[k], z1), 0.04, M["steel"]))
    for k, (sx, sy) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1))):
        pts = []
        for z, a in ((4.0, 1.6), (MAST_H, 0.6)):
            for d in (-0.12, 0.12):
                pts += [(sx * a + d, sy * a + d, z), (sx * a - d, sy * a + d, z)]
        c.uc_hull(pts)
    # platform at 28 m
    zp = 28.0; a = hw_at(zp) + 0.5
    pf = box("platform", (-a, -a, zp), (a, a, zp + 0.1), M["steel"]); uv_box(pf); P(pf)
    for s in (-1, 1):
        for q in range(-2, 3):
            P(box("po", (s * a - .02, q * a / 2.2 - .02, zp), (s * a + .02, q * a / 2.2 + .02, zp + 1.0), M["steel"]))
            P(box("po", (q * a / 2.2 - .02, s * a - .02, zp), (q * a / 2.2 + .02, s * a + .02, zp + 1.0), M["steel"]))
        P(box("rl", (s * a - .02, -a, zp + .95), (s * a + .02, a, zp + 1.0), M["steel"]))
        P(box("rl", (-a, s * a - .02, zp + .95), (a, s * a + .02, zp + 1.0), M["steel"]))
    # dishes and panels
    for (z, ang, r) in ((24.0, 0.0, 0.9), (30.0, 140.0, 0.7), (34.0, 250.0, 0.6)):
        ar = math.radians(ang)
        cx, cy = math.cos(ar) * (hw_at(z) + 0.7), math.sin(ar) * (hw_at(z) + 0.7)
        d = cyl_axis("dish", (cx, cy, z), r, 0.12, "x" if abs(math.cos(ar)) > 0.7 else "y", M["concrete"], seg=20); P(d)
        P(box("feed", (cx - .05, cy - .05, z - .05), (cx + .05, cy + .05, z + .4), M["steel"]))
    for z in (36.0, 38.0):
        for sx, sy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            p = box("pan", (sx * 1.0 - (0.15 if sx == 0 else 0.05), sy * 1.0 - (0.15 if sy == 0 else 0.05), z), (sx * 1.0 + (0.15 if sx == 0 else 0.05), sy * 1.0 + (0.15 if sy == 0 else 0.05), z + 1.6), M["olive"]); uv_box(p); P(p)
    spike = cylinder("spike", (0, 0, MAST_H + 2.5), 0.05, 5.0, M["steel"]); P(spike)
    for z in (MAST_H + 5.0, 20.0):
        bc = cylinder("bcn", (0, 0, z + 0.15), 0.18, 0.3, red) if z > 30 else None
        if bc: P(bc)
    for k, (sx, sy) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1))):
        bc = box("bcn", (sx * hw_at(20.0) - .12, sy * hw_at(20.0) - .12, 20.0), (sx * hw_at(20.0) + .12, sy * hw_at(20.0) + .12, 20.3), red); P(bc)
    c.lights.append(("red", (0, 0, MAST_H + 5.3)))
    c.lights.append(("red", (0, 0, 20.3)))
    # ground cabinets
    for i, x in enumerate((5.5, 6.7)):
        cb = box("cab", (x - .5, -3, 0), (x + .5, -1.8, 1.8), M["olive"], bev=0.02); uv_box(cb); P(cb)
        c.uc((x - .5, -3, 0), (x + .5, -1.8, 1.8))
    gen = box("gen", (5.0, 1.5, 0), (7.4, 3.5, 1.6), M["olive"], bev=0.03); uv_box(gen); P(gen); c.uc((5.0, 1.5, 0), (7.4, 3.5, 1.6))
    return c


def main(outdir):
    kit.reset()
    M = kit.std_materials()
    c = build(M)
    cams = [dict(name="front", loc=(-40, -55, 26), target=(0, 0, 19), lens=40, frame=1),
            dict(name="base", loc=(-14, -16, 5), target=(0, 0, 4), lens=32, frame=40),
            dict(name="interior", loc=(0, -2.8, 1.6), target=(0, 3, 1.5), lens=20, frame=40, pls=[(0, 0, 3.3, 300)])]
    finish(c, outdir, cams)


if __name__ == "__main__":
    main(sys.argv[1])
