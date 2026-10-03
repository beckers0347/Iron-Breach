import unreal, math
opts = unreal.AnimPoseEvaluationOptions()
def yaw(a, b):
    d = (b.x - a.x, b.y - a.y); return math.degrees(math.atan2(d[1], d[0]))
def meas(anim, names, tag):
    pose = unreal.AnimPoseExtensions.get_anim_pose_at_time(anim, 0.0, opts)
    g = lambda n: unreal.AnimPoseExtensions.get_bone_pose(pose, n, unreal.AnimPoseSpaces.WORLD).translation
    hips = yaw(g(names[0]), g(names[1])); sh = yaw(g(names[2]), g(names[3])); head = g(names[4])
    unreal.log("TWIST %s hipline=%.1f shoulderline=%.1f diff=%.1f" % (tag, hips, sh, sh - hips))
meas(unreal.load_asset("/Game/Characters/Mannequins/Anims/Unarmed/MM_Idle"), ("thigh_l", "thigh_r", "clavicle_l", "clavicle_r", "head"), "Manny MM_Idle")
for ch in ("Static", "Rhodes"):
    meas(unreal.load_asset("/Game/Characters/NPCs/%s/Retargeted/Loco_Idle_%s" % (ch, ch)), ("LeftUpLeg", "RightUpLeg", "LeftShoulder", "RightShoulder", "Head"), ch + " idle")
    sk = unreal.load_asset("/Game/Characters/NPCs/%s/SKN_%s" % (ch, ch))
    pose = unreal.AnimPoseExtensions.get_reference_pose(sk.skeleton)
    g = lambda n: unreal.AnimPoseExtensions.get_bone_pose(pose, n, unreal.AnimPoseSpaces.WORLD).translation
    unreal.log("TWIST %s REF hipline=%.1f shoulderline=%.1f" % (ch, yaw(g("LeftUpLeg"), g("RightUpLeg")), yaw(g("LeftShoulder"), g("RightShoulder"))))
open("X:/IronBreach/Saved/run_done.txt","w").write("ok"); unreal.SystemLibrary.quit_editor()
