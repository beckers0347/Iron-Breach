"""Carrowgate armoured-bunker kit (Blender, metres, Z up, building front = -Y, footprint centred on origin, floor top z=0).

Matches the look of SM_Barracks_02 / SM_Hangar_04: riveted armour plating, tapered buttresses, parapet roofs with
railings and rooftop plant, chamfers, yellow bollards, numbered chevron markings, hazard-striped door frames.
Material slot names are the same as Barracks_02 so the UE side can reuse its procedural materials.

Run headless:  blender -b -P build_all.py -- <out_root>
"""
import bpy, bmesh, math, random, os, json
from mathutils import Vector, Matrix

# preview colours only (UE re-assigns the real procedural materials by slot name)
PREVIEW = {
    "Concrete_Weathered": (0.55, 0.55, 0.52, 0.9, 0.0), "Interior_Concrete": (0.5, 0.45, 0.36, 0.9, 0.0),
    "Armor_Paint": (0.12, 0.125, 0.135, 0.6, 0.35), "Door_Metal": (0.2, 0.21, 0.22, 0.55, 0.4),
    "Hazard_Stripes": (0.8, 0.52, 0.0, 0.7, 0.0), "Yellow_Paint": (0.75, 0.5, 0.0, 0.55, 0.0),
    "Window_Glass": (0.01, 0.02, 0.03, 0.06, 0.0), "Light_Strip": (1.0, 0.85, 0.55, 0.4, 0.0),
    "Black_Opening": (0.005, 0.005, 0.005, 0.9, 0.0), "Bolt_Steel": (0.3, 0.3, 0.32, 0.55, 0.5),
    "Pipe_Steel": (0.15, 0.155, 0.16, 0.6, 0.4), "Red_Paint": (0.55, 0.04, 0.03, 0.55, 0.0),
    "White_Paint": (0.85, 0.85, 0.82, 0.6, 0.0),
}

SIDES = {"front": ((0, -1), (1, 0)), "back": ((0, 1), (-1, 0)), "left": ((-1, 0), (0, -1)), "right": ((1, 0), (0, 1))}
Z = Vector((0, 0, 1))


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def make_material(name):
    m = bpy.data.materials.get(name)
    if m:
        return m
    c = PREVIEW.get(name, (0.5, 0.5, 0.5, 0.7, 0.0))
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    m.diffuse_color = (c[0] ** 0.6, c[1] ** 0.6, c[2] ** 0.6, 1)
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (c[0], c[1], c[2], 1)
    b.inputs["Roughness"].default_value = c[3]
    b.inputs["Metallic"].default_value = c[4]
    if name == "Light_Strip":
        b.inputs["Emission Color"].default_value = (1, 0.85, 0.55, 1)
        b.inputs["Emission Strength"].default_value = 5.0
    return m


def rotz(deg):
    return Matrix.Rotation(math.radians(deg), 4, "Z")


