import unreal
P = unreal.log
def asset(p):
    try: return unreal.EditorAssetLibrary.load_asset(p)
    except Exception as e: P("NPCDIAG load fail %s %r" % (p, e)); return None
for p in ("/Game/Characters/NPCs/MsIdris/Ms_Idris_Infantry", "/Game/Characters/NPCs/MsIdris/Ms_Idris_Fixed", "/Game/Characters/NPCs/MsIdris/Ms_Idris_wSkeleton"):
    m = asset(p)
    if not m: P("NPCDIAG missing " + p); continue
    P("NPCDIAG %s class=%s" % (p, m.get_class().get_name()))
    try:
        b = m.get_bounds(); P("NPCDIAG   bounds origin=%s extent=%s" % (b.origin, b.box_extent))
        sk = m.get_editor_property("skeleton"); P("NPCDIAG   skeleton=%s" % (sk.get_path_name() if sk else None))
        P("NPCDIAG   bones=%d" % m.skeleton.get_reference_pose().__len__() if False else "NPCDIAG   n/a")
        P("NPCDIAG   imported_bounds=%s" % (m.get_imported_bounds(),))
    except Exception as e: P("NPCDIAG   err %r" % e)
abp = asset("/Game/Characters/NPCs/Shared/ABP_NPC_Locomotion")
if abp:
    P("NPCDIAG ABP class=%s skeleton=%s" % (abp.get_class().get_name(), abp.get_editor_property("target_skeleton").get_path_name() if abp.get_editor_property("target_skeleton") else None))
bs = asset("/Game/Characters/NPCs/Shared/BS_NPC_Unarmed_Locomotion")
if bs: P("NPCDIAG BS skeleton=%s" % (bs.get_editor_property("skeleton").get_path_name() if bs.get_editor_property("skeleton") else None))
inf = asset("/Game/Characters/Infantry")  
open("X:/IronBreach/Saved/npcdiag_done.txt","w").write("ok")
unreal.SystemLibrary.quit_editor()
