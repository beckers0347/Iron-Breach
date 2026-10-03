import unreal, runpy
g = runpy.run_path("X:/IronBreach/Scripts/ib_rescale_idris_infantry.py", run_name="__main__")
m = unreal.load_asset("/Game/Characters/NPCs/MsIdris/Ms_Idris_Infantry")
b = m.get_bounds()
unreal.log("NPCFIX origin=%s ext=%s skel=%s" % (b.origin, b.box_extent, m.skeleton.get_name()))
unreal.EditorAssetLibrary.save_asset("/Game/Characters/NPCs/MsIdris/Ms_Idris_Infantry")
open("X:/IronBreach/Saved/npcfix_done.txt", "w").write("ok")
unreal.SystemLibrary.quit_editor()
