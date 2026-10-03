"""Blender (bpy) builder for the grass patch meshes. Run with python3 (bpy module) - not inside UE.
Writes SM_GrassPatch_<n>.fbx (4 m x 4 m tiles of real blade geometry, ~7k tris each, one slot named M_Grass).
UV: v = height fraction (0 root .. 1 tip) - the UE material uses it for the root-to-tip colour gradient."""
import bpy, bmesh, math, random, os, sys

OUT = sys.argv[1] if len(sys.argv) > 1 else "/mnt/user-data/outputs/SourceArtGrass"
SIZE = 4.0          # metres
SPACING = 0.35
os.makedirs(OUT, exist_ok=True)


def build(seed):
    rng = random.Random(seed)
    verts, faces, uvs, nrm = [], [], [], []
    n = int(SIZE / SPACING)
    for ix in range(n):
        for iy in range(n):
            cx = -SIZE / 2 + (ix + rng.random()) * SPACING
            cy = -SIZE / 2 + (iy + rng.random()) * SPACING
            for _ in range(rng.randint(8, 13)):
                bx = cx + rng.uniform(-0.12, 0.12)
                by = cy + rng.uniform(-0.12, 0.12)
                h = rng.uniform(0.22, 0.5) * (1.6 if rng.random() < 0.05 else 1.0)
                w = rng.uniform(0.016, 0.03)
                th = rng.uniform(0, 2 * math.pi)
                dx, dy = math.cos(th), math.sin(th)
                px, py = -dy, dx
                lean = h * rng.uniform(0.15, 0.55)
                rows = []
                base = len(verts)
                for k, t in enumerate((0.0, 0.34, 0.68)):
                    wt = w * (1.0 - 0.55 * t)
                    off = lean * t * t
                    z = h * t * (1.0 - 0.12 * t)
                    cxk, cyk = bx + dx * off, by + dy * off
                    for s, u in ((-1, 0.0), (1, 1.0)):
                        verts.append((cxk + px * wt * s, cyk + py * wt * s, z))
                        uvs.append((u, t))
                        nrm.append((dx * 0.25, dy * 0.25, 0.95))
                off = lean
                verts.append((bx + dx * off, by + dy * off, h * 0.9))
                uvs.append((0.5, 1.0))
                nrm.append((dx * 0.35, dy * 0.35, 0.9))
                faces += [(base, base + 1, base + 3, base + 2), (base + 2, base + 3, base + 5, base + 4), (base + 4, base + 5, base + 6)]
    return verts, faces, uvs, nrm


def make(idx):
    verts, faces, uvs, nrm = build(1000 + idx)
    me = bpy.data.meshes.new("SM_GrassPatch_%d" % idx)
    me.from_pydata(verts, [], faces)
    me.update()
    uv = me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        for li in poly.loop_indices:
            vi = me.loops[li].vertex_index
            uv.data[li].uv = uvs[vi]
    try:
        l = [tuple(v) for v in nrm]
        norm = []
        for x, y, z in l:
            m = math.sqrt(x * x + y * y + z * z)
            norm.append((x / m, y / m, z / m))
        me.normals_split_custom_set_from_vertices(norm)
    except Exception as e:
        print("custom normals skipped:", e)
    mat = bpy.data.materials.get("M_Grass") or bpy.data.materials.new("M_Grass")
    me.materials.append(mat)
    ob = bpy.data.objects.new("SM_GrassPatch_%d" % idx, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob, len(faces), len(verts)


bpy.ops.wm.read_factory_settings(use_empty=True)
for i in range(4):
    ob, nf, nv = make(i)
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    path = os.path.join(OUT, "SM_GrassPatch_%d.fbx" % i)
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True, object_types={"MESH"}, axis_forward="-Y", axis_up="Z",
                             global_scale=1.0, apply_unit_scale=True, apply_scale_options="FBX_SCALE_NONE",
                             mesh_smooth_type="FACE", add_leaf_bones=False, path_mode="STRIP")
    print("PATCH", i, "faces", nf, "verts", nv, os.path.getsize(path), "bytes")
