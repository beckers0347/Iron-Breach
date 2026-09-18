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
    a = get_actor_by_label("SM_MessHall_Tripo")
    if not a:
        log("SM_MessHall_Tripo not found")
        return
    origin, extent = a.get_actor_bounds(False)
    log(f"get_actor_bounds(False): origin={origin} extent={extent}")
    origin2, extent2 = a.get_actor_bounds(True)
    log(f"get_actor_bounds(True): origin={origin2} extent={extent2}")

    comp = getattr(a, "static_mesh_component", None) or a.get_component_by_class(unreal.StaticMeshComponent)
    b = comp.bounds
    log(f"comp.bounds: origin={b.origin} box_extent={b.box_extent} sphere_radius={b.sphere_radius}")

    lmin, lmax = comp.get_local_bounds()
    log(f"comp.get_local_bounds(): local_min={lmin} local_max={lmax}")

    log("Done.")

main()
