import unreal
P = lambda s: unreal.log("ANIMPROBE " + s)
bs = unreal.load_asset("/Game/Characters/NPCs/Shared/BS_NPC_Unarmed_Locomotion")
try:
    samples = bs.get_editor_property("sample_data")
    for s in samples:
        a = s.get_editor_property("animation")
        P("BS sample %s value=%s" % (a.get_path_name() if a else None, s.get_editor_property("sample_value")))
        if a:
            P("   enable_root_motion=%s force_root_lock=%s length=%.2f" % (a.get_editor_property("enable_root_motion"), a.get_editor_property("force_root_lock"), a.get_editor_property("sequence_length")))
            try:
                opts = unreal.AnimPoseEvaluationOptions()
                for t in (0.0, a.get_editor_property("sequence_length") * 0.5, a.get_editor_property("sequence_length") - 0.01):
                    pose = unreal.AnimPoseExtensions.get_anim_pose_at_time(a, t, opts)
                    names = unreal.AnimPoseExtensions.get_bone_names(pose)
                    root = names[0]
                    tr = unreal.AnimPoseExtensions.get_bone_pose(pose, root, unreal.AnimPoseSpaces.WORLD)
                    pel = unreal.AnimPoseExtensions.get_bone_pose(pose, names[1], unreal.AnimPoseSpaces.WORLD)
                    P("   t=%.2f root(%s)=%s  %s=%s" % (t, root, tr.translation, names[1], pel.translation))
            except Exception as e:
                P("   pose err %r" % e)
except Exception as e:
    P("bs err %r" % e)
abp = unreal.load_asset("/Game/Characters/NPCs/Shared/ABP_NPC_Locomotion")
try:
    cdo = unreal.get_default_object(abp.generated_class())
    P("ABP root_motion_mode=%s" % cdo.get_editor_property("root_motion_mode"))
except Exception as e:
    P("abp err %r" % e)
m = unreal.load_asset("/Game/Characters/NPCs/MsIdris/Ms_Idris_Infantry")
try:
    opts = unreal.AnimPoseEvaluationOptions()
    pose = unreal.AnimPoseExtensions.get_reference_pose(m.skeleton)
    for b in ("foot_l", "ball_l", "foot_r", "ball_r", "head", "pelvis"):
        try:
            P("REF %s=%s" % (b, unreal.AnimPoseExtensions.get_bone_pose(pose, b, unreal.AnimPoseSpaces.WORLD).translation))
        except Exception as e:
            P("REF %s err %r" % (b, e))
except Exception as e:
    P("ref err %r" % e)
unreal.EditorLoadingAndSavingUtils.load_map("/Game/_GarrisonPreview_Disposable/CarrowGateGarrison_BoulderShore3")
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    c = a.get_class().get_name()
    if c == "IBGuideRoute":
        g = a.get_editor_property("guide_actor"); f = a.get_editor_property("followers")
        P("ROUTE guide=%s followers=%s auto=%s afterAct1=%s yawoff=%s speed=%s debug=%s" % (g, [str(x) for x in f], a.get_editor_property("b_auto_start"), a.get_editor_property("start_after_act1"), a.get_editor_property("facing_yaw_offset"), a.get_editor_property("walk_speed"), a.get_editor_property("b_debug_draw")))
        for i, w in enumerate(a.get_editor_property("waypoints")):
            P("  WP%d %s wait=%s tag=%s line=%s" % (i, w.get_editor_property("location"), w.get_editor_property("wait_for_player_radius"), w.get_editor_property("arrival_event_tag"), w.get_editor_property("arrival_line").get_editor_property("text")))
    if c.startswith("Act") and "Director" in c:
        props = [p for p in ("squad_npcs", "district_npcs", "b_auto_start", "start_after_act1", "start_after") ]
        out = []
        for p in ("squad_npcs", "district_npcs", "b_auto_start"):
            try: out.append("%s=%s" % (p, [str(x) for x in a.get_editor_property(p)] if p != "b_auto_start" else a.get_editor_property(p)))
            except Exception: pass
        P("DIR %s %s" % (c, " ".join(out)))
    if c == "PlayerStart":
        P("PLAYERSTART %s %s" % (a.get_actor_location(), a.get_actor_rotation()))
open("X:/IronBreach/Saved/animprobe_done.txt","w").write("ok")
unreal.SystemLibrary.quit_editor()
