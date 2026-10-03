import bpy, sys, os, glob, math
from mathutils import Vector
bpy.ops.wm.read_factory_settings(use_empty=True)
files = sorted(glob.glob("X:/IronBreach/SourceArt/Carrowgate/Props/SM_Prop_*.fbx"))
x = 0; row = 0; col = 0
for f in files:
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=f)
    new = [o for o in bpy.data.objects if o not in before]
    for o in new:
        if o.name.startswith("UCX"): o.hide_render = True; o.hide_viewport = True
        elif o.parent is None: o.location = Vector((col * 3.4, -row * 3.2, 0))
    col += 1
    if col == 6: col = 0; row += 1
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'MATERIAL'
sc.render.resolution_x, sc.render.resolution_y = 1900, 1100
cam = bpy.data.objects.new("c", bpy.data.cameras.new("c")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = 25
cam.location = Vector((8.5, -22, 12)); cam.rotation_euler = (Vector((8.5, -7, 0)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
sc.render.filepath = "X:/IronBreach/SourceArt/Carrowgate/Props/_sheet.png"
bpy.ops.render.render(write_still=True)
