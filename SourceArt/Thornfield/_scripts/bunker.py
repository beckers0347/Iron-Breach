import sys, os, math, json, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector, noise
import kit
from kit import box, hull, cylinder, quad, cut, uv_box, set_pivot, join, finalize_static, bevel

NAME = "SM_BermBunker"
W, D, H = 22.0, 18.0, 7.0   # footprint half = 11 / 9
HALL_H = 4.0
SEED = 7


def xb(z):  # battered half width at height z
    return 11.0 - 2.2 * z / 7.0


def yb_back(z):
    return 9.0 - 1.0 * z / 7.0


def mound_z(x, y):
    t = 1 - (x / 9.8) ** 2 - ((y - 1.4) / 7.6) ** 2
    return 6.6 + 1.6 * math.sqrt(max(0.0, t))


def build(M):
    random.seed(SEED)
    parts = []   # static pieces
    P = parts.append
    doors = {}
    ucx = []
    lights = []

    # ---- apron / floor slab ----
    slab = box("slab", (-13, -14, -0.3), (13, 11, 0), M["floor"], bev=0.03)
    uv_box(slab); P(slab)

    # ---- hull ----
    pts = []
    for s in (-1, 1):
        pts += [(s * 11, -9, 0), (s * 11, 9, 0),
                (s * xb(5.2), -9, 5.2), (s * xb(5.2), yb_back(5.2), 5.2),
                (s * 8.8, -5.5, 7.0), (s * 8.8, 8.0, 7.0)]
    h = hull("hull", pts, M["concrete"], bev=0.05)
    void = box("void", (-8, -6.2, -0.1), (8, 7.0, HALL_H))
    front_open = box("fo", (-2.5, -9.6, -0.1), (2.5, -6.0, 4.0))
    rear_open = box("ro", (-1.0, 6.8, -0.1), (1.0, 10.0, 2.5))
    cut(h, void, front_open, rear_open)
    h.data.materials.clear()
    h.data.materials.append(M["concrete"]); h.data.materials.append(M["moss"])
    for p in h.data.polygons:
        p.material_index = 1 if (p.normal.z > 0.25 and p.center.z > 4.9) else 0
    uv_box(h); P(h)

    # ---- roof mound ----
    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=96, v_segments=48, radius=1.0)
    for v in bm.verts:
        x, y, z = v.co
        px, py, pz = x * 9.8, y * 7.6 + 1.4, 6.6 + z * 1.6
        if z > 0:
            n = noise.fractal(Vector((px * 0.35, py * 0.35, 3.1)), 1.0, 2.0, 4)
            n2 = noise.noise(Vector((px * 1.7, py * 1.7, 9.0)))
            pz += (n * 0.45 + n2 * 0.08) * z
        v.co = Vector((px, py, pz))
    mound = kit._link("mound", bm, M["moss"])
    kit.smooth(mound, 60)
    uv_box(mound); P(mound)

    # ---- moss tufts (silhouette breakup) ----
    import bmesh as _bm
    rnd = random.Random(11)
    tp = []
    for _ in range(200):  # on mound
        x = rnd.uniform(-9.3, 9.3); y = rnd.uniform(-6.0, 8.6)
        if mound_z(x, y) > 6.65:
            tp.append((x, y, mound_z(x, y)))
    for _ in range(200):  # edges: front slope, sides top
        side = rnd.choice(("f", "l", "r", "b"))
        if side == "f":
            x = rnd.uniform(-9.2, 9.2); y = rnd.uniform(-9.1, -6.0); z = 5.2 + (y + 9) / 3.5 * 1.8
        elif side == "b":
            x = rnd.uniform(-8.6, 8.6); y = rnd.uniform(7.2, 8.3); z = 6.6
        else:
            s_ = -1 if side == "l" else 1
            x = s_ * rnd.uniform(8.7, 9.6); y = rnd.uniform(-8.5, 8.0); z = rnd.uniform(5.4, 6.9)
            z = min(z, 7.0)
        tp.append((x, y, z))
    tb = _bm.new()
    for (x, y, z) in tp:
        r = rnd.uniform(0.12, 0.34)
        res = _bm.ops.create_icosphere(tb, subdivisions=2, radius=r)
        for v in res["verts"]:
            j = 1.0 + 0.35 * noise.noise(Vector((x * 5 + v.co.x * 9, y * 5 + v.co.y * 9, v.co.z * 9)))
            v.co = Vector((x + v.co.x * 1.25 * j, y + v.co.y * 1.25 * j, z + v.co.z * 0.95 * j - 0.12))
    tuft = kit._link("tufts", tb, M["moss"]); uv_box(tuft); P(tuft)

    # ---- front: piers, header, jambs, track, strips ----
    for s in (-1, 1):
        x0, x1 = sorted((s * 5.4, s * 8.0))
        p = box("pier", (x0, -9.65, 0), (x1, -8.9, 5.4), M["concrete_dk"], bev=0.05)
        uv_box(p); P(p)
        # hazard boards at pier base
        hz = box("hz", (x0 + .05, -9.67, 0.15), (x1 - .05, -9.65, 0.55), M["hazard"])
        uv_box(hz); P(hz)
        # jambs
        j0, j1 = sorted((s * 2.5, s * 2.9))
        j = box("jamb", (j0, -9.15, 0), (j1, -8.9, 4.12), M["steel"], bev=0.02)
        uv_box(j); P(j)
        # blue indicator
        bl = box("bl", (s * 5.15 - .1, -9.2, 2.1), (s * 5.15 + .1, -9.12, 2.3), M["blue"])
        P(bl); lights.append(("blue", (s * 5.15, -9.25, 2.2)))
    header = box("header", (-5.3, -9.15, 4.12), (5.3, -8.9, 5.3), M["steel"], bev=0.03)
    uv_box(header); P(header)
    track = box("track", (-5.3, -9.58, 4.0), (5.3, -9.15, 4.12), M["steel"], bev=0.02)
    uv_box(track); P(track)
    for row, zc in enumerate((4.5, 4.9)):
        for s in (-1, 1):
            for seg in ((0.4, 2.2), (2.6, 4.9)):
                a, b = sorted((s * seg[0], s * seg[1]))
                st = box("strip", (a, -9.2, zc - .06), (b, -9.15, zc + .06), M["amber"])
                P(st)
            lights.append(("amber", (s * 1.4, -9.4, zc)))
            lights.append(("amber", (s * 3.7, -9.4, zc)))

    # ---- sides: pilasters + steel panels ----
    for s in (-1, 1):
        for yc in (-7.0, -3.5, 0.0, 3.5, 7.0):
            y0, y1 = yc - 0.5, yc + 0.5
            pp = []
            for y in (y0, y1):
                pp += [(s * 11.0, y, 0), (s * 11.75, y, 0), (s * xb(5.8), y, 5.8), (s * (xb(5.8) + 0.35), y, 5.8)]
            pl = hull("pil", pp, M["concrete"], bev=0.04)
            uv_box(pl); P(pl)
        nrm = Vector((7.0, 0, 2.2)).normalized()
        for y0, y1 in ((-6.4, -4.1), (-2.9, -0.6), (0.6, 2.9), (4.1, 6.4)):
            z0, z1 = 0.35, 5.0
            cs = []
            for y in (y0, y1):
                for z in (z0, z1):
                    base = Vector((s * xb(z), y, z))
                    off = Vector((s * nrm.x, 0, nrm.z)) * 0.10
                    cs += [base, base + off]
            pn = hull("panel", cs, M["steel"], bev=0.015, seg=1)
            uv_box(pn); P(pn)
            # light strip near top
            if abs(y0) < 5:
                ls = hull("sl", [Vector((s * xb(5.0), y0 + .4, 4.75)) + Vector((s * nrm.x, 0, nrm.z)) * q
                                 for q in (0.1, 0.13)] +
                          [Vector((s * xb(5.0), y1 - .4, 4.75)) + Vector((s * nrm.x, 0, nrm.z)) * q
                           for q in (0.1, 0.13)] +
                          [Vector((s * xb(4.85), y0 + .4, 4.85)) + Vector((s * nrm.x, 0, nrm.z)) * q
                           for q in (0.1, 0.13)] +
                          [Vector((s * xb(4.85), y1 - .4, 4.85)) + Vector((s * nrm.x, 0, nrm.z)) * q
                           for q in (0.1, 0.13)], M["amber"])
                P(ls)

    # rear: steel panel frame around rear door
    rf = box("rframe", (-1.25, 7.6, 0), (1.25, 8.7, 2.8), M["steel"])
    cut(rf, box("rfc", (-1.0, 7.0, -0.1), (1.0, 9.0, 2.5)))
    uv_box(rf); P(rf)
    # rear steps
    st = box("step", (-1.8, 9.0, 0), (1.8, 10.2, 0.15), M["concrete"]); uv_box(st); P(st)

    # ---- banner ----
    bn = quad("banner", (5.95, -9.70, 1.0), (7.45, -9.70, 1.0), (7.45, -9.70, 4.9), (5.95, -9.70, 4.9), M["banner"])
    P(bn)
    bn2 = box("bannerbar", (5.9, -9.74, 4.9), (7.5, -9.66, 5.0), M["steel"]); uv_box(bn2); P(bn2)

    # ---- front hazard floor stripe ----
    hs = box("hzfloor", (-2.6, -10.6, 0), (2.6, -10.1, 0.02), M["hazard"]); uv_box(hs); P(hs)

    # ---- interior partition + vestibule ----
    PY0, PY1 = -4.35, -4.05
    pl = box("part_l", (-8.05, PY0, 0), (-1.6, PY1, HALL_H + .05), M["concrete"], bev=0.02)
    pr = box("part_r", (1.6, PY0, 0), (8.05, PY1, HALL_H + .05), M["concrete"], bev=0.02)
    pt = box("part_t", (-1.6, PY0, 3.0), (1.6, PY1, HALL_H + .05), M["concrete"], bev=0.02)
    for o in (pl, pr, pt):
        uv_box(o); P(o)
    for s in (-1, 1):
        a, b = sorted((s * 1.6, s * 1.75))
        fr = box("pfr", (a, PY0 - .05, 0), (b, PY1 + .05, 3.0), M["steel"]); uv_box(fr); P(fr)
    ft = box("pft", (-1.75, PY0 - .05, 3.0), (1.75, PY1 + .05, 3.15), M["steel"]); uv_box(ft); P(ft)
    # ceiling ribs
    for yc in (-5.2, -2.0, 1.0, 4.0, 6.5):
        rb = box("rib", (-8, yc - 0.2, HALL_H - 0.3), (8, yc + 0.2, HALL_H), M["concrete_dk"]); uv_box(rb); P(rb)
    # ceiling lights
    for yc in (-5.2, -2.5, 0.0, 2.5, 5.0):
        for xc in (-4.0, 0.0, 4.0):
            if yc == -5.2 and xc != 0.0:
                continue
            lt = box("lt", (xc - .6, yc - .1, HALL_H - 0.38), (xc + .6, yc + .1, HALL_H - 0.3), M["white"])
            P(lt); lights.append(("white", (xc, yc, HALL_H - 0.45)))
    # wall trim stripe (hazard) at vestibule floor
    ht = box("hzv", (-1.6, -5.5, 0), (1.6, -5.1, 0.015), M["hazard"]); uv_box(ht); P(ht)

    # ---- interior props: bunks, lockers, tables ----
    def bunk(x, y, s):
        # head against side wall at x=s*8; length along x
        x0, x1 = (s * 8 - 0.0, s * 6.0) if s > 0 else (s * 8, s * 6.0)
        a, b = sorted((s * 7.95, s * 5.95))
        for lvl, z in ((0, 0.45), (1, 1.4)):
            m = box("mat", (a + .02, y - .43, z), (b - .02, y + .43, z + .14), M["fabric"], bev=0.02, seg=1); P(m)
            fr = box("bfr", (a, y - .45, z - .06), (b, y + .45, z), M["olive"]); uv_box(fr); P(fr)
        for px in (a + .04, b - .04):
            for py in (y - .42, y + .42):
                po = box("post", (px - .035, py - .035, 0), (px + .035, py + .035, 1.95), M["olive"]); uv_box(po); P(po)
    for s in (-1, 1):
        for y in (-3.4, -1.6, 0.2, 2.0, 3.8, 5.6):
            bunk(s * 7, y, s)
    for i, x in enumerate((-7.0, -5.8, -4.6, 4.6, 5.8, 7.0)):
        lk = box("locker", (x - .3, 6.45, 0), (x + .3, 6.95, 2.0), M["olive"], bev=0.01, seg=1); uv_box(lk); P(lk)
    for tx in (-2.2, 2.2):
        tb = box("table", (tx - 1.0, 0.8, 0.72), (tx + 1.0, 1.7, 0.78), M["olive"]); uv_box(tb); P(tb)
        for lx in (-.9, .9):
            for ly in (.88, 1.62):
                lg = box("leg", (tx + lx - .03, ly - .03, 0), (tx + lx + .03, ly + .03, .72), M["steel"]); uv_box(lg); P(lg)
        for by in (0.35, 2.15):
            bn_ = box("bench", (tx - 1.0, by - .2, 0.4), (tx + 1.0, by + .2, 0.45), M["olive"]); uv_box(bn_); P(bn_)
            for lx in (-.9, .9):
                lg = box("bleg", (tx + lx - .03, by - .03, 0), (tx + lx + .03, by + .03, .4), M["steel"]); uv_box(lg); P(lg)

    # ---- roof equipment ----
    eq = [(-5.5, -3.0, 1.6, 1.4, 1.5), (-2.5, -2.2, 1.2, 1.2, 1.1), (3.0, -2.8, 1.8, 1.4, 1.3),
          (6.0, -0.5, 1.2, 1.2, 1.7), (-6.2, 2.5, 1.5, 1.5, 1.3), (-1.0, 3.0, 1.4, 1.0, 1.0),
          (4.0, 3.5, 1.7, 1.2, 1.4), (6.4, 4.5, 1.1, 1.1, 1.6), (-3.5, 5.0, 1.3, 1.0, 1.0), (0.5, -0.5, 1.2, 1.0, 0.9)]
    for i, (x, y, sx, sy, sz) in enumerate(eq):
        z0 = mound_z(x, y) - 0.25
        b = box(f"eq{i}", (x - sx / 2, y - sy / 2, z0), (x + sx / 2, y + sy / 2, z0 + sz), M["olive"], bev=0.03)
        uv_box(b); P(b)
        cap = box(f"eqc{i}", (x - sx / 2 - .05, y - sy / 2 - .05, z0 + sz), (x + sx / 2 + .05, y + sy / 2 + .05, z0 + sz + .08), M["steel"]); uv_box(cap); P(cap)
        for k in range(5):  # louvres on -Y face
            lv = box("lv", (x - sx / 2 + .15, y - sy / 2 - .03, z0 + .3 + k * (sz - .6) / 5), (x + sx / 2 - .15, y - sy / 2, z0 + .3 + k * (sz - .6) / 5 + .06), M["concrete_dk"]); P(lv)
    for i, (x, y) in enumerate(((-7.2, -1.0), (7.0, 2.5), (-0.5, 6.0))):
        z0 = mound_z(x, y) - 0.3
        c = cylinder(f"stack{i}", (x, y, z0 + 1.0), 0.22, 2.0, M["steel"]); uv_box(c); P(c)
        c2 = cylinder(f"stackc{i}", (x, y, z0 + 2.05), 0.3, 0.1, M["steel"]); P(c2)
    # pipes along mound
    for i, (x0, x1, y) in enumerate(((-4, -1, -1.0), (1.5, 5.0, 1.0))):
        for k in range(8):
            xa = x0 + (x1 - x0) * k / 8
            xb_ = x0 + (x1 - x0) * (k + 1) / 8
            z = mound_z(xa, y) + 0.02
            pp = box(f"pipe{i}_{k}", (xa, y - .11, z), (xb_ + .02, y + .11, z + .22), M["steel"]); P(pp)
    # ---- UCX collision ----
    def uc(mn, mx):
        ucx.append((mn, mx))
    uc((-13, -14, -0.3), (13, 11, 0))                         # slab
    uc((-11, -9, 0), (-2.5, -6.2, 5.2))                        # front wall L
    uc((2.5, -9, 0), (11, -6.2, 5.2))                          # front wall R
    uc((-2.5, -9, 4.0), (2.5, -6.2, 5.4))                      # lintel
    uc((-11, -6.2, 0), (-8, 9, 4.0))                           # side L
    uc((8, -6.2, 0), (11, 9, 4.0))                             # side R
    uc((-1.0, 7.0, 2.5), (1.0, 9.0, 4.0))                      # rear lintel
    uc((-8, 7.0, 0), (-1.0, 9.0, 4.0))                         # rear L
    uc((1.0, 7.0, 0), (8, 9.0, 4.0))                           # rear R
    uc((-9.5, -6.2, 4.0), (9.5, 8.2, 7.2))                     # roof mass
    uc((-8.05, -4.35, 0), (-1.6, -4.05, 4.0))                  # partition L
    uc((1.6, -4.35, 0), (8.05, -4.05, 4.0))                    # partition R
    uc((-1.6, -4.35, 3.0), (1.6, -4.05, 4.0))                  # partition lintel
    uc((-9.0, -9.65, 4.0), (9.0, -6.2, 7.0))                   # front slope mass
    # bunks as simple boxes
    for s in (-1, 1):
        for y in (-3.4, -1.6, 0.2, 2.0, 3.8, 5.6):
            a, b = sorted((s * 7.95, s * 5.95))
            uc((a, y - .45, 0), (b, y + .45, 1.95))
    uc((-7.3, 6.45, 0), (-4.3, 6.95, 2.0)); uc((4.3, 6.45, 0), (7.3, 6.95, 2.0))

    # ---- doors ----
    def leaf_blast(side):
        s = side
        x0, x1 = sorted((s * 0.02, s * 2.62))
        plate = box("plate", (x0, -9.45, 0.05), (x1, -9.25, 4.0), M["steel"], bev=0.02)
        objs = [plate]
        # ribs
        rib = lambda a, b, c, d, e, f: box("rib", (a, b, c), (d, e, f), M["steel"])
        xs = sorted((s * 0.12, s * 2.52))
        objs += [rib(xs[0], -9.5, 0.15, xs[1], -9.45, 0.3), rib(xs[0], -9.5, 3.75, xs[1], -9.45, 3.9),
                 rib(xs[0], -9.5, 0.3, xs[0] + 0.12, -9.45, 3.75), rib(xs[1] - 0.12, -9.5, 0.3, xs[1], -9.45, 3.75)]
        mid = (xs[0] + xs[1]) / 2
        objs += [rib(mid - .06, -9.5, 0.3, mid + .06, -9.45, 3.75), rib(xs[0], -9.5, 1.9, xs[1], -9.45, 2.02)]
        # handle + hazard
        hx = s * 0.35
        objs += [box("handle", (hx - .07, -9.58, 1.5), (hx + .07, -9.45, 2.3), M["steel"])]
        for o in objs:
            uv_box(o)
        hzs = box("hzd", (xs[0], -9.51, 0.3), (xs[1], -9.5, 0.6), M["hazard"]); uv_box(hzs)
        objs.append(hzs)
        lamp = box("dl", (s * 0.5 - .1, -9.52, 3.55), (s * 0.5 + .1, -9.5, 3.7), M["amber"])
        objs.append(lamp)
        return objs
    for s, nm in ((-1, "L"), (1, "R")):
        d = join(f"{NAME}_BlastDoor_{nm}", leaf_blast(s))
        set_pivot(d, (s * 1.3, -9.35, 0))
        doors[d.name] = dict(type="slide", pivot=(s * 1.3, -9.35, 0), axis=(1, 0, 0), open=s * 2.45)
    def inner(side):
        s = side
        a, b = sorted((s * 0.02, s * 1.58))
        pl_ = box("ip", (a, -4.26, 0.03), (b, -4.14, 2.95), M["steel"], bev=0.01, seg=1)
        o = [pl_, box("ir", (a + .1, -4.28, 0.15), (b - .1, -4.26, 0.25), M["steel"]),
             box("ir", (a + .1, -4.28, 2.65), (b - .1, -4.26, 2.75), M["steel"]),
             box("hd", (s * 0.2 - .04, -4.32, 1.0), (s * 0.2 + .04, -4.26, 1.3), M["steel"])]
        for q in o:
            uv_box(q)
        return o
    for s, nm in ((-1, "L"), (1, "R")):
        d = join(f"{NAME}_InnerDoor_{nm}", inner(s))
        set_pivot(d, (s * 1.6, -4.2, 0))
        doors[d.name] = dict(type="hinge", pivot=(s * 1.6, -4.2, 0), axis=(0, 0, 1), open=-s * 100.0)
    rd = [box("rd", (-0.99, 7.2, 0.03), (0.99, 7.32, 2.45), M["steel"], bev=0.01, seg=1),
          box("rdh", (0.6, 7.14, 1.0), (0.8, 7.2, 1.2), M["steel"])]
    for q in rd:
        uv_box(q)
    d = join(f"{NAME}_RearDoor", rd)
    set_pivot(d, (-0.99, 7.26, 0))
    doors[d.name] = dict(type="hinge", pivot=(-0.99, 7.26, 0), axis=(0, 0, 1), open=-95.0)

    return parts, doors, ucx, lights


