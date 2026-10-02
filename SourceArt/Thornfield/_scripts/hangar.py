import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector
import kit
from kit import box, hull, cylinder, quad, cut, uv_box, set_pivot, join
import kit2
from kit2 import Ctx, prism, strut, cyl_axis, blast_leaf, finish

NAME = "SM_HangarBlock"
BAYS = (-22.0, 0.0, 22.0)
Y0, Y1 = -20.0, 20.0
EAVE, RIDGE = 10.5, 14.0
OPEN_W, OPEN_H = 14.0, 10.5


def prof_out(bx, inset=0.0):
    i = inset
    return [(bx - 11 + i, -0.1 if inset else 0), (bx + 11 - i, -0.1 if inset else 0),
            (bx + 11 - i, EAVE - i), (bx + 4 - i * 0.55, RIDGE - i), (bx - 4 + i * 0.55, RIDGE - i), (bx - 11 + i, EAVE - i)]


def build(M):
    c = Ctx(NAME); c.M = M; P = c.P
    random.seed(3)
    solar = kit.flat_mat("M_Solar", (0.04, 0.08, 0.2), 0.25, 0.6)
    # floor / apron
    slab = box("slab", (-34, -32, -0.3), (34, 22, 0), M["floor"], bev=0.03); uv_box(slab); P(slab)
    for i in range(7):  # apron hazard stripes
        x = -30 + i * 10
        hz = kit.hull("hzs", [(x, -30, 0), (x + 2.2, -30, 0), (x + 5.2, -24, 0), (x + 3.0, -24, 0),
                              (x, -30, 0.02), (x + 2.2, -30, 0.02), (x + 5.2, -24, 0.02), (x + 3.0, -24, 0.02)], M["hazard"])
        uv_box(hz); P(hz)
    for bi, bx in enumerate(BAYS):
        # ---- shell ----
        h = prism("hull", prof_out(bx), Y0, Y1, M["steel_dk"], bev=0.04)
        void = prism("void", prof_out(bx, 0.5), Y0 + 0.5, Y1 - 0.5)
        fo = box("fo", (bx - 7, Y0 - 1, -0.1), (bx + 7, Y0 + 1.5, OPEN_H))
        ro = box("ro", (bx - 1.0, Y1 - 1.5, -0.1), (bx + 1.0, Y1 + 1, 2.6))
        cut(h, void, fo, ro)
        h.data.materials.clear(); h.data.materials.append(M["steel_dk"]); h.data.materials.append(M["olive"])
        for p in h.data.polygons:
            p.material_index = 1 if p.normal.z > 0.3 else 0
        uv_box(h); P(h)
        # front frame
        for s in (-1, 1):
            a, b = sorted((bx + s * 7.0, bx + s * 8.3))
            j = box("jamb", (a, Y0 - 0.55, 0), (b, Y0, OPEN_H + 1.2), M["concrete_dk"], bev=0.04); uv_box(j); P(j)
            ch = hull("ch", [(bx + s * 8.3, Y0 - 0.55, OPEN_H + 1.2), (bx + s * 8.3, Y0, OPEN_H + 1.2),
                             (bx + s * 4.0, Y0 - 0.55, RIDGE - 0.3), (bx + s * 4.0, Y0, RIDGE - 0.3),
                             (bx + s * 8.3, Y0 - 0.55, OPEN_H + 2.3), (bx + s * 8.3, Y0, OPEN_H + 2.3),
                             (bx + s * 3.6, Y0 - 0.55, RIDGE + 0.0), (bx + s * 3.6, Y0, RIDGE + 0.0)], M["concrete_dk"])
            uv_box(ch); P(ch)
        lt = box("lintel", (bx - 7.0, Y0 - 0.55, OPEN_H), (bx + 7.0, Y0, OPEN_H + 1.2), M["concrete_dk"], bev=0.04); uv_box(lt); P(lt)
        top = box("lt2", (bx - 4.0, Y0 - 0.55, OPEN_H + 1.2), (bx + 4.0, Y0, RIDGE - 0.3), M["steel"]); uv_box(top); P(top)
        # amber lights above door, under lintel
        for s in (-1, 1):
            st = box("st", (bx + s * 0.5 if s > 0 else bx - 6.5, Y0 - 0.58, OPEN_H - 0.35), (bx + 6.5 if s > 0 else bx - 0.5, Y0 - 0.55, OPEN_H - 0.2), M["amber"]); P(st)
        # door rail above opening (outside)
        rl = box("rail", (bx - 11.0, Y0 - 1.15, OPEN_H + 0.05), (bx + 11.0, Y0 - 0.6, OPEN_H + 0.35), M["steel"]); uv_box(rl); P(rl)
        # roof ribs, solar, skylight
        for s in (-1, 1):
            p0, p1 = Vector((bx + s * 11, EAVE)), Vector((bx + s * 4, RIDGE))
            d = (p1 - p0).normalized(); n = Vector((-d.y, d.x)) if s > 0 else Vector((d.y, -d.x))
            if n.y < 0:
                n = -n
            for k in range(20):
                yc = -19 + k * 2.0
                pts = []
                for yy in (yc - 0.07, yc + 0.07):
                    for p in (p0, p1):
                        pts.append((p.x, yy, p.y)); pts.append((p.x + n.x * 0.2, yy, p.y + n.y * 0.2))
                r = hull("rib", pts, M["concrete_dk"]); uv_box(r, 2); P(r)
            # solar on the front-sloping side panels
            for (ya, yb) in ((-17, -11), (-9, -3), (-1, 5), (7, 13)):
                q0, q1 = p0 + (p1 - p0) * 0.2, p0 + (p1 - p0) * 0.8
                pts = []
                for yy in (ya, yb):
                    for q in (q0, q1):
                        pts.append((q.x + n.x * 0.22, yy, q.y + n.y * 0.22)); pts.append((q.x + n.x * 0.3, yy, q.y + n.y * 0.3))
                sp = hull("solar", pts, solar); uv_box(sp, 2); P(sp)
        sk = box("sky", (bx - 3.4, -12, RIDGE), (bx + 3.4, 12, RIDGE + 0.3), M["glass"]); P(sk)
        skf = box("skf", (bx - 3.6, -12.2, RIDGE), (bx + 3.6, 12.2, RIDGE + 0.15), M["steel"]); uv_box(skf); P(skf)
        for k in range(3):
            vx = box("vent", (bx - 2 + k * 2.6, 14, RIDGE), (bx - 1 + k * 2.6, 15.2, RIDGE + 0.9), M["olive"]); uv_box(vx); P(vx)
        # corner piers
        for s in (-1, 1):
            pb = box("pier", (bx + s * 11 - 0.7, Y0 - 1.0, 0), (bx + s * 11 + 0.7, Y0 + 0.3, 3.2), M["concrete"], bev=0.06); uv_box(pb); P(pb)
        # ---- interior ----
        for yc in (-14, -7, 0, 7, 14):
            for s in (-1, 1):
                a, b = sorted((bx + s * 9.8, bx + s * 10.5))
                col = box("col", (a, yc - 0.3, 0), (b, yc + 0.3, EAVE - 0.3), M["olive"]); uv_box(col); P(col)
            tie = box("tie", (bx - 10.5, yc - 0.15, EAVE - 0.55), (bx + 10.5, yc + 0.15, EAVE - 0.3), M["olive"]); uv_box(tie); P(tie)
            for s in (-1, 1):
                st = strut("raf", (bx + s * 10.4, yc, EAVE - 0.3), (bx + s * 3.8, yc, RIDGE - 0.6), 0.1, M["olive"]); P(st)
                br = strut("brace", (bx + s * 6.0, yc, EAVE - 0.4), (bx + s * 3.2, yc, EAVE + 1.6), 0.07, M["olive"]); P(br)
            lt = box("lamp", (bx - 3, yc - 0.12, EAVE - 0.7), (bx + 3, yc + 0.12, EAVE - 0.58), M["amber"]); P(lt)
            c.lights.append(("amber", (bx, yc, EAVE - 0.8)))
        for s in (-1, 1):
            pp = cyl_axis("pipe", (bx + s * 9.5, 0, 3.0), 0.16, 38.5, "y", M["steel"]); P(pp)
            pp2 = cyl_axis("pipe", (bx + s * 9.5, 0, 3.6), 0.1, 38.5, "y", M["olive"]); P(pp2)
            rail = box("rail", (bx + s * 3 - 0.1, Y0 + 1, 0), (bx + s * 3 + 0.1, Y1 - 1, 0.07), M["steel"]); uv_box(rail); P(rail)
        for k in range(6):  # floor markings
            fm = box("fm", (bx - 8.5, Y0 + 3 + k * 6, 0), (bx + 8.5, Y0 + 3.15 + k * 6, 0.015), M["hazard"]); uv_box(fm); P(fm)
        # props: crates & benches along back
        for k, x in enumerate((-8, -6.2, 6.2, 8)):
            cr = box("crate", (bx + x - .8, 16.8, 0), (bx + x + .8, 18.4, 1.4 + (k % 2) * .6), M["olive"], bev=0.03); uv_box(cr); P(cr)
        wb = box("bench", (bx - 3, 18.4, 0.85), (bx + 3, 19.3, 0.95), M["steel"]); uv_box(wb); P(wb)
        for lx in (-2.8, 2.8):
            lg = box("lg", (bx + lx - .05, 18.5, 0), (bx + lx + .05, 19.2, 0.85), M["steel"]); P(lg)
        # ---- collision ----
        c.uc((bx - 11, Y0, 0), (bx - 10.5, Y1, EAVE))
        c.uc((bx + 10.5, Y0, 0), (bx + 11, Y1, EAVE))
        c.uc((bx - 10.5, Y1 - 0.5, 0), (bx - 1.0, Y1, EAVE))
        c.uc((bx + 1.0, Y1 - 0.5, 0), (bx + 10.5, Y1, EAVE))
        c.uc((bx - 1.0, Y1 - 0.5, 2.6), (bx + 1.0, Y1, EAVE))
        c.uc((bx - 10.5, Y0, 0), (bx - 7.0, Y0 + 0.5, EAVE))
        c.uc((bx + 7.0, Y0, 0), (bx + 10.5, Y0 + 0.5, EAVE))
        c.uc((bx - 7.0, Y0, OPEN_H), (bx + 7.0, Y0 + 0.5, RIDGE))
        # roof hull as convex box approximation: two stepped boxes
        c.uc((bx - 11, Y0, EAVE - 0.3), (bx + 11, Y1, EAVE + 0.3))
        c.uc((bx - 7.5, Y0, EAVE), (bx + 7.5, Y1, RIDGE - 0.2))
        # ---- doors ----
        for side, sn in ((-1, "L"), (1, "R")):
            for layer, ln in ((0, "B"), (1, "A")):
                if ln == "A":
                    xa, xb = (bx - 3.5, bx - 0.02) if side < 0 else (bx + 0.02, bx + 3.5)
                    ya, yb = Y0 - 1.30, Y0 - 1.10
                    amt = side * 7.0
                else:
                    xa, xb = (bx - 7.3, bx - 3.52) if side < 0 else (bx + 3.52, bx + 7.3)
                    ya, yb = Y0 - 0.95, Y0 - 0.75
                    amt = side * 3.5
                objs = blast_leaf("leaf", xa, xb, 0.05, OPEN_H - 0.05, ya, yb, M, side=side)
                xc = (xa + xb) / 2
                c.add_door(f"Bay{bi}_Door{sn}{ln}", objs, (xc, (ya + yb) / 2, 0), "slide", (1, 0, 0), amt)
        rd = [box("rd", (bx - 0.99, Y1 - 0.9, 0.03), (bx + 0.99, Y1 - 0.8, 2.55), M["steel"], bev=0.01, seg=1),
              box("rdh", (bx + 0.6, Y1 - 0.95, 1.0), (bx + 0.8, Y1 - 0.9, 1.2), M["steel"])]
        for q in rd:
            uv_box(q)
        c.add_door(f"Bay{bi}_RearDoor", rd, (bx - 0.99, Y1 - 0.85, 0), "hinge", (0, 0, 1), -95.0)
    # end banners (east/west faces)
    for sx, xs in ((-1, -33.05), (1, 33.05)):
        y0, y1 = -17.0, -14.8
        if sx > 0:
            q = quad("banner", (xs, y0, 3.0), (xs, y1, 3.0), (xs, y1, 9.0), (xs, y0, 9.0), M["banner"])
        else:
            q = quad("banner", (xs, y1, 3.0), (xs, y0, 3.0), (xs, y0, 9.0), (xs, y1, 9.0), M["banner"])
        P(q)
    c.uc((-34, -32, -0.3), (34, 22, 0))
    return c


def main(outdir):
    kit.reset()
    M = kit.std_materials()
    c = build(M)
    cams = [dict(name="front", loc=(-75, -90, 48), target=(0, 0, 5), lens=34, frame=1),
            dict(name="front_open", loc=(-30, -60, 8), target=(-6, -20, 5), lens=30, frame=40),
            dict(name="interior", loc=(0, 14, 2.4), target=(0, -20, 4.5), lens=20, frame=40,
                 pls=[(0, 12, 9.5, 6000), (0, 0, 9.5, 6000), (0, -12, 9.5, 6000)])]
    finish(c, outdir, cams)


if __name__ == "__main__":
    main(sys.argv[1])
