import unreal
AT = unreal.AssetToolsHelpers.get_asset_tools()
for tag, yaw in (("P", 90), ("N", -90)):
    t = unreal.AssetImportTask()
    t.filename = "X:/Downloads/NPCs/MsIdris_Source/Ms_Idris_wSkeleton.fbx"
    t.destination_path = "/Game/_NPCTest"; t.destination_name = "Face_" + tag
    t.automated = True; t.save = False; t.replace_existing = True
    o = unreal.FbxImportUI(); o.import_mesh = True; o.import_as_skeletal = True; o.import_animations = False
    o.import_materials = False; o.import_textures = False; o.create_physics_asset = False
    o.skeletal_mesh_import_data.set_editor_property("import_rotation", unreal.Rotator(roll=-90, pitch=0, yaw=yaw))
    t.options = o
    AT.import_asset_tasks([t])
    m = unreal.load_asset("/Game/_NPCTest/Face_" + tag)
    pose = unreal.AnimPoseExtensions.get_reference_pose(m.skeleton)
    def w(n): return unreal.AnimPoseExtensions.get_bone_pose(pose, n, unreal.AnimPoseSpaces.WORLD).translation
    f, tb, lh = w("LeftFoot"), w("LeftToeBase"), w("LeftHand")
    b = m.get_bounds()
    unreal.log("FACE %s yaw=%d ext=(%.0f,%.0f,%.0f) toe-foot=(%.1f,%.1f) LeftHand=(%.0f,%.0f,%.0f)" % (tag, yaw, b.box_extent.x, b.box_extent.y, b.box_extent.z, tb.x - f.x, tb.y - f.y, lh.x, lh.y, lh.z))
open("X:/IronBreach/Saved/run_done.txt","w").write("ok"); unreal.SystemLibrary.quit_editor()
