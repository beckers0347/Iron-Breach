import bpy, sys
from mathutils import Vector
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=sys.argv[sys.argv.index("--")+1])
ob = next(o for o in bpy.data.objects if o.type == 'MESH' and not o.name.startswith("UCX"))
dg = bpy.context.evaluated_depsgraph_get()
def ray(o, d):
    ok, loc, n, i, obj, m = bpy.context.scene.ray_cast(dg, Vector(o), Vector(d))
    return (round(loc.x,2), round(loc.y,2), round(loc.z,2)) if ok else None
print("FLOOR", ray((0,0,6),(0,0,-1)), ray((5,3,6),(0,0,-1)))
for z in (1.0, 2.5):
    print("Z", z, "+X", ray((0,0,z),(1,0,0)), "-X", ray((0,0,z),(-1,0,0)), "+Y", ray((0,0,z),(0,1,0)), "-Y", ray((0,0,z),(0,-1,0)))
for y in (-6, 0, 6):
    print("row y", y, "+X", ray((0,y,1.2),(1,0,0)), "-X", ray((0,y,1.2),(-1,0,0)))
for x in (-8, 0, 8):
    print("col x", x, "+Y", ray((x,0,1.2),(0,1,0)), "-Y", ray((x,0,1.2),(0,-1,0)))
print("CEIL", ray((0,0,1),(0,0,1)))
