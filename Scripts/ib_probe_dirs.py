import unreal
unreal.EditorLoadingAndSavingUtils.load_map("/Game/_GarrisonPreview_Disposable/CarrowGateGarrison_BoulderShore3")
P = lambda s: unreal.log("DIRPROBE " + s)
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    c = a.get_class().get_name()
    if c in ("IBGuideRoute",) or (c.startswith("Act") and "Director" in c) or "M1" in a.get_actor_label():
        vals = []
        for p in ("auto_start", "start_after_act1", "start_delay_seconds", "initial_delay", "guide_actor", "pull_player", "leash_distance_cm", "facing_yaw_offset"):
            try: vals.append("%s=%s" % (p, a.get_editor_property(p)))
            except Exception: pass
        P("%s [%s] %s" % (a.get_actor_label(), c, " ".join(vals)))
        if c == "IBGuideRoute":
            for i, w in enumerate(a.get_editor_property("waypoints")):
                P("   WP%d %s" % (i, w.get_editor_property("location")))
open("X:/IronBreach/Saved/dirprobe_done.txt", "w").write("ok")
unreal.SystemLibrary.quit_editor()
