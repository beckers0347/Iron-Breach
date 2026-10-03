import unreal
for p in ("/Game/Buildings/Barracks_02/Static/SM_Barracks_02", "/Game/Buildings/Hangar_04/Static/SM_Hangar_04", "/Game/IronBreach/Thornfield/Meshes/BermBunker/SM_BermBunker"):
    a = unreal.EditorAssetLibrary.load_asset(p)
    if a:
        unreal.log("HULLDIAG saved %s hulls=%d" % (p.split('/')[-1], unreal.EditorStaticMeshLibrary.get_convex_collision_count(a)))
    else:
        unreal.log("HULLDIAG missing " + p)
open("X:/IronBreach/Saved/diag_done.txt", "w").write("ok")
unreal.SystemLibrary.quit_editor()
