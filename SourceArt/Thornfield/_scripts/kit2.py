"""Shared helpers for building scripts (on top of kit.py)."""
import sys, os, math, json, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
from mathutils import Vector, Matrix, noise
import kit
from kit import box, hull, cylinder, quad, cut, uv_box, set_pivot, join, finalize_static, bevel


def prism(name, prof, y0, y1, mat=None, bev=0.0):
    """Convex XZ profile extruded along Y (hull)."""
    pts = [(x, y0, z) for x, z in prof] + [(x, y1, z) for x, z in prof]
    return hull(name, pts, mat, bev=bev)


def strut(name, p0, p1, t=0.1, mat=None):
    """Square-section strut between two points."""
    a, b = Vector(p0), Vector(p1)
    d = (b - a)
    if d.length < 1e-4:
        return None
    d.normalize()
    up = Vector((0, 0, 1)) if abs(d.z) < 0.95 else Vector((1, 0, 0))
    s = d.cross(up).normalized() * t
    u = d.cross(s).normalized() * t
    pts = []
    for p in (a, b):
        for sx, sy in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
            pts.append(p + s * sx + u * sy)
    return hull(name, pts, mat)


def cyl_axis(name, center, r, length, axis, mat=None, seg=16):
    """Cylinder along 'x','y' or 'z' (baked)."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r, depth=length)
    for v in bm.verts:
        x, y, z = v.co
        if axis == "x":
            v.co = Vector((z, y, -x))
        elif axis == "y":
            v.co = Vector((x, z, y))
        v.co += Vector(center)
    return kit._link(name, bm, mat)


def banner_obj(x0, x1, z0, z1, y, M, name="banner", flip=False):
    """Hanging banner facing -Y (front)."""
    q = quad(name, (x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1), M["banner"])
    bar = box(name + "_bar", (x0 - .05, y - .04, z1), (x1 + .05, y + .04, z1 + .1), M["steel"])
    uv_box(bar)
    return [q, bar]


def blast_leaf(name, x0, x1, z0, z1, y0, y1, M, rib=0.05, hazard=True, lamp=True, side=1):
    """Panel door leaf (facing -Y) with ribs. Returns joined object (not yet pivoted)."""
    objs = []
    plate = box("pl", (x0, y0, z0), (x1, y1, z1), M["steel"], bev=0.02)
    objs.append(plate)
    w, h = x1 - x0, z1 - z0
    yf = y0 - rib
    inset = 0.12
    objs += [box("r", (x0 + inset, yf, z0 + inset), (x1 - inset, y0, z0 + inset + .12), M["steel"]),
             box("r", (x0 + inset, yf, z1 - inset - .12), (x1 - inset, y0, z1 - inset), M["steel"]),
             box("r", (x0 + inset, yf, z0 + inset), (x0 + inset + .12, y0, z1 - inset), M["steel"]),
             box("r", (x1 - inset - .12, yf, z0 + inset), (x1 - inset, y0, z1 - inset), M["steel"])]
    nv = max(1, int(w // 1.8))
    for i in range(1, nv):
        xc = x0 + w * i / nv
        objs.append(box("r", (xc - .05, yf, z0 + inset), (xc + .05, y0, z1 - inset), M["steel"]))
    nh = max(1, int(h // 2.0))
    for i in range(1, nh):
        zc = z0 + h * i / nh
        objs.append(box("r", (x0 + inset, yf, zc - .05), (x1 - inset, y0, zc + .05), M["steel"]))
    for o in objs:
        uv_box(o)
    if hazard:
        hz = box("hz", (x0 + inset, yf - .01, z0 + .3), (x1 - inset, yf, z0 + .3 + min(0.4, h * .1)), M["hazard"])
        uv_box(hz); objs.append(hz)
    if lamp:
        xm = (x0 + x1) / 2
        objs.append(box("lp", (xm - .12, yf - .01, z1 - .6), (xm + .12, yf, z1 - .45), M["amber"]))
    return objs


class Ctx:
    def __init__(self, name):
        self.name = name
        self.parts = []
        self.doors = {}
        self.ucx = []
        self.lights = []
        self.M = None

    def P(self, o):
        if o is not None:
            self.parts.append(o)
        return o

    def uc(self, mn, mx):
        self.ucx.append((mn, mx))

    def uc_hull(self, pts):
        self.ucx.append(("H", [tuple(p) for p in pts]))

    def add_door(self, suffix, objs, pivot, kind, axis, amount):
        d = join(f"{self.name}_{suffix}", objs)
        set_pivot(d, pivot)
        self.doors[d.name] = dict(type=kind, pivot=tuple(pivot), axis=tuple(axis), open=amount)
        return d


def finish(ctx, outdir, cams, preview=None, lights_pl=None, extra_meta=None):
    if preview is None:
        preview = not os.environ.get("NOPREVIEW")
    """Join static, build UCX, keyframe doors, export fbx/blend/json and render previews.
    cams: list of dict(name, loc, target, lens, frame, lights(bool), sun(bool))"""
    name = ctx.name
    static = join(name, ctx.parts)
    finalize_static(static)
    door_objs = [bpy.data.objects[n] for n in ctx.doors]
    for d in door_objs:
        finalize_static(d)
    col = []
    for i, (mn, mx) in enumerate(ctx.ucx):
        if mn == "H":
            col.append(hull(f"UCX_{name}_{i:02d}", mx))
        else:
            col.append(box(f"UCX_{name}_{i:02d}", mn, mx))
    os.makedirs(outdir, exist_ok=True)
    for nm, info in ctx.doors.items():
        ob = bpy.data.objects[nm]
        kind = info["type"]
        prop = "location" if kind == "slide" else "rotation_euler"
        ob.keyframe_insert(prop, frame=1)
        if kind == "slide":
            ob.location = Vector(info["pivot"]) + Vector(info["axis"]) * info["open"]
        else:
            r = [0, 0, 0]
            ax = info["axis"]
            idx = [i for i in range(3) if ax[i]][0]
            r[idx] = math.radians(info["open"]) * (1 if ax[idx] > 0 else -1)
            ob.rotation_euler = tuple(r)
        ob.keyframe_insert(prop, frame=40)
        if kind == "slide":
            ob.location = Vector(info["pivot"])
        else:
            ob.rotation_euler = (0, 0, 0)
    meta = dict(name=name, doors=ctx.doors, lights=ctx.lights,
                note="Blender coords in meters; front faces -Y; hinge open = degrees about axis, slide open = meters along axis")
    if extra_meta:
        meta.update(extra_meta)
    json.dump(meta, open(os.path.join(outdir, f"{name}.json"), "w"), indent=1, default=list)
    kit.export_fbx(os.path.join(outdir, f"{name}.fbx"), [static] + door_objs + col)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(outdir, f"{name}.blend"))
    tris = sum(len(p.vertices) - 2 for o in [static] + door_objs for p in o.data.polygons)
    print("STATS", name, "polys", len(static.data.polygons), "tris~", tris, "doors", len(door_objs), "ucx", len(col))
    if preview:
        for o in col:
            o.hide_render = True
        kit.setup_render(samples=int(os.environ.get("SAMPLES", 24)))
        sun_made = False
        for c in cams:
            bpy.context.scene.frame_set(c.get("frame", 1))
            if c.get("sun", True) and not sun_made:
                kit.sun(); sun_made = True
            for (x, y, z, e) in c.get("pls", []):
                L = bpy.data.lights.new("pl", "POINT"); L.energy = e; L.shadow_soft_size = 0.5
                lo = bpy.data.objects.new("pl", L); bpy.context.scene.collection.objects.link(lo)
                lo.location = (x, y, z)
            cam = kit.camera(c["loc"], c["target"], c.get("lens", 30), c["name"])
            kit.render(cam, os.path.join(outdir, f"prev_{c['name']}.png"))
            for o in [o for o in bpy.data.objects if o.type == "LIGHT" and o.name.startswith("pl")]:
                bpy.data.objects.remove(o, do_unlink=True)


def chamfer_box(name, cx, cy, hw, z0, z1, ch, mat=None, bev=0.0):
    pts = []
    for z in (z0, z1):
        for (x, y) in ((hw - ch, hw), (hw, hw - ch), (hw, -hw + ch), (hw - ch, -hw),
                       (-hw + ch, -hw), (-hw, -hw + ch), (-hw, hw - ch), (-hw + ch, hw)):
            pts.append((cx + x, cy + y, z))
    return hull(name, pts, mat, bev=bev)


def tower(c, cx, cy, w, shaft_h, prefix, cabin_h=3.4, door_open=95.0):
    """Hollow walkable tower with square-spiral stairs and an enclosed glazed cabin.
    Door on -Y face at ground. Returns dict of key coordinates."""
    M = c.M; P = c.P
    iw = w - 0.8
    hw = w / 2
    # shaft
    h = box(prefix + "shaft", (cx - hw, cy - hw, 0), (cx + hw, cy + hw, shaft_h), M["concrete"], bev=0.05)
    void = box("v", (cx - iw / 2, cy - iw / 2, -0.1), (cx + iw / 2, cy + iw / 2, shaft_h + 0.01))
    dc = box("dc", (cx - 0.75, cy - hw - 1, -0.1), (cx + 0.75, cy - hw + 1.2, 2.4))
    cut(h, void, dc)
    uv_box(h); P(h)
    # skirt + corner hazards + bands
    sk = box(prefix + "skirt", (cx - hw - 0.4, cy - hw - 0.4, 0), (cx + hw + 0.4, cy + hw + 0.4, 1.2), M["concrete_dk"], bev=0.05)
    cut(sk, box("v", (cx - hw + 0.2, cy - hw + 0.2, -0.1), (cx + hw - 0.2, cy + hw - 0.2, 1.3)), box("dc", (cx - 0.75, cy - hw - 1, -0.1), (cx + 0.75, cy - hw + 1.2, 2.4)))
    uv_box(sk); P(sk)
    for z in (3.5, 6.5, 9.5):
        if z < shaft_h - 0.5:
            bd = box("band", (cx - hw - 0.08, cy - hw - 0.08, z), (cx + hw + 0.08, cy + hw + 0.08, z + 0.25), M["steel"]); uv_box(bd); P(bd)
    for sx in (-1, 1):
        for sy in (-1, 1):
            hz = box("hz", (cx + sx * hw - 0.02 if sx > 0 else cx - hw - 0.02, cy + sy * hw - 0.02 if sy > 0 else cy - hw - 0.02, 0.3),
                     (cx + hw + 0.02 if sx > 0 else cx - hw + 0.02, cy + hw + 0.02 if sy > 0 else cy - hw + 0.02, 1.2), M["hazard"] ) if False else None
    # door frame + leaf
    for s in (-1, 1):
        a, b = sorted((cx + s * 0.75, cx + s * 0.9))
        fr = box("df", (a, cy - hw - 0.04, 0), (b, cy - hw + 0.4, 2.4), M["steel"]); uv_box(fr); P(fr)
    fh = box("dfh", (cx - 0.9, cy - hw - 0.04, 2.4), (cx + 0.9, cy - hw + 0.4, 2.55), M["steel"]); uv_box(fh); P(fh)
    lf = [box("lf", (cx - 0.73, cy - hw + 0.15, 0.03), (cx + 0.73, cy - hw + 0.25, 2.37), M["steel"], bev=0.01, seg=1),
          box("hd", (cx + 0.4, cy - hw + 0.1, 1.0), (cx + 0.6, cy - hw + 0.15, 1.2), M["steel"])]
    for q in lf:
        uv_box(q)
    c.add_door(prefix + "Door", lf, (cx - 0.73, cy - hw + 0.2, 0), "hinge", (0, 0, 1), door_open)
    # stairs
    N = int(round(shaft_h / 0.2)); rise = shaft_h / N
    a = iw / 2 - 0.55
    L = 2 * a
    W = [(-a, -a), (-a, a), (a, a), (a, -a), (-a, -a)]
    D = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    tread_rects = []
    steps = []
    rails = []
    for i in range(N):
        s = (i + 0.5) * 0.28
        seg = int(s // L) % 4
        t = s % L
        px = cx + W[seg][0] + D[seg][0] * t
        py = cy + W[seg][1] + D[seg][1] * t
        top = (i + 1) * rise
        if D[seg][0] == 0:
            mn = (px - 0.55, py - 0.15); mx = (px + 0.55, py + 0.15)
        else:
            mn = (px - 0.15, py - 0.55); mx = (px + 0.15, py + 0.55)
        tread_rects.append((mn, mx, top))
        st = box("step", (mn[0], mn[1], top - 0.14), (mx[0], mx[1], top), M["steel"]); uv_box(st); steps.append(st)
        c.uc((mn[0], mn[1], top - 0.14), (mx[0], mx[1], top))
        inward = [(1, 0), (0, -1), (-1, 0), (0, 1)][seg]
        rails.append((px + inward[0] * 0.5, py + inward[1] * 0.5, top, D[seg]))
    # inner railing (posts + rail + collision) along the open well
    prev = None
    for i, (rx, ry, top, dd) in enumerate(rails):
        po = box("post", (rx - 0.025, ry - 0.025, top), (rx + 0.025, ry + 0.025, top + 0.95), M["steel"]); P(po)
        if prev is not None and (abs(rx - prev[0]) < 0.4 and abs(ry - prev[1]) < 0.4):
            P(strut("rail", (prev[0], prev[1], prev[2] + 0.95), (rx, ry, top + 0.95), 0.025, M["steel"]))
            pts = []
            for (qx, qy, qz) in ((prev[0], prev[1], prev[2]), (rx, ry, top)):
                for dx in (-0.04, 0.04):
                    for dy in (-0.04, 0.04):
                        pts += [(qx + dx, qy + dy, qz), (qx + dx, qy + dy, qz + 1.0)]
            c.uc_hull(pts)
        prev = (rx, ry, top)
    # floor slab at shaft_h (with stair hole)
    fl = box("floor", (cx - iw / 2 - 0.05, cy - iw / 2 - 0.05, shaft_h - 0.3), (cx + iw / 2 + 0.05, cy + iw / 2 + 0.05, shaft_h), M["floor"])
    hole_rects = tread_rects[N - 13:]
    for (mn, mx, top) in hole_rects:
        cut(fl, box("hc", (mn[0] - 0.02, mn[1] - 0.02, shaft_h - 0.5), (mx[0] + 0.02, mx[1] + 0.02, shaft_h + 0.2)))
    uv_box(fl); P(fl)
    for st in steps:
        P(st)
    # floor collision grid avoiding hole
    cell = 0.4
    n = int(math.ceil((iw + 0.1) / cell))
    x0 = cx - iw / 2 - 0.05; y0 = cy - iw / 2 - 0.05
    def in_hole(xa, ya, xb, yb):
        for (mn, mx, top) in hole_rects:
            if xa < mx[0] + 0.03 and xb > mn[0] - 0.03 and ya < mx[1] + 0.03 and yb > mn[1] - 0.03:
                return True
        return False
    for r in range(n):
        ya, yb = y0 + r * cell, min(y0 + (r + 1) * cell, cy + iw / 2 + 0.05)
        run = None
        for q in range(n + 1):
            xa, xb = x0 + q * cell, min(x0 + (q + 1) * cell, cx + iw / 2 + 0.05)
            ok = q < n and not in_hole(xa, ya, xb, yb)
            if ok and run is None:
                run = xa
            if (not ok) and run is not None:
                c.uc((run, ya, shaft_h - 0.3), (x0 + q * cell if q < n else cx + iw / 2 + 0.05, yb, shaft_h))
                run = None
    # wall lamps
    for z in (3.0, 6.0, 9.0, 12.0):
        if z < shaft_h - 0.3:
            lp = box("lamp", (cx - iw / 2, cy - 0.3, z), (cx - iw / 2 + 0.08, cy + 0.3, z + 0.2), M["white"]); P(lp)
            c.lights.append(("white", (cx - iw / 2 + 0.4, cy, z + 0.1)))
    # walls collision
    t = (w - iw) / 2
    c.uc((cx - hw, cy - hw, 0), (cx - hw + t, cy + hw, shaft_h)); c.uc((cx + hw - t, cy - hw, 0), (cx + hw, cy + hw, shaft_h))
    c.uc((cx - hw, cy + hw - t, 0), (cx + hw, cy + hw, shaft_h))
    c.uc((cx - hw, cy - hw, 0), (cx - 0.75, cy - hw + t, shaft_h)); c.uc((cx + 0.75, cy - hw, 0), (cx + hw, cy - hw + t, shaft_h))
    c.uc((cx - 0.75, cy - hw, 2.4), (cx + 0.75, cy - hw + t, shaft_h))
    # ---- cabin ----
    z0 = shaft_h; z1 = shaft_h + cabin_h
    ch = chamfer_box(prefix + "cabin", cx, cy, (w + 1.2) / 2, z0, z1, 0.8, M["concrete_dk"], bev=0.04)
    ci = box("ci", (cx - iw / 2 - 0.2, cy - iw / 2 - 0.2, z0 - 0.01), (cx + iw / 2 + 0.2, cy + iw / 2 + 0.2, z1 - 0.35))
    wz0, wz1 = z0 + 0.9, z0 + 2.5
    wins = [box("w", (cx - 3.0, cy - 6, wz0), (cx - 0.35, cy + 6, wz1)), box("w", (cx + 0.35, cy - 6, wz0), (cx + 3.0, cy + 6, wz1)),
            box("w", (cx - 6, cy - 2.4, wz0), (cx + 6, cy + 2.4, wz1))]
    cut(ch, ci, *wins)
    uv_box(ch); P(ch)
    for (xa, xb) in ((-2.9, -0.45), (0.45, 2.9)):
        for yy in (cy - (w + 1.2) / 2 + 0.25, cy + (w + 1.2) / 2 - 0.25):
            gl = box("gl", (cx + xa, yy - 0.03, wz0 + 0.05), (cx + xb, yy + 0.03, wz1 - 0.05), M["glass_amber"]); P(gl)
    for xx in (cx - (w + 1.2) / 2 + 0.25, cx + (w + 1.2) / 2 - 0.25):
        gl = box("gl", (xx - 0.03, cy - 2.3, wz0 + 0.05), (xx + 0.03, cy + 2.3, wz1 - 0.05), M["glass_amber"]); P(gl)
    roof = box("roof", (cx - (w + 3.0) / 2, cy - (w + 3.0) / 2, z1 - 0.35), (cx + (w + 3.0) / 2, cy + (w + 3.0) / 2, z1 + 0.15), M["concrete"], bev=0.05); uv_box(roof); P(roof)
    for sx in (-1, 1):
        hzr = box("hzr", (cx + sx * (w + 3.0) / 2 - 0.02, cy - 1.0, z1 - 0.3), (cx + sx * (w + 3.0) / 2 + 0.02, cy + 1.0, z1 + 0.1), M["hazard"]) if False else None
    ant = cylinder(prefix + "ant", (cx + 2.0, cy + 2.0, z1 + 1.8), 0.04, 3.6, M["steel"]); P(ant)
    dish = cylinder(prefix + "beacon", (cx - 2.0, cy - 2.0, z1 + 0.4), 0.2, 0.5, M["blue"]); P(dish)
    c.lights.append(("blue", (cx - 2.0, cy - 2.0, z1 + 0.7)))
    # cabin interior console + chair + lamp
    cs = box("console", (cx - 2.0, cy + 1.6, z0), (cx + 2.0, cy + 2.4, z0 + 1.0), M["olive"]); uv_box(cs); P(cs)
    sc = box("scr", (cx - 1.8, cy + 2.3, z0 + 1.0), (cx + 1.8, cy + 2.4, z0 + 1.6), M["screen"]); P(sc)
    lamp = box("cl", (cx - 0.6, cy - 0.1, z1 - 0.45), (cx + 0.6, cy + 0.1, z1 - 0.35), M["white"]); P(lamp)
    c.lights.append(("white", (cx, cy, z1 - 0.6)))
    c.uc((cx - 2.0, cy + 1.6, z0), (cx + 2.0, cy + 2.4, z0 + 1.0))
    # cabin collision walls & roof
    ho = (w + 1.2) / 2
    c.uc((cx - ho, cy - ho, z0), (cx - iw / 2 - 0.2, cy + ho, z1)); c.uc((cx + iw / 2 + 0.2, cy - ho, z0), (cx + ho, cy + ho, z1))
    c.uc((cx - ho, cy - ho, z0), (cx + ho, cy - iw / 2 - 0.2, z1)); c.uc((cx - ho, cy + iw / 2 + 0.2, z0), (cx + ho, cy + ho, z1))
    c.uc((cx - (w + 3) / 2, cy - (w + 3) / 2, z1 - 0.35), (cx + (w + 3) / 2, cy + (w + 3) / 2, z1 + 0.15))
    return dict(top=z1 + 0.15)
