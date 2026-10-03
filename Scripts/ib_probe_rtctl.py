import unreal
c = unreal.IKRetargeterController
for fn in ("add_default_ops", "assign_ik_rig_to_all_ops", "auto_map_chains", "auto_align_all_bones", "get_num_retarget_ops", "add_retarget_op"):
    f = getattr(c, fn)
    unreal.log("RTC %s: %s" % (fn, (f.__doc__ or "")[:260].replace("\n", " | ")))
open("X:/IronBreach/Saved/run_done.txt","w").write("ok"); unreal.SystemLibrary.quit_editor()
