import unreal, os, runpy, traceback
unreal.EditorLoadingAndSavingUtils.load_map("/Game/IronBreach/Thornfield/Levels/L_ThornfieldGarrison")
S = os.environ.get("IB_GEN_SCRIPTS", "").split(",")
for s in [x for x in S if x]:
    p = "X:/IronBreach/LevelGenTools/scripts/%s.py" % s
    unreal.log("RUNGEN start " + s)
    try:
        runpy.run_path(p, run_name="__main__")
        unreal.log("RUNGEN ok " + s)
    except BaseException:
        unreal.log_error("RUNGEN FAIL " + s + "\n" + traceback.format_exc())
open("X:/IronBreach/Saved/rungen_done.txt", "w").write("done")
unreal.SystemLibrary.quit_editor()
