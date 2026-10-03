import unreal, runpy, traceback, os
LEVEL = "/Game/_GarrisonPreview_Disposable/CarrowGateGarrison_BoulderShore3"
try:
    unreal.EditorLoadingAndSavingUtils.load_map(LEVEL)
    runpy.run_path(os.environ["IB_SCRIPT"], run_name="__main__")
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    assert "BoulderShore3" in w.get_path_name()
    unreal.log("APPLY saved=%s" % unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level())
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
except BaseException:
    unreal.log_error("APPLY FAIL " + traceback.format_exc())
open("X:/IronBreach/Saved/apply_done.txt", "w").write("ok")
unreal.SystemLibrary.quit_editor()
