"""
IBPY: ib_hangar_collision.py -- checks SM_Hangar_04's collision and fixes it if the UCX hulls did not import.

  py "X:/IronBreach/Scripts/ib_hangar_collision.py"

1. Reloads /Game/Buildings/Hangar_04/Static/SM_Hangar_04 and counts convex hulls (expect 13).
2. If there are none, sets Collision Complexity = "Use Complex Collision As Simple" so the walls/roof still block
   (heavier than hulls, fine for one building). The floor stays open either way: the mesh has no floor.
Nothing is saved: File > Save All afterwards.
"""
import unreal

PATH = "/Game/Buildings/Hangar_04/Static/SM_Hangar_04"


def log(m): unreal.log(f"IBPY: {m}")


mesh = unreal.EditorAssetLibrary.load_asset(PATH)
if not mesh:
    unreal.log_error(f"IBPY: ERROR -- {PATH} not found")
else:
    bs = mesh.get_editor_property("body_setup")
    agg = bs.get_editor_property("agg_geom")
    hulls = len(agg.get_editor_property("convex_elems"))
    boxes = len(agg.get_editor_property("box_elems"))
    log(f"{mesh.get_name()}: convex hulls {hulls}, boxes {boxes}, trace flag {bs.get_editor_property('collision_trace_flag')}")
    if hulls >= 13:
        log("UCX hulls present -- nothing to fix.")
    else:
        bs.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
        mesh.modify()
        log("no usable hulls -> set Collision Complexity to 'Use Complex Collision As Simple'. Save All, then test walking into a wall in PIE.")
