import bpy, sys
from mathutils import Vector
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=sys.argv[sys.argv.index("--")+1])
for o in bpy.data.objects:
    print("OBJ", o.name, o.type, tuple(round(v,2) for v in o.location), tuple(round(v,1) for v in o.rotation_euler), tuple(round(v,3) for v in o.scale))
    if o.type == 'ARMATURE':
        for b in o.data.bones:
            print("BONE", b.name, tuple(round(v,1) for v in (o.matrix_world @ b.head_local)), tuple(round(v,1) for v in (o.matrix_world @ b.tail_local)), b.parent.name if b.parent else None)
