import unreal
m = unreal.load_asset("/Game/Characters/Infantry/Meshes/JumpSuit/Base_Character_Mesh")
b = m.get_bounds()
unreal.log("INFB extent=%s origin=%s" % (b.box_extent, b.origin))
sk = m.skeleton
# mesh-space ref pose via the skeletal mesh's own ref skeleton
rs = m.get_ref_skeleton() if hasattr(m, "get_ref_skeleton") else None
unreal.log("INFB has ref skel api %s" % (rs is not None))
for n in ("Hips", "Head", "LeftFoot", "LeftHand", "RightHand"):
    try:
        unreal.log("INFB socket-less %s" % n)
    except Exception: pass
anim = unreal.load_asset("/Game/Characters/Infantry/Animations/Locomotion_Unarmed/Loco_Idle")
opts = unreal.AnimPoseEvaluationOptions()
pose = unreal.AnimPoseExtensions.get_anim_pose_at_time(anim, 0.0, opts)
for n in ("Hips", "Head", "LeftFoot", "RightFoot", "LeftHand"):
    t = unreal.AnimPoseExtensions.get_bone_pose(pose, n, unreal.AnimPoseSpaces.WORLD).translation
    unreal.log("INFB idle %s (%.1f,%.1f,%.1f)" % (n, t.x, t.y, t.z))
for p in ("Idris/Retargeted/Loco_Idle_Idris", "Rhodes/Retargeted/Loco_Idle_Rhodes"):
    a = unreal.load_asset("/Game/Characters/NPCs/" + p)
    pose = unreal.AnimPoseExtensions.get_anim_pose_at_time(a, 0.0, opts)
    for n in ("Hips", "Head", "LeftFoot", "LeftHand"):
        t = unreal.AnimPoseExtensions.get_bone_pose(pose, n, unreal.AnimPoseSpaces.WORLD).translation
        unreal.log("INFB %s %s (%.1f,%.1f,%.1f)" % (p.split('/')[-1], n, t.x, t.y, t.z))
open("X:/IronBreach/Saved/run_done.txt","w").write("ok"); unreal.SystemLibrary.quit_editor()
