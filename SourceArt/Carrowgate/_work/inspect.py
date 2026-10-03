import bpy, sys, math
from mathutils import Vector
path = sys.argv[sys.argv.index("--")+1]
out = sys.argv[sys.argv.index("--")+2]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=path)
objs = [o for o in bpy.data.objects if o.type == 'MESH']
mn = Vector((1e9,)*3); mx = Vector((-1e9,)*3)
for o in objs:
    for c in o.bound_box:
        w = o.matrix_world @ Vector(c)
        mn = Vector(map(min, mn, w)); mx = Vector(map(max, mx, w))
print("OBJS", [(o.name, len(o.data.polygons)) for o in objs])
print("DIMS", tuple(round(v,2) for v in (mx-mn)), "MIN", tuple(round(v,2) for v in mn), "MAX", tuple(round(v,2) for v in mx))
print("MATS", sorted({m.name for o in objs for m in o.data.materials if m}))
print("UNIT", bpy.context.scene.unit_settings.scale_length)
# simple preview render
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'MATERIAL'
sc.render.resolution_x, sc.render.resolution_y = 1000, 640
cam = bpy.data.objects.new("c", bpy.data.cameras.new("c")); sc.collection.objects.link(cam); sc.camera = cam
c = (mn+mx)/2; d = (mx-mn).length
cam.location = c + Vector((-0.9, -1.3, 0.7))*d*0.8
dirv = c - cam.location
cam.rotation_euler = dirv.to_track_quat('-Z','Y').to_euler()
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
