import unreal, runpy, traceback, json
LEVEL = "/Game/_GarrisonPreview_Disposable/CarrowGateGarrison_BoulderShore3"
HEAD = open("X:/IronBreach/Scripts/ib_replace_garrison_buildings.py").read().split("\ndef main():")[0]
for nm in ("Armory", "Medical", "Command", "MessHall", "MainGate"):
    d = "/Game/Buildings/%s/Doors" % nm
    try:
        if unreal.EditorAssetLibrary.does_directory_exist(d):
            unreal.EditorAssetLibrary.delete_directory(d)       # fresh door assets; the level's old spawns are replaced below
            unreal.log("APPLY cleared " + d)
    except BaseException:
        unreal.log_error("APPLY CLEAR FAIL " + d + traceback.format_exc())
try:
    unreal.EditorLoadingAndSavingUtils.load_map(LEVEL)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    assert "BoulderShore3" in world.get_path_name(), world.get_path_name()
    g = runpy.run_path("X:/IronBreach/Scripts/ib_replace_garrison_buildings.py", run_name="__main__")
    assert not g.get("FAILED"), "replace script reported errors - level NOT saved"
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    assert "BoulderShore3" in world.get_path_name()
    r1 = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    r2 = unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    unreal.log("APPLY saved level=%s dirty=%s" % (r1, r2))
except BaseException:
    unreal.log_error("APPLY FAIL " + traceback.format_exc())
open("X:/IronBreach/Saved/apply_done.txt", "w").write("ok")
unreal.SystemLibrary.quit_editor()
