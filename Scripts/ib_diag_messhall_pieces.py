import unreal

def log(msg):
    unreal.log(f"IBPY: {msg}")

def main():
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    all_actors = subsystem.get_all_level_actors()
    for a in all_actors:
        label = a.get_actor_label()
        folder = str(a.get_folder_path())
        if "Mess Hall" in folder or "MessHall" in label or label.startswith("06_"):
            loc = a.get_actor_location()
            cls = a.get_class().get_name()
            comp = getattr(a, "static_mesh_component", None) or a.get_component_by_class(unreal.StaticMeshComponent)
            bounds_str = ""
            if comp:
                try:
                    lmin, lmax = comp.get_local_bounds()
                    bounds_str = f" local_min={lmin} local_max={lmax}"
                except Exception as e:
                    bounds_str = f" (bounds err: {e})"
            log(f"[{cls}] label='{label}' folder='{folder}' loc=({loc.x:.1f},{loc.y:.1f},{loc.z:.1f}){bounds_str}")
    log("Done.")

main()
