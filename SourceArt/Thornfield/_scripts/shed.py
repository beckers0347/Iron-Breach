import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector
import kit
from kit import box, cylinder, uv_box, hull, cut
import kit2
from kit2 import Ctx, finish, strut, cyl_axis, prism

CFG = {
    "SM_RearShed": dict(W=12.0, D=8.0, Hw=3.2, rise=0.8, nwin=2, kind="storage"),
    "SM_MessHall": dict(W=20.0, D=12.0, Hw=4.0, rise=1.0, nwin=4, kind="mess"),
}


def build(name, cfg, M):
    W, D, Hw, rise = cfg["W"], cfg["D"], cfg["Hw"], cfg["rise"]
    c = Ctx(name); c.M = M; P = c.P
    hx, hy = W / 2, D / 2
    t = 0.3
    slab = box("slab", (-hx - 2, -hy - 3.5, -0.3), (hx + 2, hy + 1.5, 0), M["floor"], bev=0.03); uv_box(slab); P(slab)
    c.uc((-hx - 2, -hy - 3.5, -0.3), (hx + 2, hy + 1.5, 0))
    prof = [(-hx, 0), (hx, 0), (hx, Hw), (0, Hw + rise), (-hx, Hw)]
    h = prism("hull", prof, -hy, hy, M["steel_dk"], bev=0.03)
    vprof = [(-hx + t, -0.1), (hx - t, -0.1), (hx - t, Hw - 0.05), (0, Hw + rise - 0.25), (-hx + t, Hw - 0.05)]
    void = prism("void", vprof, -hy + t, hy - t)
    cuts = [void, box("fo", (-1.6, -hy - 1, -0.1), (1.6, -hy + 1, 2.8))]
    spacing = W / (cfg["nwin"] + 1)
    wy = [(-hy + 1.8 + i * (D - 3.6) / max(1, (cfg["nwin"] // 2 if cfg["kind"] == "mess" else 1)) ) for i in range(0)]
    nws = 3 if cfg["kind"] == "mess" else 2
    ys = [(-hy + (i + 1) * D / (nws + 1)) for i in range(nws)]
    for y in ys:
        cuts.append(box("w", (-hx - 1, y - 0.7, 1.2), (hx + 1, y + 0.7, 2.5)))
    cut(h, *cuts)
    h.data.materials.clear(); h.data.materials.append(M["steel_dk"]); h.data.materials.append(M["olive"])
    for p in h.data.polygons:
        p.material_index = 1 if p.normal.z > 0.3 else 0
    uv_box(h); P(h)
    for y in ys:
        for sx in (-1, 1):
            gl = box("gl", (sx * (hx - t / 2) - 0.03, y - 0.65, 1.25), (sx * (hx - t / 2) + 0.03, y + 0.65, 2.45), M["glass_amber"]); P(gl)
            fr = box("wf", (sx * hx - 0.06 if sx > 0 else -hx - 0.06, y - 0.78, 1.12), (hx + 0.06 if sx > 0 else -hx + 0.06, y + 0.78, 1.22), M["steel"]); uv_box(fr); P(fr)
            fr2 = box("wf", (sx * hx - 0.06 if sx > 0 else -hx - 0.06, y - 0.78, 2.5), (hx + 0.06 if sx > 0 else -hx + 0.06, y + 0.78, 2.6), M["steel"]); uv_box(fr2); P(fr2)
    # door frame
    for s in (-1, 1):
        a, b = sorted((s * 1.6, s * 1.8))
        fr = box("df", (a, -hy - 0.05, 0), (b, -hy + t + 0.05, 2.85), M["steel"]); uv_box(fr); P(fr)
    fh = box("dfh", (-1.8, -hy - 0.05, 2.8), (1.8, -hy + t + 0.05, 3.0), M["steel"]); uv_box(fh); P(fh)
    hz = box("hz", (-hx - 0.02, -hy - 0.02, 0.1), (hx + 0.02, -hy + 0.0, 0.45), M["hazard"]) if False else None
    ln = box("lamp", (-0.3, -hy - 0.08, 3.1), (0.3, -hy - 0.02, 3.2), M["amber"]); P(ln)
    c.lights.append(("amber", (0, -hy - 0.3, 3.1)))
    # roof ribs
    for s in (-1, 1):
        p0, p1 = Vector((s * hx, Hw)), Vector((0, Hw + rise))
        d = (p1 - p0).normalized(); n = Vector((-d.y, d.x)) if s > 0 else Vector((d.y, -d.x))
        if n.y < 0:
            n = -n
        yy = -hy + 0.5
        while yy < hy:
            pts = []
            for y_ in (yy - 0.06, yy + 0.06):
                for p in (p0, p1):
                    pts += [(p.x, y_, p.y), (p.x + n.x * 0.14, y_, p.y + n.y * 0.14)]
            P(hull("rib", pts, M["concrete_dk"]))
            yy += 1.2
    # roof vents
    for k in range(2 if cfg["kind"] == "storage" else 4):
        vx = box("vent", (-0.4, -hy + 1.5 + k * (D - 3) / (1 if cfg["kind"] == "storage" else 3), Hw + rise), (0.4, -hy + 2.3 + k * (D - 3) / (1 if cfg["kind"] == "storage" else 3), Hw + rise + 0.55), M["olive"]); uv_box(vx); P(vx)
    if cfg["kind"] == "mess":
        for x in (-4, 4):
            st = cylinder("stack", (x, hy - 3, Hw + rise + 0.9), 0.3, 2.0, M["steel"]); P(st)
    # banner by door
    for q in kit2.banner_obj(1.95, 3.0, 1.0, 3.0, -hy - 0.06, M, "banner"):
        P(q)
    # interior
    if cfg["kind"] == "storage":
        for s in (-1, 1):
            for k in range(3):
                y = -1.5 + k * 2.2
                sh = box("shelf", (s * (hx - t) - (0.5 if s > 0 else 0.0) if s > 0 else -hx + t, y - .5, 0), (hx - t if s > 0 else -hx + t + 0.5, y + .5, 2.0), M["olive"]) if False else None
                a, b = sorted((s * (hx - t - 0.55), s * (hx - t)))
                sf = box("shelf", (a, y - 0.5, 0), (b, y + 0.5, 2.1), M["olive"], bev=0.01, seg=1); uv_box(sf); P(sf)
                for z in (0.7, 1.4):
                    P(box("sh", (a, y - 0.5, z), (b, y + 0.5, z + 0.04), M["steel"]))
                c.uc((a, y - .5, 0), (b, y + .5, 2.1))
        for k in range(4):
            cr = box("crate", (-1.2 + (k % 2) * 1.5, hy - 1.6 - (k // 2) * 1.0, 0), (-0.2 + (k % 2) * 1.5, hy - 0.8 - (k // 2) * 1.0, 0.9 + (k % 3) * 0.3), M["olive"], bev=0.02); uv_box(cr); P(cr)
        c.uc((-1.2, hy - 2.6, 0), (1.3, hy - 0.8, 1.5))
    else:
        for r in range(3):
            y = -hy + 2.5 + r * 2.8
            for sx in (-1, 1):
                x0 = sx * 4.5
                tb = box("tab", (x0 - 2.5, y - .45, 0.72), (x0 + 2.5, y + .45, 0.78), M["olive"]); uv_box(tb); P(tb)
                for lx in (-2.3, 2.3):
                    for ly in (-.4, .4):
                        P(box("lg", (x0 + lx - .03, y + ly - .03, 0), (x0 + lx + .03, y + ly + .03, .72), M["steel"]))
                for by in (-0.85, 0.85):
                    P(box("bn", (x0 - 2.5, y + by - .2, 0.4), (x0 + 2.5, y + by + .2, 0.45), M["fabric"]))
                c.uc((x0 - 2.5, y - 1.05, 0), (x0 + 2.5, y + 1.05, 0.78))
        # kitchen counter at back
        kc = box("kc", (-8.5, hy - 2.2, 0), (8.5, hy - 1.0, 1.0), M["steel"], bev=0.02); uv_box(kc); P(kc); c.uc((-8.5, hy - 2.2, 0), (8.5, hy - 1.0, 1.0))
        hd = box("hood", (-6, hy - 2.4, 2.2), (6, hy - 0.5, 2.8), M["steel"]); uv_box(hd); P(hd)
    for xc in ((-hx / 2, hx / 2) if cfg["kind"] == "storage" else (-7, -2.3, 2.3, 7)):
        for yc in ((-1.5, 1.5) if cfg["kind"] == "storage" else (-3.5, 0.5, 3.5)):
            zl = Hw - 0.1
            lt = box("lt", (xc - 0.6, yc - 0.1, zl - 0.08), (xc + 0.6, yc + 0.1, zl), M["white"]); P(lt)
            c.lights.append(("white", (xc, yc, zl - 0.2)))
    # collision
    c.uc((-hx, -hy, 0), (-hx + t, hy, Hw)); c.uc((hx - t, -hy, 0), (hx, hy, Hw)); c.uc((-hx, hy - t, 0), (hx, hy, Hw))
    c.uc((-hx, -hy, 0), (-1.6, -hy + t, Hw)); c.uc((1.6, -hy, 0), (hx, -hy + t, Hw)); c.uc((-1.6, -hy, 2.8), (1.6, -hy + t, Hw))
    c.uc((-hx, -hy, Hw - 0.1), (hx, hy, Hw + rise))
    # doors
    for s, sn in ((-1, "L"), (1, "R")):
        a, b = sorted((s * 0.02, s * 1.58))
        lf = [box("lf", (a, -hy + 0.1, 0.03), (b, -hy + 0.2, 2.77), M["steel"], bev=0.01, seg=1),
              box("lr", (a + .1, -hy + 0.04, 0.2), (b - .1, -hy + 0.1, 0.3), M["steel"]),
              box("lr", (a + .1, -hy + 0.04, 2.45), (b - .1, -hy + 0.1, 2.55), M["steel"]),
              box("hd", (s * 0.3 - .05, -hy + 0.02, 1.0), (s * 0.3 + .05, -hy + 0.1, 1.3), M["steel"])]
        for q in lf:
            uv_box(q)
        c.add_door(f"Door{sn}", lf, (s * 1.6 * -1 * -1 * 1.0 + 0.0, -hy + 0.15, 0) if False else (-s * 0.0 + s * 1.6 * 0 + (-1.6 if s < 0 else 1.6), -hy + 0.15, 0), "hinge", (0, 0, 1), 95.0 * (1 if s < 0 else -1))
    return c


def main(name, outdir):
    kit.reset()
    M = kit.std_materials()
    cfg = CFG[name]
    c = build(name, cfg, M)
    D = cfg["D"]; W = cfg["W"]
    cams = [dict(name="front", loc=(-W * 1.1, -D * 2.2, W * 0.6), target=(0, 0, 2), lens=34, frame=1),
            dict(name="front_open", loc=(-5, -D / 2 - 7, 1.7), target=(0, 0, 1.6), lens=26, frame=40),
            dict(name="interior", loc=(0, -D / 2 + 1.0, 1.6), target=(0, D / 2, 1.5), lens=20, frame=40,
                 pls=[(0, -1, cfg["Hw"] - 0.3, 500), (0, D / 2 - 2, cfg["Hw"] - 0.3, 500)])]
    finish(c, outdir, cams)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
