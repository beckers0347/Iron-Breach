import unreal
unreal.EditorLoadingAndSavingUtils.load_map("/Game/_GarrisonPreview_Disposable/CarrowGateGarrison_BoulderShore3")
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    if a.get_actor_label().startswith("NPC_"):
        c = a.skeletal_mesh_component
        o, e = a.get_actor_bounds(False)
        unreal.log("NPCPROBE %s loc=%s rot=%s hiddenGame=%s visible=%s relRot=%s boundsCenter=(%d,%d,%d) ext=(%d,%d,%d) tags=%s" % (
            a.get_actor_label(), a.get_actor_location(), a.get_actor_rotation(), a.get_editor_property("hidden"), c.get_editor_property("visible"),
            c.relative_rotation, o.x, o.y, o.z, e.x, e.y, e.z, [str(t) for t in a.tags]))
open("X:/IronBreach/Saved/probe_done.txt","w").write("ok")
unreal.SystemLibrary.quit_editor()