def main(outdir, preview=True):
    kit.reset()
    M = kit.std_materials()
    parts, doors, ucx, lights = build(M)
    static = join(NAME, parts)
    finalize_static(static)
    door_objs = [bpy.data.objects[n] for n in doors]
    for d in door_objs:
        finalize_static(d)
    col = []
    for i, (mn, mx) in enumerate(ucx):
        c = box(f"UCX_{NAME}_{i:02d}", mn, mx)
        col.append(c)
    os.makedirs(outdir, exist_ok=True)
    # door animation actions (for blend preview)
    for nm, info in doors.items():
        ob = bpy.data.objects[nm]
        ob.keyframe_insert("location" if info["type"] == "slide" else "rotation_euler", frame=1)
        if info["type"] == "slide":
            ob.location = Vector(info["pivot"]) + Vector(info["axis"]) * info["open"]
            ob.keyframe_insert("location", frame=40)
            ob.location = Vector(info["pivot"])
        else:
            ob.rotation_euler = (0, 0, math.radians(info["open"]))
            ob.keyframe_insert("rotation_euler", frame=40)
            ob.rotation_euler = (0, 0, 0)
    meta = dict(name=NAME, size_m=[22, 18, 7], doors=doors, lights=lights,
                note="Blender coords in meters; front faces -Y; hinge open = degrees about Z, slide open = meters along axis")
    json.dump(meta, open(os.path.join(outdir, f"{NAME}.json"), "w"), indent=1, default=list)
    kit.export_fbx(os.path.join(outdir, f"{NAME}.fbx"), [static] + door_objs + col)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(outdir, f"{NAME}.blend"))
    # stats
    tris = sum(len(p.vertices) - 2 for o in [static] + door_objs for p in o.data.polygons)
    print("STATIC polys", len(static.data.polygons), "approx tris", tris)
    if preview:
        for o in col:
            o.hide_render = True
        kit.setup_render(samples=int(os.environ.get("SAMPLES", 32)))
        bpy.context.scene.frame_set(1)
        kit.sun()
        c1 = kit.camera((-26, -30, 17), (0, 0, 3.5), 32)
        kit.render(c1, os.path.join(outdir, "prev_front.png"))
        bpy.context.scene.frame_set(40)
        c3 = kit.camera((-12, -22, 2.4), (0, -9, 2.2), 30, "Cam3")
        kit.render(c3, os.path.join(outdir, "prev_door_open.png"))
        for (x, y) in ((0, -5.4), (0, -1), (0, 3), (-4, 5), (4, 5)):
            L = bpy.data.lights.new("pl", "POINT"); L.energy = 900; L.shadow_soft_size = 0.4
            lo = bpy.data.objects.new("pl", L); bpy.context.scene.collection.objects.link(lo)
            lo.location = (x, y, 3.5)
        if os.environ.get("SKIP_INT"):
            return
        c2 = kit.camera((0, -5.6, 1.7), (0, 5, 1.7), 20, "Cam2")
        kit.render(c2, os.path.join(outdir, "prev_interior.png"))



if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "out_bunker")
