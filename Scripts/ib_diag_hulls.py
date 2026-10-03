import unreal, sys
sys.path.insert(0, "X:/IronBreach/Scripts")
src = open("X:/IronBreach/Scripts/ib_replace_garrison_buildings.py").read().split("\ndef main():")[0]
ns = {"__name__": "ib_diag", "__file__": "X:/IronBreach/Scripts/ib_replace_garrison_buildings.py"}
exec(compile(src, "ibrep", "exec"), ns)
imp = ns["import_fbx"]
for tag, path in (("Barracks", "X:/IronBreach/SourceArt/Barracks_02/SM_Barracks_02.fbx"), ("Armory", "X:/IronBreach/SourceArt/Carrowgate/Armory/SM_Armory.fbx")):
    assets = imp(path, "/Game/_DiagTmp/" + tag, "SM_" + tag, False)
    for a in assets:
        if isinstance(a, unreal.StaticMesh):
            unreal.log("HULLDIAG %s hulls=%d" % (tag, unreal.EditorStaticMeshLibrary.get_convex_collision_count(a)))
            bs = a.get_editor_property("body_setup")
            unreal.log("HULLDIAG %s collision_trace_flag=%s" % (tag, bs.get_editor_property("collision_trace_flag")))
open("X:/IronBreach/Saved/diag_done.txt", "w").write("ok")
unreal.SystemLibrary.quit_editor()
