import unreal
opts = unreal.AnimPoseEvaluationOptions()
for n in ("Loco_Idle_Idris", "Loco_Walking_Idris"):
    a = unreal.load_asset("/Game/Characters/NPCs/MsIdris/Retargeted/" + n)
    L = a.get_editor_property("sequence_length")
    unreal.log("RTP %s len=%.2f skeleton=%s frames=%s" % (n, L, a.get_editor_property("skeleton").get_name() if a.get_editor_property("skeleton") else None, a.get_number_of_sampled_keys() if hasattr(a, "get_number_of_sampled_keys") else "?"))
    for t in (0.0, L * 0.25, L * 0.5, L * 0.75):
        opts.set_editor_property("extract_root_motion", False) if False else None
        pose = unreal.AnimPoseExtensions.get_anim_pose_at_time(a, t, opts)
        names = [str(x) for x in unreal.AnimPoseExtensions.get_bone_names(pose)]
        def tr(b):
            return unreal.AnimPoseExtensions.get_bone_pose(pose, b, unreal.AnimPoseSpaces.WORLD).translation
        hips, lf, rh = tr("Hips"), tr("LeftFoot"), tr("RightHand")
        unreal.log("RTP   t=%.2f Hips=(%.0f,%.0f,%.0f) LFoot=(%.0f,%.0f,%.0f) RHand=(%.0f,%.0f,%.0f)" % (t, hips.x, hips.y, hips.z, lf.x, lf.y, lf.z, rh.x, rh.y, rh.z))
sk = unreal.load_asset("/Game/Characters/NPCs/MsIdris/SK_Idris_Own")
pose = unreal.AnimPoseExtensions.get_reference_pose(sk.skeleton)
names = [str(x) for x in unreal.AnimPoseExtensions.get_bone_names(pose)]
unreal.log("RTP ref bones %s" % names[:10])
t = unreal.AnimPoseExtensions.get_bone_pose(pose, "Hips", unreal.AnimPoseSpaces.WORLD).translation
unreal.log("RTP ref Hips=(%.0f,%.0f,%.0f)" % (t.x, t.y, t.z))
open("X:/IronBreach/Saved/run_done.txt","w").write("ok"); unreal.SystemLibrary.quit_editor()