class Builder:
    def __init__(self, name, seed=1):
        self.name = name
        self.bm = bmesh.new()
        self.uv = self.bm.loops.layers.uv.new("UVMap")
        self.mats = []
        self.hulls = []          # (center Vector, size tuple, yaw deg)
        self.rng = random.Random(seed)
        self.off = Vector((0, 0, 0))

    # -- material slots -------------------------------------------------------------------
    def mi(self, m):
        if m not in self.mats:
            self.mats.append(m)
        return self.mats.index(m)

    def _finish_faces(self, faces, mat, inward=None, mat_in=None):
        for f in faces:
            f.normal_update()
            n = f.normal
            idx = self.mi(mat_in if (inward is not None and mat_in and n.dot(inward) > 0.9) else mat)
            f.material_index = idx
            a = max(range(3), key=lambda i: abs(n[i]))
            for lp in f.loops:
                p = lp.vert.co
                lp[self.uv].uv = {2: (p.x / 3, p.y / 3), 0: (p.y / 3, p.z / 3), 1: (p.x / 3, p.z / 3)}[a]

    # -- primitives -----------------------------------------------------------------------
    def box(self, c, s, mat, yaw=0.0, inward=None, mat_in=None, hull=False, rot=None):
        c = Vector(c) + self.off
        res = bmesh.ops.create_cube(self.bm, size=1.0)
        verts = res["verts"]
        R = rot if rot is not None else rotz(yaw)
        M = Matrix.Translation(c) @ R @ Matrix.Diagonal((s[0], s[1], s[2], 1.0))
        bmesh.ops.transform(self.bm, matrix=M, verts=verts)
        faces = {f for v in verts for f in v.link_faces}
        self._finish_faces(faces, mat, inward, mat_in)
        if hull:
            self.hulls.append((c, tuple(s), yaw))

    def cyl(self, c, r, h, mat, seg=12, axis=None):
        c = Vector(c) + self.off
        res = bmesh.ops.create_cone(self.bm, cap_ends=True, cap_tris=False, segments=seg, radius1=r, radius2=r, depth=h)
        verts = res["verts"]
        R = Matrix.Identity(4)
        if axis is not None:
            R = Z.rotation_difference(Vector(axis).normalized()).to_matrix().to_4x4()
        bmesh.ops.transform(self.bm, matrix=Matrix.Translation(c) @ R, verts=verts)
        self._finish_faces({f for v in verts for f in v.link_faces}, mat)

    def cone(self, c, r1, r2, h, mat, seg=10, axis=None):
        c = Vector(c) + self.off
        res = bmesh.ops.create_cone(self.bm, cap_ends=True, cap_tris=False, segments=seg, radius1=r1, radius2=r2, depth=h)
        verts = res["verts"]
        R = Matrix.Identity(4)
        if axis is not None:
            R = Z.rotation_difference(Vector(axis).normalized()).to_matrix().to_4x4()
        bmesh.ops.transform(self.bm, matrix=Matrix.Translation(c) @ R, verts=verts)
        self._finish_faces({f for v in verts for f in v.link_faces}, mat)

    def bolt(self, p, n, r=0.055):
        self.cone(p, r, r * 0.8, 0.05, "Bolt_Steel", seg=6, axis=n)

    def profile(self, origin, u, n, uc, width, pts, mat):
        """Extrude a convex (d_out, z) polygon along the wall direction u, centred on uc."""
        origin, u, n = Vector(origin) + self.off, Vector(u), Vector(n)
        def W(d, z, du):
            return origin + u * (uc + du) + n * d + Z * z
        v0 = [self.bm.verts.new(W(d, z, -width / 2)) for d, z in pts]
        v1 = [self.bm.verts.new(W(d, z, width / 2)) for d, z in pts]
        faces = [self.bm.faces.new(v0), self.bm.faces.new(list(reversed(v1)))]
        k = len(pts)
        for i in range(k):
            j = (i + 1) % k
            faces.append(self.bm.faces.new([v0[i], v0[j], v1[j], v1[i]]))
        bmesh.ops.recalc_face_normals(self.bm, faces=faces)
        self._finish_faces(faces, mat)

    # -- objects --------------------------------------------------------------------------
    def to_object(self, name, collection=None):
        mesh = bpy.data.meshes.new(name)
        self.bm.to_mesh(mesh)
        for m in self.mats:
            mesh.materials.append(make_material(m))
        for p in mesh.polygons:
            p.use_smooth = False
        ob = bpy.data.objects.new(name, mesh)
        (collection or bpy.context.scene.collection).objects.link(ob)
        return ob

    def hull_objects(self, prefix):
        out = []
        for i, (c, s, yaw) in enumerate(self.hulls, 1):
            bm = bmesh.new()
            res = bmesh.ops.create_cube(bm, size=1.0)
            bmesh.ops.transform(bm, matrix=Matrix.Translation(c) @ rotz(yaw) @ Matrix.Diagonal((s[0], s[1], s[2], 1)), verts=res["verts"])
            me = bpy.data.meshes.new("%s_%02d" % (prefix, i))
            bm.to_mesh(me)
            bm.free()
            ob = bpy.data.objects.new("%s_%02d" % (prefix, i), me)
            bpy.context.scene.collection.objects.link(ob)
            out.append(ob)
        return out


# ------------------------------------------------------------------------------------------
# shell pieces
# ------------------------------------------------------------------------------------------
def frame_of(L, W, side):
    n, u = SIDES[side]
    n, u = Vector((n[0], n[1], 0)), Vector((u[0], u[1], 0))
    half = W / 2 if side in ("front", "back") else L / 2
    return n * half, u, n


