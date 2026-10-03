import unreal, math
opts = unreal.AnimPoseEvaluationOptions()
def yw(a, b): return math.degrees(math.atan2(b.y - a.y, b.x - a.x))
def rep(anim, n, tag):
    pose = unreal.AnimPoseExtensions.get_anim_pose_at_time(anim, 0.0, opts)
    g = lambda k: unreal.AnimPoseExtensions.get_bone_pose(pose, k, unreal.AnimPoseSpaces.WORLD).translation
    hip = yw(g(n["tl"]), g(n["tr"])); sh = yw(g(n["cl"]), g(n["cr"]))
    footL = yw(g(n["fl"]), g(n["bl"])); footR = yw(g(n["fr"]), g(n["br"]))
    head_fwd = None
    unreal.log("FEET %s hipline=%.0f shoulderline=%.0f  toeL=%.0f toeR=%.0f  (forward = hipline-90 = %.0f)" % (tag, hip, sh, footL, footR, hip - 90))
rep(unreal.load_asset("/Game/Characters/Mannequins/Anims/Unarmed/MM_Idle"),
    dict(tl="thigh_l", tr="thigh_r", cl="clavicle_l", cr="clavicle_r", fl="foot_l", bl="ball_l", fr="foot_r", br="ball_r"), "Manny")
for ch in ("Static", "Rhodes"):
    rep(unreal.load_asset("/Game/Characters/NPCs/%s/Retargeted/Loco_Idle_%s" % (ch, ch)),
        dict(tl="LeftUpLeg", tr="RightUpLeg", cl="LeftShoulder", cr="RightShoulder", fl="LeftFoot", bl="LeftToeBase", fr="RightFoot", br="RightToeBase"), ch)
open("X:/IronBreach/Saved/run_done.txt","w").write("ok"); unreal.SystemLibrary.quit_editor()
