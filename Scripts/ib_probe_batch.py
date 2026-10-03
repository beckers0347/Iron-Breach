import unreal
for fn in ("duplicate_and_retarget", "run_batch_retarget"):
    f = getattr(unreal.IKRetargetBatchOperation, fn)
    unreal.log("BATCH %s doc: %s" % (fn, f.__doc__))
open("X:/IronBreach/Saved/run_done.txt","w").write("ok"); unreal.SystemLibrary.quit_editor()