def wall(B, L, W, H, t, side, openings, mat_out="Concrete_Weathered", mat_in="Interior_Concrete", plates=0.9, bolts=True, skirt=True):
    """Solid wall with rectangular openings. openings: (uc, width, height, sill). Returns solid segments."""
    origin, u, n = frame_of(L, W, side)
    length = L if side in ("front", "back") else W - 2 * t
    segs = []
    cur = -length / 2
    for uc, w, h, sill in sorted(openings):
        a, b = uc - w / 2, uc + w / 2
        if a > cur + 1e-4:
            segs.append((cur, a, 0.0, H))
        segs.append((a, b, sill + h, H))
        if sill > 0:
            segs.append((a, b, 0.0, sill))
        cur = b
    if cur < length / 2 - 1e-4:
        segs.append((cur, length / 2, 0.0, H))
    yaw = math.degrees(math.atan2(u.y, u.x))
    for a, b, z0, z1 in segs:
        um, zc = (a + b) / 2, (z0 + z1) / 2
        c = origin + u * um - n * (t / 2) + Z * zc
        big = (b - a) > 0.9 and (z1 - z0) > 0.9
        B.box(c, (b - a, t, z1 - z0), mat_out, yaw=yaw, inward=-n, mat_in=mat_in, hull=big)
    # battered base skirt (sloped wedge) along the solid parts that reach the ground
    if skirt:
        for a, b, z0, z1 in segs:
            if z0 == 0.0 and (b - a) > 1.0:
                B.profile(origin, u, n, (a + b) / 2, (b - a), [(0.0, 0.0), (1.15, 0.0), (1.15, 0.45), (0.0, 3.6)], mat_out)
    # armour plates + rivets on the outside of the solid parts (large sheets, a few dark ones)
    if plates > 0:
        for a, b, z0, z1 in segs:
            if (b - a) < 1.6 or (z1 - z0) < 1.4:
                continue
            nu = max(1, round((b - a - 0.7) / 3.4))
            nz = max(1, round((z1 - z0 - 0.7) / 2.7))
            pw, ph = (b - a - 0.7) / nu, (z1 - z0 - 0.7) / nz
            for i in range(nu):
                for j in range(nz):
                    uc = a + 0.35 + pw * (i + 0.5)
                    zc = z0 + 0.35 + ph * (j + 0.5)
                    if B.rng.random() > plates:
                        continue
                    c = origin + u * uc + n * 0.035 + Z * zc
                    pm = "Armor_Paint" if B.rng.random() < 0.07 else "Concrete_Weathered"
                    B.box(c, (pw - 0.14, 0.07, ph - 0.14), pm, yaw=yaw)
                    if bolts:
                        for k in range(max(2, int((pw - 0.5) / 0.9) + 1)):
                            x = uc - pw / 2 + 0.22 + k * (pw - 0.44) / max(1, max(2, int((pw - 0.5) / 0.9) + 1) - 1)
                            for dz in (-1, 1):
                                B.bolt(origin + u * x + n * 0.075 + Z * (zc + dz * (ph / 2 - 0.2)), n)
    return segs


