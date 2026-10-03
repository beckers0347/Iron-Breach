import unreal
for p in ("SK_Idris_Own", "Ms_Idris_Infantry"):
    m = unreal.load_asset("/Game/Characters/NPCs/MsIdris/" + p)
    unreal.log("MATP %s %s" % (p, [ (str(s.get_editor_property("material_slot_name")), s.get_editor_property("material_interface").get_path_name() if s.get_editor_property("material_interface") else None) for s in m.get_editor_property("materials")]))
open("X:/IronBreach/Saved/run_done.txt","w").write("ok"); unreal.SystemLibrary.quit_editor()
