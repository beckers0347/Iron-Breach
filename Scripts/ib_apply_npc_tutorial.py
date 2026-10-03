import unreal, runpy, traceback
LEVEL = "/Game/_GarrisonPreview_Disposable/CarrowGateGarrison_BoulderShore3"
try:
    unreal.EditorLoadingAndSavingUtils.load_map(LEVEL)
    runpy.run_path("X:/IronBreach/Scripts/ib_fix_npc_tutorial.py", run_name="__main__")
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    assert "BoulderShore3" in w.get_path_name()
    unreal.log("APPLY saved=%s" % unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level())
except BaseException:
    unreal.log_error("APPLY FAIL " + traceback.format_exc())
open("X:/IronBreach/Saved/apply_done.txt", "w").write("ok")
unreal.SystemLibrary.quit_editor()
