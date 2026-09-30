import unreal

def log(msg):
    unreal.log(f"IBPY: {msg}")

def get_actor_by_label(label):
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for a in subsystem.get_all_level_actors():
        if a.get_actor_label() == label:
            return a
    return None

def main():
    exterior = get_actor_by_label("SM_Armory_Tripo")
    mesh_comp = getattr(exterior, "static_mesh_component", None) or exterior.get_component_by_class(unreal.StaticMeshComponent)
    log(f"Collision enabled before: {mesh_comp.get_collision_enabled()}")

    mesh_comp.set_collision_enabled(unreal.CollisionEnabled.QUERY_ONLY)
    log(f"Collision enabled after set: {mesh_comp.get_collision_enabled()}")

    world = unreal.EditorLevelLibrary.get_editor_world()
    actor_loc = exterior.get_actor_location()

    start = unreal.Vector(actor_loc.x, actor_loc.y, actor_loc.z + 300)
    end = unreal.Vector(actor_loc.x + 3000, actor_loc.y, actor_loc.z + 300)

    try:
        hit = unreal.SystemLibrary.line_trace_single(
            world, start, end,
            unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,
            True, [], unreal.DrawDebugTrace.NONE, True
        )
        log(f"line_trace_single result: {hit}")
        if hit:
            log(f"  to_dict: {hit.to_dict()}")
    except Exception as e:
        log(f"line_trace_single failed: {e}")

    # restore
    mesh_comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    log("Restored NO_COLLISION.")
    log("Done.")

main()
