import unreal
for ch in ("Idris", "Rhodes", "Bricks", "Static"):
    m = unreal.load_asset("/Game/Characters/NPCs/%s/SKN_%s" % (ch, ch))
    b = m.get_bounds()
    pose = unreal.AnimPoseExtensions.get_reference_pose(m.skeleton)
    g = lambda n: unreal.AnimPoseExtensions.get_bone_pose(pose, n, unreal.AnimPoseSpaces.WORLD).translation
    f, t, lh = g("LeftFoot"), g("LeftToeBase"), g("LeftHand")
    unreal.log("EXT %s ext=(%.0f,%.0f,%.0f) toe-foot=(%.1f,%.1f) LeftHand=(%.0f,%.0f,%.0f)" % (ch, b.box_extent.x, b.box_extent.y, b.box_extent.z, t.x - f.x, t.y - f.y, lh.x, lh.y, lh.z))
open("X:/IronBreach/Saved/run_done.txt","w").write("ok"); unreal.SystemLibrary.quit_editor()
