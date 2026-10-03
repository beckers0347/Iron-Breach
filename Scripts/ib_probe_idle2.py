import unreal
opts = unreal.AnimPoseEvaluationOptions()
for ch in ("Static",):
    m = unreal.load_asset("/Game/Characters/NPCs/%s/SKN_%s" % (ch, ch))
    unreal.log("IDLE2 mesh skel=%s bounds ext=%s" % (m.skeleton.get_path_name(), m.get_bounds().box_extent))
    a = unreal.load_asset("/Game/Characters/NPCs/%s/Retargeted/Loco_Idle_%s" % (ch, ch))
    unreal.log("IDLE2 anim skel=%s" % a.get_editor_property("skeleton").get_path_name())
    ref = unreal.AnimPoseExtensions.get_reference_pose(m.skeleton)
    pose = unreal.AnimPoseExtensions.get_anim_pose_at_time(a, 0.0, opts)
    for n in ("Hips", "Spine2", "Head", "LeftUpLeg", "LeftLeg", "LeftFoot", "LeftToeBase", "LeftHand"):
        r = unreal.AnimPoseExtensions.get_bone_pose(ref, n, unreal.AnimPoseSpaces.WORLD)
        p = unreal.AnimPoseExtensions.get_bone_pose(pose, n, unreal.AnimPoseSpaces.WORLD)
        unreal.log("IDLE2 %-11s ref(%.0f,%.0f,%.0f) scale(%.2f) | idle(%.0f,%.0f,%.0f) scale(%.2f,%.2f,%.2f)" % (n, r.translation.x, r.translation.y, r.translation.z, r.scale3d.x, p.translation.x, p.translation.y, p.translation.z, p.scale3d.x, p.scale3d.y, p.scale3d.z))
open("X:/IronBreach/Saved/run_done.txt","w").write("ok"); unreal.SystemLibrary.quit_editor()
