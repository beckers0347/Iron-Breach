import unreal
opts = unreal.AnimPoseEvaluationOptions()
for ch in ("Idris", "Rhodes"):
    for kind in ("Idle", "Walking"):
        a = unreal.load_asset("/Game/Characters/NPCs/%s/Retargeted/Loco_%s_%s" % (ch, kind, ch))
        L = a.get_editor_property("sequence_length")
        rows = []
        for t in (0.0, L * 0.25, L * 0.5, L * 0.75):
            pose = unreal.AnimPoseExtensions.get_anim_pose_at_time(a, t, opts)
            g = lambda n: unreal.AnimPoseExtensions.get_bone_pose(pose, n, unreal.AnimPoseSpaces.WORLD).translation
            h, hd, lf, lh = g("Hips"), g("Head"), g("LeftFoot"), g("LeftHand")
            rows.append("H(%.0f,%.0f,%.0f) head z%.0f LF(%.0f,%.0f,%.0f) LH(%.0f,%.0f,%.0f)" % (h.x, h.y, h.z, hd.z, lf.x, lf.y, lf.z, lh.x, lh.y, lh.z))
        unreal.log("WALKP %s %s len=%.2f lock=%s :: %s" % (ch, kind, L, a.get_editor_property("force_root_lock"), " | ".join(rows)))
open("X:/IronBreach/Saved/run_done.txt","w").write("ok"); unreal.SystemLibrary.quit_editor()
