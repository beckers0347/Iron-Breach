"""
IBPY: ib_fix_building_collision.py -- diagnose + fix collision on the Barracks (and Hangar).

  py "X:/IronBreach/Scripts/ib_fix_building_collision.py"

For each building mesh it logs: convex hull count (expected: Barracks 11, Hangar 13), collision complexity, and the
placed actors' collision settings. Then it fixes:
  * hulls missing/short  -> Collision Complexity = Use Complex Collision As Simple (walls/roof block; floor stays open)
  * actors tagged IB_Barracks02 / IB_Hangar04 -> collision enabled, profile BlockAll, queries+physics on
Set FORCE_COMPLEX = True to use complex collision even when hulls exist (if you still walk through walls).
Nothing is saved: File > Save All afterwards, then test in PIE (walk into every wall, then through each door).
"""
import unreal

FORCE_COMPLEX = False
BUILDINGS = [
    ("/Game/Buildings/Barracks_02/Static/SM_Barracks_02", 11, "IB_Barracks02"),
    ("/Game/Buildings/Hangar_04/Static/SM_Hangar_04", 13, "IB_Hangar04"),
]


def log(m): unreal.log(f"IBPY: {m}")
def warn(m): unreal.log_warning(f"IBPY: WARNING -- {m}")


actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
for path, expect, tag in BUILDINGS:
    mesh = unreal.EditorAssetLibrary.load_asset(path)
    if not mesh:
        log(f"{path}: not found, skipping")
        continue
    bs = mesh.get_editor_property("body_setup")
    agg = bs.get_editor_property("agg_geom")
    hulls = len(agg.get_editor_property("convex_elems"))
    flag = bs.get_editor_property("collision_trace_flag")
    log(f"{mesh.get_name()}: hulls {hulls}/{expect}, complexity {flag}")
    if FORCE_COMPLEX or hulls < expect:
        bs.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
        mesh.modify()
        log(f"  -> set to Use Complex Collision As Simple ({'forced' if FORCE_COMPLEX else 'hulls missing'})")
    else:
        bs.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_SIMPLE_AND_COMPLEX)
        log("  -> hulls OK, complexity = Project Default / Simple And Complex")
    n = 0
    for a in actors:
        if tag in [str(t) for t in a.tags] and isinstance(a, unreal.StaticMeshActor):
            if a.static_mesh_component.static_mesh != mesh:
                continue
            a.set_actor_enable_collision(True)
            c = a.static_mesh_component
            try:
                c.set_collision_profile_name("BlockAll")
                c.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
            except Exception as e:
                warn(f"  could not set profile on '{a.get_actor_label()}': {e}")
            log(f"  actor '{a.get_actor_label()}': collision enabled, BlockAll")
            n += 1
    if not n:
        warn(f"  no placed actor with tag {tag} found for this mesh (asset fixed only)")
log("DONE. File > Save All, then test in PIE.")
