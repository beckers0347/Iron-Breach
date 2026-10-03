import unreal, traceback
LEVEL = "/Game/_GarrisonPreview_Disposable/CarrowGateGarrison_BoulderShore3"
unreal.EditorLoadingAndSavingUtils.load_map(LEVEL)
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
assert "BoulderShore3" in world.get_path_name()
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
try:
    n = 0
    for a in list(EAS.get_all_level_actors()):
        if str(a.get_folder_path()).startswith("_Replaced_") and a.get_actor_label().endswith("_REPLACED"):
            unreal.log("REMOVE %s [%s]" % (a.get_actor_label(), a.get_folder_path()))
            EAS.destroy_actor(a); n += 1
    ok = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    unreal.log("REMOVED %d actors, saved=%s" % (n, ok))
except BaseException:
    unreal.log_error("REMOVE FAIL " + traceback.format_exc())
open("X:/IronBreach/Saved/remove_done.txt", "w").write("ok")
unreal.SystemLibrary.quit_editor()