def door_frame(B, L, W, H, side, uc, w, h, sill=0.0, hazard=True, light=True, proud=0.35):
    origin, u, n = frame_of(L, W, side)
    yaw = math.degrees(math.atan2(u.y, u.x))
    jw = 0.55 if w > 2.5 else 0.38
    for s_ in (-1, 1):
        B.box(origin + u * (uc + s_ * (w / 2 + jw / 2 - 0.02)) + n * proud / 2 + Z * (sill + h / 2 + 0.3), (jw, proud, h + 0.6), "Armor_Paint", yaw=yaw)
        for k in range(int(h // 0.9)):
            B.bolt(origin + u * (uc + s_ * (w / 2 + jw / 2 - 0.02)) + n * (proud + 0.02) + Z * (sill + 0.4 + k * 0.9), n)
    B.box(origin + u * uc + n * (proud + 0.05) / 2 + Z * (sill + h + 0.3), (w + jw * 2 - 0.04, proud + 0.05, 0.6), "Armor_Paint", yaw=yaw)
    if hazard:
        B.box(origin + u * uc + n * (proud + 0.08) + Z * (sill + h + 0.3), (w + jw * 2 - 0.5, 0.03, 0.26), "Hazard_Stripes", yaw=yaw)
    # louvre / vent lintel above the door (as on Hangar_04)
    if sill + h + 2.3 < H:
        lw = w + jw * 2 + 1.6
        B.box(origin + u * uc + n * 0.3 + Z * (sill + h + 1.4), (lw, 0.6, 1.1), "Armor_Paint", yaw=yaw)
        for k in range(5):
            B.box(origin + u * uc + n * 0.62 + Z * (sill + h + 1.0 + k * 0.2), (lw - 0.5, 0.04, 0.09), "Black_Opening", yaw=yaw)
        for k in range(int(lw // 1.2) + 1):
            B.bolt(origin + u * (uc - lw / 2 + 0.25 + k * (lw - 0.5) / max(1, int(lw // 1.2))) + n * 0.61 + Z * (sill + h + 1.85), n)
    if light and sill + h + 2.9 < H:
        B.box(origin + u * uc + n * (proud + 0.12) + Z * (sill + h + 0.62), (min(w, 2.4), 0.06, 0.1), "Light_Strip", yaw=yaw)
    B.box(origin + u * uc + n * 0.55 + Z * 0.04, (w + 1.2, 1.1, 0.08), "Hazard_Stripes", yaw=yaw)


def buttresses(B, L, W, H, side, positions, width=1.0, depth=1.0, mat="Armor_Paint"):
    """Tall tapered dark armour columns (as on Barracks_02)."""
    origin, u, n = frame_of(L, W, side)
    top = H - 0.6
    for uc in positions:
        B.profile(origin, u, n, uc, width, [(0.0, 0.0), (depth + 0.3, 0.0), (depth + 0.3, 0.45), (depth, 1.2), (depth * 0.62, top * 0.6), (depth * 0.45, top), (0.0, top)], mat)
        B.profile(origin, u, n, uc, width + 0.3, [(depth * 0.45 - 0.02, top - 0.05), (depth * 0.45 + 0.12, top - 0.05), (depth * 0.45 + 0.12, top + 0.35), (depth * 0.45 - 0.02, top + 0.35)], mat)
        k = 0
        z = 0.9
        while z < top - 0.4:
            d = depth - (depth - depth * 0.45) * (z / top) * 0.8 + 0.01
            for sx in (-1, 1):
                B.bolt(origin + u * (uc + sx * width * 0.34) + n * d + Z * z, n)
            z += 1.1


def windows(B, L, W, H, side, ucs, z0, w=1.5, h=0.9, bars=True):
    origin, u, n = frame_of(L, W, side)
    yaw = math.degrees(math.atan2(u.y, u.x))
    for uc in ucs:
        c = origin + u * uc + n * 0.075 + Z * (z0 + h / 2)
        B.box(c, (w + 0.24, 0.1, h + 0.24), "Armor_Paint", yaw=yaw)
        B.box(c + n * 0.06, (w, 0.05, h), "Window_Glass", yaw=yaw)
        if bars:
            for k in range(1, 5):
                B.box(c + n * 0.1 + u * (-w / 2 + w * k / 5), (0.03, 0.03, h), "Pipe_Steel", yaw=yaw)


def bollards(B, L, W, side, ucs, offset=1.9, h=1.0):
    origin, u, n = frame_of(L, W, side)
    for uc in ucs:
        p = origin + u * uc + n * offset
        B.cyl((p.x, p.y, h / 2), 0.11, h, "Yellow_Paint", seg=8)


SEG7 = {"0": "abcdef", "1": "bc", "2": "abged", "3": "abgcd", "4": "fgbc", "5": "afgcd", "6": "afgedc", "7": "abc", "8": "abcdefg", "9": "abcdfg"}


def digits(B, L, W, side, text, uc, zc, h=1.7, mat="Pipe_Steel", raised=0.07):
    """Real font numerals (flat grey, like the 02 / 04 on Barracks_02 / Hangar_04), converted to mesh and merged."""
    origin, u, n = frame_of(L, W, side)
    cu = bpy.data.curves.new("txt", "FONT")
    cu.body = text
    cu.size = h / 0.72
    cu.extrude = raised * 0.5
    cu.align_x, cu.align_y = "CENTER", "CENTER"
    ob = bpy.data.objects.new("txt", cu)
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    bpy.data.objects.remove(ob, do_unlink=True)
    bpy.context.view_layer.update()
    M = Matrix(((u.x, 0, n.x, 0), (u.y, 0, n.y, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
    M[0][1], M[1][1], M[2][1] = Z.x, Z.y, Z.z
    M = Matrix(((u.x, Z.x, n.x, 0), (u.y, Z.y, n.y, 0), (u.z, Z.z, n.z, 0), (0, 0, 0, 1)))
    pos = origin + u * uc + n * (0.075 + raised * 0.5) + Z * zc + B.off
    tmp = bmesh.new()
    tmp.from_mesh(me)
    bmesh.ops.transform(tmp, matrix=Matrix.Translation(pos) @ M, verts=tmp.verts)
    vmap = {v: B.bm.verts.new(v.co) for v in tmp.verts}
    newf = []
    for f in tmp.faces:
        try:
            newf.append(B.bm.faces.new([vmap[v] for v in f.verts]))
        except ValueError:
            pass
    tmp.free()
    bpy.data.meshes.remove(me)
    B._finish_faces(newf, mat)


def chevron(B, L, W, side, uc, zc, w=1.8, mat="Pipe_Steel", count=2):
    origin, u, n = frame_of(L, W, side)
    yaw = math.degrees(math.atan2(u.y, u.x))
    for k in range(count):
        z = zc - k * 0.55
        for s in (-1, 1):
            Rlean = Matrix.Rotation(math.radians(35 * s), 4, n)
            B.box(origin + u * (uc + s * w * 0.25) + n * 0.1 + Z * z, (w * 0.62, 0.05, 0.2), mat, yaw=0, rot=Rlean @ rotz(yaw))


def cross(B, L, W, side, uc, zc, size=2.4, mat="Red_Paint", back="White_Paint"):
    origin, u, n = frame_of(L, W, side)
    yaw = math.degrees(math.atan2(u.y, u.x))
    B.box(origin + u * uc + n * 0.08 + Z * zc, (size * 1.25, 0.04, size * 1.25), back, yaw=yaw)
    B.box(origin + u * uc + n * 0.11 + Z * zc, (size, 0.04, size * 0.32), mat, yaw=yaw)
    B.box(origin + u * uc + n * 0.11 + Z * zc, (size * 0.32, 0.04, size), mat, yaw=yaw)


def roof(B, L, W, H, rt=0.7, parapet=0.95, rails=True, inset=0.0):
    z1 = H + rt
    B.box((0, 0, H + rt / 2), (L, W, rt), "Concrete_Weathered", inward=-Z, mat_in="Interior_Concrete", hull=True)
    pt = 0.45
    for sx in (-1, 1):
        B.box((sx * (L / 2 - pt / 2), 0, z1 + parapet / 2), (pt, W, parapet), "Armor_Paint")
    for sy in (-1, 1):
        B.box((0, sy * (W / 2 - pt / 2), z1 + parapet / 2), (L - 2 * pt, pt, parapet), "Armor_Paint")
    B.box((0, 0, z1 + parapet + 0.05), (L + 0.3, W + 0.3, 0.1), "Armor_Paint") if False else None
    for sx in (-1, 1):
        B.box((sx * (L / 2 - 0.2), 0, z1 + parapet + 0.06), (0.6, W + 0.1, 0.12), "Armor_Paint")
    for sy in (-1, 1):
        B.box((0, sy * (W / 2 - 0.2), z1 + parapet + 0.06), (L + 0.1, 0.6, 0.12), "Armor_Paint")
    if rails:
        for sy in (-1, 1):
            y = sy * (W / 2 - 0.15)
            for k in range(int(L // 2.2) + 1):
                x = -L / 2 + 0.3 + k * ((L - 0.6) / int(L // 2.2))
                B.box((x, y, z1 + parapet + 0.5), (0.06, 0.06, 1.0), "Pipe_Steel")
            for zz in (0.55, 1.0):
                B.box((0, y, z1 + parapet + zz), (L - 0.5, 0.05, 0.05), "Pipe_Steel")
    return z1 + parapet


def fan(B, x, y, z, r=0.9):
    B.box((x, y, z + 0.3), (r * 2.3, r * 2.3, 0.6), "Armor_Paint")
    B.cyl((x, y, z + 0.64), r * 0.85, 0.08, "Black_Opening", seg=16)
    for k in range(3):
        B.box((x, y, z + 0.7), (r * 1.5, 0.12, 0.03), "Pipe_Steel", yaw=60 * k)


def vent(B, x, y, z, sx=1.4, sy=1.2, sz=1.1):
    B.box((x, y, z + sz / 2), (sx, sy, sz), "Armor_Paint")
    B.box((x, y, z + sz + 0.06), (sx + 0.18, sy + 0.18, 0.12), "Concrete_Weathered")
    for k in range(4):
        B.box((x, y - sy / 2 - 0.02, z + 0.25 + k * 0.2), (sx * 0.7, 0.03, 0.06), "Black_Opening")


def mast(B, x, y, z, h=6.0, r=0.07):
    B.cyl((x, y, z + h / 2), r, h, "Pipe_Steel", seg=6)
    for k in range(1, 4):
        B.box((x, y, z + h * k / 4), (0.9 - 0.15 * k, 0.04, 0.04), "Pipe_Steel", yaw=30 * k)
    B.cone((x, y, z + h + 0.18), 0.05, 0.0, 0.35, "Light_Strip", seg=6)


def dish(B, x, y, z, r=1.1, yaw=0.0):
    B.cyl((x, y, z + 0.6), 0.08, 1.2, "Pipe_Steel", seg=6)
    Rt = rotz(yaw) @ Matrix.Rotation(math.radians(-55), 4, "Y")
    res = bmesh.ops.create_cone(B.bm, cap_ends=True, cap_tris=False, segments=14, radius1=r, radius2=r * 0.12, depth=0.35)
    bmesh.ops.transform(B.bm, matrix=Matrix.Translation((x, y, z + 1.35)) @ Rt, verts=res["verts"])
    B._finish_faces({f for v in res["verts"] for f in v.link_faces}, "Concrete_Weathered")


def lights_strip_row(B, L, W, H, xs, ys, z=None):
    z = (H - 0.15) if z is None else z
    for x in xs:
        for y in ys:
            B.box((x, y, z), (0.18, 2.4, 0.08), "Light_Strip")


# ------------------------------------------------------------------------------------------
# doors
# ------------------------------------------------------------------------------------------
class Door:
    def __init__(self, key, kind, pivot, axis, amount, seconds, B, vols):
        self.key, self.kind, self.pivot, self.axis, self.amount, self.seconds = key, kind, pivot, axis, amount, seconds
        self.B, self.vols = B, vols


def door_vols(L, W, side, uc, w, h, sill=0.0, depth=3.2, extra=1.4, t=0.9, off=(0, 0, 0)):
    origin, u, n = frame_of(L, W, side)
    origin = origin + Vector(off)
    cs = origin + u * uc + n * (depth * 0.5 + 0.2) + Z * (sill + 1.6)
    cb = origin + u * uc - n * (t / 2 - 0.1) + Z * (sill + h / 2)
    swap = side in ("left", "right")
    hs = (depth * 0.5, w / 2 + extra, 1.7) if swap else (w / 2 + extra, depth * 0.5, 1.7)
    hb = (t / 2, w / 2 - 0.1, h / 2) if swap else (w / 2 - 0.1, t / 2, h / 2)
    return {"sensor_c": tuple(round(v, 3) for v in cs), "sensor_h": tuple(round(v, 3) for v in hs),
            "blocker_c": tuple(round(v, 3) for v in cb), "blocker_h": tuple(round(v, 3) for v in hb), "blocker_pitch": 0.0}


def slide_door(key, L, W, side, uc, w, h, dirsign=1, sill=0.0, seconds=1.2, leaf_w=None, stripes=True, cu=None, off=(0, 0, 0)):
    """Sliding leaf riding on the outside of the wall; slides along +/-u by (leaf_w + 0.3)."""
    origin, u, n = frame_of(L, W, side)
    yaw = math.degrees(math.atan2(u.y, u.x))
    lw = leaf_w or (w + 0.5)
    off = Vector(off)
    B = Builder("door_" + key)
    B.off = off
    th = 0.3
    cu = (uc + dirsign * (lw - w) / 2) if cu is None else cu
    ctr = origin + u * cu + n * (0.52 + th / 2) + Z * (sill + h / 2 + 0.05)
    B.box(ctr, (lw, th, h + 0.1), "Door_Metal", yaw=yaw)
    ns = max(3, int((lw - 0.4) / 0.42))
    for k in range(ns):                              # vertical slats, as on the Hangar_04 doors
        B.box(ctr + u * (-lw / 2 + 0.25 + k * (lw - 0.5) / (ns - 1)) + n * (th / 2 + 0.03), (0.1, 0.06, h - 0.3), "Pipe_Steel", yaw=yaw)
    for k in range(int(h // 1.6)):
        B.box(ctr + n * (th / 2 + 0.06) + Z * (-h / 2 + 0.6 + k * 1.6), (lw - 0.2, 0.06, 0.16), "Armor_Paint", yaw=yaw)
    if stripes:
        lead = ctr - u * dirsign * (lw / 2 - 0.13) + n * (th / 2 + 0.02)
        B.box(lead, (0.22, 0.03, h), "Hazard_Stripes", yaw=yaw)
    for i in range(5):
        for j in range(int(h // 1.2) + 1):
            B.bolt(ctr + u * (-lw / 2 + 0.2 + i * (lw - 0.4) / 4) + n * (th / 2 + 0.04) + Z * (-h / 2 + 0.25 + j * 1.2), n)
    amount = dirsign * (lw + 0.3)
    axis = tuple(u)
    return Door(key, "slide", tuple(ctr + off), axis, amount, seconds, B, door_vols(L, W, side, uc, w, h, sill, off=off))


def hinge_door(key, L, W, side, uc, w, h, hinge="left", sill=0.0, seconds=1.0, swing=105.0, off=(0, 0, 0)):
    """Hinged leaf in the opening plane that swings outward about its jamb."""
    origin, u, n = frame_of(L, W, side)
    yaw = math.degrees(math.atan2(u.y, u.x))
    off = Vector(off)
    B = Builder("door_" + key)
    B.off = off
    s = -1 if hinge == "left" else 1                 # jamb side along u
    piv = origin + u * (uc + s * w / 2) - n * 0.25 + Z * (sill)
    d = -u * s                                       # leaf direction from the pivot
    th = 0.22
    ctr = origin + u * uc - n * 0.25 + Z * (sill + h / 2)
    B.box(ctr, (w - 0.08, th, h - 0.06), "Door_Metal", yaw=yaw)
    for k in range(max(3, int(w / 0.4))):
        B.box(ctr + u * (-w / 2 + 0.25 + k * (w - 0.5) / max(2, int(w / 0.4) - 1)) + n * (th / 2 + 0.02), (0.08, 0.04, h - 0.4), "Pipe_Steel", yaw=yaw)
    B.box(ctr + n * (th / 2 + 0.03) + u * (-s * (w / 2 - 0.35)) + Z * 0.0, (0.1, 0.06, 0.5), "Pipe_Steel", yaw=yaw)
    for j in range(int(h // 1.0)):
        B.bolt(ctr + u * (w / 2 - 0.3) * 1 + n * (th / 2 + 0.03) + Z * (-h / 2 + 0.3 + j * 1.0), n)
        B.bolt(ctr - u * (w / 2 - 0.3) * 1 + n * (th / 2 + 0.03) + Z * (-h / 2 + 0.3 + j * 1.0), n)
    cross_z = d.x * n.y - d.y * n.x                  # z of d x n
    amount = swing if cross_z > 0 else -swing
    return Door(key, "hinge", tuple(piv + off), (0, 0, 1), amount, seconds, B, door_vols(L, W, side, uc, w, h, sill, off=off))


# ------------------------------------------------------------------------------------------
# export
# ------------------------------------------------------------------------------------------
def select_only(objs):
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]


def export_fbx(path, objs, armature=False):
    select_only(objs)
    types = {"ARMATURE", "MESH"} if armature else {"MESH"}
    kw = dict(filepath=path, use_selection=True, object_types=types, axis_forward="-Y", axis_up="Z", global_scale=1.0,
              apply_unit_scale=True, apply_scale_options="FBX_SCALE_NONE", mesh_smooth_type="FACE", add_leaf_bones=False,
              path_mode="STRIP")
    if armature:
        kw.update(bake_anim=True, bake_anim_use_all_actions=False, bake_anim_use_nla_strips=False,
                  bake_anim_force_startend_keying=True, bake_anim_step=1.0, bake_anim_simplify_factor=0.0)
    else:
        kw.update(bake_anim=False)
    bpy.ops.export_scene.fbx(**kw)


def export_door(door, out_dir, bname):
    scn = bpy.context.scene
    scn.render.fps = 30
    scn.frame_start, scn.frame_end = 1, 40
    ob = door.B.to_object("SK_%s_Door_%s" % (bname, door.key))
    arm_data = bpy.data.armatures.new("Door_Arm")
    arm = bpy.data.objects.new("Door_Arm_" + door.key, arm_data)
    scn.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    arm.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    eb = arm_data.edit_bones.new("Door")
    p = Vector(door.pivot)
    eb.head = p
    eb.tail = p + Vector((0, 0.5, 0))
    eb.roll = 0.0
    bpy.ops.object.mode_set(mode="OBJECT")
    vg = ob.vertex_groups.new(name="Door")
    vg.add(list(range(len(ob.data.vertices))), 1.0, "REPLACE")
    mod = ob.modifiers.new("Armature", "ARMATURE")
    mod.object = arm
    ob.parent = arm
    pb = arm.pose.bones["Door"]
    pb.rotation_mode = "XYZ"
    if door.kind == "slide":
        pb.keyframe_insert("location", frame=1)
        pb.location = Vector(door.axis) * door.amount
        pb.keyframe_insert("location", frame=40)
    else:
        pb.keyframe_insert("rotation_euler", frame=1)
        pb.rotation_euler = (0, 0, math.radians(door.amount))
        pb.keyframe_insert("rotation_euler", frame=40)
    pb.location = (0, 0, 0)
    pb.rotation_euler = (0, 0, 0)
    path = os.path.join(out_dir, "SK_%s_Door_%s.fbx" % (bname, door.key))
    export_fbx(path, [arm, ob], armature=True)
    return os.path.basename(path)


def vent_tower(B, x, y, z, sx=3.0, sy=2.6, sz=3.4):
    """Tall louvred vent block with a cap (the big rooftop blocks on Hangar_04)."""
    B.box((x, y, z + sz / 2), (sx, sy, sz), "Armor_Paint")
    B.box((x, y, z + sz + 0.1), (sx + 0.4, sy + 0.4, 0.2), "Concrete_Weathered")
    for face in (-1, 1):
        for k in range(6):
            B.box((x, y + face * (sy / 2 + 0.02), z + 0.8 + k * 0.38), (sx * 0.7, 0.04, 0.12), "Black_Opening")
    for k in range(4):
        B.bolt((x - sx / 2 + 0.3 + k * (sx - 0.6) / 3, y - sy / 2 - 0.03, z + sz - 0.25), (0, -1, 0))


def grate_panel(B, x, y, z, sx=6.0, sy=2.0):
    B.box((x, y, z + 0.04), (sx, sy, 0.08), "Black_Opening")
    for k in range(int(sx / 0.35)):
        B.box((x - sx / 2 + 0.2 + k * 0.35, y, z + 0.1), (0.05, sy - 0.1, 0.05), "Pipe_Steel")


def tank(B, x, y, z, r=1.2, h=3.6):
    B.cyl((x, y, z + h / 2), r, h, "Armor_Paint", seg=16)
    for k in (0.25, 0.75):
        B.cyl((x, y, z + h * k), r + 0.06, 0.22, "Pipe_Steel", seg=16)
    B.cyl((x, y, z + h + 0.1), r * 0.9, 0.2, "Concrete_Weathered", seg=16)
    B.cyl((x + r * 0.5, y, z + h + 0.5), 0.12, 0.8, "Pipe_Steel", seg=8)


def pipe_run(B, L, W, side, u0, u1, z, count=3, gap=0.2, r=0.07, d=0.2):
    origin, u, n = frame_of(L, W, side)
    ln = abs(u1 - u0)
    for k in range(count):
        c = origin + u * ((u0 + u1) / 2) + n * d + Z * (z + k * gap)
        B.cyl(c, r, ln, "Pipe_Steel", seg=6, axis=tuple(u))
    for e in (u0, u1):
        B.box(origin + u * e + n * (d - 0.05) + Z * (z + (count - 1) * gap / 2), (0.12, 0.14, count * gap + 0.1), "Armor_Paint", yaw=math.degrees(math.atan2(u.y, u.x)))
