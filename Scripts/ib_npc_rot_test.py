import unreal, os
SRC = "X:/Downloads/NPCs/MsIdris_Source/Ms_Idris_wSkeleton.fbx"
SK = unreal.load_asset("/Game/Characters/Infantry/Meshes/JumpSuit/Base_Character_Mesh_Skeleton")
for tag, rot in (("A", unreal.Rotator(roll=90, pitch=0, yaw=0)), ("B", unreal.Rotator(roll=-90, pitch=0, yaw=0))):
    t = unreal.AssetImportTask()
    t.filename = SRC; t.destination_path = "/Game/_NPCTest"; t.destination_name = "Idris_" + tag
    t.automated = True; t.save = False; t.replace_existing = True
    o = unreal.FbxImportUI()
    o.import_mesh = True; o.import_as_skeletal = True; o.import_animations = False; o.import_materials = False; o.import_textures = False
    o.create_physics_asset = False; o.skeleton = SK
    d = o.skeletal_mesh_import_data
    d.set_editor_property("import_uniform_scale", 1.7)
    d.set_editor_property("import_rotation", rot)
    t.options = o
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
    m = unreal.load_asset("/Game/_NPCTest/Idris_" + tag)
    if m:
        b = m.get_bounds()
        unreal.log("ROTTEST %s origin=%s ext=%s skel=%s" % (tag, b.origin, b.box_extent, m.skeleton.get_name() if m.skeleton else None))
    else:
        unreal.log("ROTTEST %s import failed" % tag)
open("X:/IronBreach/Saved/rt_done.txt", "w").write("ok")
unreal.SystemLibrary.quit_editor()
