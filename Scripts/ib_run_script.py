import unreal, runpy, traceback, os
try:
    runpy.run_path(os.environ["IB_RUN"], run_name="__main__")
except BaseException:
    unreal.log_error("RUN FAIL " + traceback.format_exc())
open("X:/IronBreach/Saved/run_done.txt", "w").write("ok")
unreal.SystemLibrary.quit_editor()
