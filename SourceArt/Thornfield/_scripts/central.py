import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector, noise
import kit
from kit import box, hull, cylinder, quad, cut, uv_box, set_pivot, join
import kit2
from kit2 import Ctx, prism, strut, cyl_axis, blast_leaf, finish

NAME = "SM_CentralBunker"
Y0, Y1 = -12.0, 12.0
OPENS = [(-15.0, 3.0, 4.6), (0.0, 3.5, 5.0), (15.0, 3.0, 4.6)]  # (cx, half width, height)


def build(M):
    c = Ctx(NAME); c.M = M; P = c.P
    random.seed(5)
    scr = kit.flat_mat("M_Screen", (0.1, 0.3, 0.5), 0.3, 0, (0.2, 0.55, 1.0), 4)
    slab = box("slab", (-30, -22, -0.3), (30, 16, 0), M["floor"], bev=0.03); uv_box(slab); P(slab)
    prof = [(-23, 0), (23, 0), (23, 5.0), (16, 8.0), (-16, 8.0), (-23, 5.0)]
    h = prism("hull", prof, Y0, Y1, M["steel_dk"], bev=0.05)
    vprof = [(-22.3, -0.1), (22.3, -0.1), (22.3, 4.6), (15.7, 7.3), (-15.7, 7.3), (-22.3, 4.6)]
    void = prism("void", vprof, Y0 + 0.7, Y1 - 0.7)
    cutters = [void]
    for cx, hw, ht in OPENS:
        cutters.append(box("fo", (cx - hw, Y0 - 1, -0.1), (cx + hw, Y0 + 1.5, ht)))
    cutters.append(box("ro", (-1.0, Y1 - 1.5, -0.1), (1.0, Y1 + 1, 2.6)))
    cut(h, *cutters)
    h.data.materials.clear(); h.data.materials.append(M["steel_dk"]); h.data.materials.append(M["moss"])
    for p in h.data.polygons:
        p.material_index = 1 if (p.normal.z > 0.3 and p.center.z > 4.6) else 0
    uv_box(h); P(h)
    # barrel vault on top
    pts = []
    for i in range(0, 13):
        a = math.pi * i / 12
        x, z = 9.0 * math.cos(a), 8.0 + 1.9 * math.sin(a)
        pts += [(x, -9.5, z), (x, 9.5, z)]
    pts += [(-9, -9.5, 7.9), (9, -9.5, 7.9), (-9, 9.5, 7.9), (9, 9.5, 7.9)]
    vault = hull("vault", pts, M["moss"]); kit.smooth(vault, 50); uv_box(vault); P(vault)
    # ribs on vault
    for yc in (-8, -4, 0, 4, 8):
        rb = hull("vr", [(x, yc + dy, z) for (x, z) in [(-9.05 * math.cos(math.pi * i / 12), 8 + 1.95 * math.sin(math.pi * i / 12)) for i in range(13)]
                          for dy in (-0.12, 0.12)], M["concrete_dk"]); P(rb)
    # roof ribs on slopes
    for s in (-1, 1):
        for yc in range(-10, 11, 2):
            rr = hull("rr", [(s * 16, yc - .07, 8.0), (s * 23, yc - .07, 5.0), (s * 16 + 0.0, yc - .07, 8.18), (s * 23 + s * 0.08, yc - .07, 5.18),
                             (s * 16, yc + .07, 8.0), (s * 23, yc + .07, 5.0), (s * 16, yc + .07, 8.18), (s * 23 + s * .08, yc + .07, 5.18)], M["concrete_dk"]); P(rr)
    # roof equipment on vault & slopes
    eq = [(-4.5, -5, 1.6, 1.4, 1.3, 9.55), (3.0, -4, 1.8, 1.3, 1.2, 9.6), (-1.0, 3, 1.4, 1.2, 1.4, 9.8), (5.0, 5, 1.6, 1.4, 1.0, 9.0),
          (-6.0, 4, 1.2, 1.2, 1.2, 8.9), (-19, -6, 1.6, 1.4, 1.3, 6.0), (19, 5, 1.6, 1.4, 1.3, 6.0)]
    for i, (x, y, sx, sy, sz, zb) in enumerate(eq):
        b = box(f"eq{i}", (x - sx / 2, y - sy / 2, zb - 0.2), (x + sx / 2, y + sy / 2, zb + sz), M["olive"], bev=0.03); uv_box(b); P(b)
        for k in range(4):
            lv = box("lv", (x - sx / 2 + .12, y - sy / 2 - .03, zb + .15 + k * (sz - .4) / 4), (x + sx / 2 - .12, y - sy / 2, zb + .21 + k * (sz - .4) / 4), M["concrete_dk"]); P(lv)
    for i, (x, y) in enumerate(((-7.5, -7), (7.5, 1), (-12, 6))):
        st = cylinder(f"stack{i}", (x, y, 9.4), 0.25, 2.0, M["steel"]); P(st)
    ant = cylinder("ant", (8.5, -8, 12), 0.05, 5.0, M["steel"]); P(ant)
    # ---- front facade: piers, frames, headers ----
    for cx, hw, ht in OPENS:
        for s in (-1, 1):
            a, b = sorted((cx + s * hw, cx + s * (hw + 0.7)))
            j = box("jamb", (a, Y0 - 0.55, 0), (b, Y0, ht + 0.8), M["concrete_dk"], bev=0.04); uv_box(j); P(j)
        hd = box("hd", (cx - hw - 0.7, Y0 - 0.55, ht), (cx + hw + 0.7, Y0, ht + 0.8), M["concrete_dk"], bev=0.04); uv_box(hd); P(hd)
        trk = box("trk", (cx - hw - 3.4, Y0 - 1.0, ht - 0.1), (cx + hw + 3.4, Y0 - 0.55, ht + 0.1), M["steel"]); uv_box(trk); P(trk)
        for s in (-1, 1):
            a, b = sorted((cx + s * 0.3, cx + s * (hw + 0.4)))
            st = box("st", (a, Y0 - 0.58, ht + 0.3), (b, Y0 - 0.55, ht + 0.45), M["amber"]); P(st)
        c.lights.append(("amber", (cx, Y0 - 0.8, ht + 0.4)))
    for s in (-1, 1):  # corner piers w/ banners + blue lights
        pb = box("cp", (s * 22.0 - 0.9, Y0 - 0.7, 0), (s * 22.0 + 0.9, Y0 + 0.2, 5.4), M["concrete"], bev=0.06); uv_box(pb); P(pb)
        bl = box("bl", (s * 20.6 - .1, Y0 - 0.65, 2.4), (s * 20.6 + .1, Y0 - 0.5, 2.6), M["blue"]); P(bl)
        c.lights.append(("blue", (s * 20.6, Y0 - 0.8, 2.5)))
        for q in kit2.banner_obj(s * 22.0 - 0.6, s * 22.0 + 0.6, 1.0, 4.6, Y0 - 0.74, M, "banner"):
            P(q)
    # mid pilasters on front between openings
    for x in (-9.0, -6.0, 6.0, 9.0):
        pl = box("pil", (x - 0.35, Y0 - 0.45, 0), (x + 0.35, Y0, 5.6 if abs(x) < 7 else 6.0), M["concrete_dk"], bev=0.03); uv_box(pl); P(pl)
    hz = box("hzf", (-3.4, Y0 - 1.9, 0), (3.4, Y0 - 1.5, 0.02), M["hazard"]); uv_box(hz); P(hz)
    # side stair + retaining wall (exterior dressing, west side)
    rw = hull("rwall", [(-27, -9, 0), (-24, -9, 0), (-27, 9, 0), (-24, 9, 0), (-27, -9, 3.4), (-24.4, -9, 3.4), (-27, 9, 3.4), (-24.4, 9, 3.4)], M["concrete"], bev=0.04); uv_box(rw); P(rw)
    for i in range(17):
        z = 0.2 * (i + 1)
        stp = box("stp", (-24.0, -10.5 + i * 0.5, 0), (-22.9, -10.0 + i * 0.5, z), M["concrete"]); uv_box(stp); P(stp)
    c.uc((-27, -9, 0), (-24, 9, 3.4))
    for i in range(17):
        c.uc((-24.0, -10.5 + i * 0.5, 0), (-22.9, -10.0 + i * 0.5, 0.2 * (i + 1)))
    # ---- partitions with doorways ----
    for s in (-1, 1):
        a, b = sorted((s * 7.85, s * 8.15))
        p1 = box("pt", (a, Y0 + 0.65, 0), (b, -1.2, 7.4), M["concrete"], bev=0.01); uv_box(p1); P(p1)
        p2 = box("pt", (a, 1.2, 0), (b, Y1 - 0.65, 7.4), M["concrete"], bev=0.01); uv_box(p2); P(p2)
        p3 = box("pt", (a, -1.2, 2.7), (b, 1.2, 7.4), M["concrete"], bev=0.01); uv_box(p3); P(p3)
        for yy in (-1.3, 1.2):
            fr = box("fr", (a - .05, yy, 0), (b + .05, yy + .1, 2.7), M["steel"]); uv_box(fr); P(fr)
        c.uc((a, Y0 + 0.65, 0), (b, -1.2, 7.4)); c.uc((a, 1.2, 0), (b, Y1 - 0.65, 7.4)); c.uc((a, -1.2, 2.7), (b, 1.2, 7.4))
    for s, sn in ((-1, "W"), (1, "E")):
        pass
    # remove helper leaves built above (we build real ones below)
    # ---- ceiling lights / ribs ----
    for xc in (-15, 0, 15):
        for yc in (-8, -3, 3, 8):
            zl = 7.0 if xc == 0 else (6.7 if abs(xc) == 15 else 7.0)
            lt = box("lt", (xc - 1.0, yc - .12, zl - 0.08), (xc + 1.0, yc + .12, zl), M["white"]); P(lt)
            c.lights.append(("white", (xc, yc, zl - 0.2)))
    # ---- interior props: command room (center) ----
    tb = box("holo", (-2.5, -1.2, 0.0), (2.5, 1.2, 0.95), M["steel_dk"], bev=0.03); uv_box(tb); P(tb)
    tt = box("holot", (-2.3, -1.0, 0.95), (2.3, 1.0, 1.02), scr); P(tt)
    for k in range(6):  # consoles along back wall
        x = -6.0 + k * 2.4
        cs = box("cons", (x - 0.9, 9.9, 0), (x + 0.9, 11.0, 1.0), M["olive"], bev=0.02); uv_box(cs); P(cs)
        sc = box("scr", (x - 0.8, 10.8, 1.0), (x + 0.8, 10.9, 2.0), scr); P(sc)
        ch = box("chair", (x - 0.3, 8.8, 0.0), (x + 0.3, 9.4, 0.5), M["fabric"]); P(ch)
    for k in range(4):  # wall screens on east/west walls of center
        for s in (-1, 1):
            sc = box("ws", (s * 7.8 - (0.1 if s > 0 else -0.0), -9.0 + k * 3.0 - 0.0, 1.3), (s * 7.8 + (0.0 if s > 0 else 0.1), -8.0 + k * 3.0, 2.3), scr) if False else None
    # server racks in west room
    for r in range(2):
        for k in range(8):
            y = -9.5 + k * 2.4
            x = -20.5 + r * 5.5
            rk = box("rack", (x - 0.45, y - 0.5, 0), (x + 0.45, y + 0.5, 2.2), M["olive"], bev=0.01, seg=1); uv_box(rk); P(rk)
            led = box("led", (x - 0.4, y - 0.52, 1.6), (x + 0.4, y - 0.5, 1.7), M["blue"]); P(led)
            c.uc((x - .45, y - .5, 0), (x + .45, y + .5, 2.2)) if False else None
    # briefing table east room
    bt = box("btab", (11.5, -3.5, 0.72), (13.5, 3.5, 0.8), M["olive"]); uv_box(bt); P(bt)
    for ly in (-3.2, 3.2):
        for lx in (11.7, 13.3):
            lg = box("lg", (lx - .05, ly - .05, 0), (lx + .05, ly + .05, .72), M["steel"]); P(lg)
    for k in range(6):
        for sx in (10.7, 14.3):
            chn = box("chn", (sx - .25, -3.0 + k * 1.2 - .25, 0), (sx + .25, -3.0 + k * 1.2 + .25, .5), M["fabric"]); P(chn)
    c.uc((-2.5, -1.2, 0), (2.5, 1.2, 1.02))
    c.uc((-7.0, 9.9, 0), (4.0, 11.0, 2.0))
    c.uc((11.5, -3.5, 0), (13.5, 3.5, 0.8))
    for r in range(2):
        c.uc((-20.95 + r * 5.5, -10.0, 0), (-20.05 + r * 5.5, 9.0, 2.2))
    # ---- doors ----
    for cx, hw, ht in OPENS:
        n = "C" if cx == 0 else ("W" if cx < 0 else "E")
        for s, sn in ((-1, "L"), (1, "R")):
            xa, xb = (cx - hw - 0.1, cx - 0.02) if s < 0 else (cx + 0.02, cx + hw + 0.1)
            objs = blast_leaf("leaf", xa, xb, 0.05, ht, Y0 - 1.45, Y0 - 1.25, M, side=s)
            xc = (xa + xb) / 2
            c.add_door(f"Front{n}_Door{sn}", objs, (xc, Y0 - 1.35, 0), "slide", (1, 0, 0), s * (hw + 0.1) * 1.0)
    for s, sn in ((-1, "W"), (1, "E")):
        # hinge at y=-1.15 on partition; leaf spans +y
        lf = [box("lf", (s * 7.95 - 0.04, -1.1, 0.03), (s * 7.95 + 0.04, 1.1, 2.65), M["steel"], bev=0.01, seg=1),
              box("hd", (s * 7.95 - 0.1, 0.7, 1.0), (s * 7.95 + 0.1, 0.9, 1.2), M["steel"])]
        for q in lf:
            uv_box(q)
        c.add_door(f"Inner{sn}Door", lf, (s * 7.95, -1.15, 0), "hinge", (0, 0, 1), 95.0 * s * -1 * -1)
    rd = [box("rd", (-1.05, Y1 - 0.95, 0.03), (1.05, Y1 - 0.85, 2.55), M["steel"], bev=0.01, seg=1),
          box("rdh", (0.6, Y1 - 1.0, 1.0), (0.8, Y1 - 0.95, 1.2), M["steel"])]
    for q in rd:
        uv_box(q)
    c.add_door("RearDoor", rd, (-1.05, Y1 - 0.9, 0), "hinge", (0, 0, 1), -95.0)
    # ---- collision ----
    c.uc((-30, -22, -0.3), (30, 16, 0))
    c.uc((-23, Y0, 0), (-22.3, Y1, 5.0)); c.uc((22.3, Y0, 0), (23, Y1, 5.0))
    segs = [(-23, -18), (-12, -3.5), (3.5, 12), (18, 23)]
    for a, b in segs:
        c.uc((a, Y0, 0), (b, Y0 + 0.7, 8.0 if abs(a) < 13 else 5.0))
    for cx, hw, ht in OPENS:
        c.uc((cx - hw, Y0, ht), (cx + hw, Y0 + 0.7, 8.0))
    c.uc((-22.3, Y1 - 0.7, 0), (-1.0, Y1, 5.0)); c.uc((1.0, Y1 - 0.7, 0), (22.3, Y1, 5.0)); c.uc((-1.0, Y1 - 0.7, 2.6), (1.0, Y1, 5.0))
    c.uc((-15.7, Y1 - 0.7, 5.0), (15.7, Y1, 8.0))
    c.uc((-15.7, Y0, 7.3), (15.7, Y1, 9.9))
    c.uc((-23, Y0, 4.6), (-15.7, Y1, 5.2)); c.uc((15.7, Y0, 4.6), (23, Y1, 5.2))
    return c


def main(outdir):
    kit.reset()
    M = kit.std_materials()
    c = build(M)
    cams = [dict(name="front", loc=(-65, -70, 34), target=(0, 0, 3), lens=34, frame=1),
            dict(name="front_open", loc=(-28, -40, 4.5), target=(0, -12, 3), lens=28, frame=40),
            dict(name="interior", loc=(0, -9.5, 1.7), target=(0, 8, 1.8), lens=19, frame=40,
                 pls=[(0, -6, 6.8, 2500), (0, 2, 6.8, 2500), (0, 8, 6.8, 2500), (-10, 0, 5, 1500), (10, 0, 5, 1500)])]
    finish(c, outdir, cams)


if __name__ == "__main__":
    main(sys.argv[1])
