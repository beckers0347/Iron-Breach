import unreal

def log(msg):
    unreal.log(f"IBPY: {msg}")

def main():
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    all_actors = subsystem.get_all_level_actors()
    for a in all_actors:
        label = a.get_actor_label()
        if "Tripo" in label or "_Tripo" in label:
            loc = a.get_actor_location()
            comp = getattr(a, "static_mesh_component", None) or a.get_component_by_class(unreal.StaticMeshComponent)
            mesh_name = ""
            if comp:
                sm = comp.get_editor_property("static_mesh")
                mesh_name = sm.get_name() if sm else "None"
            folder = str(a.get_folder_path())
            log(f"label='{label}' mesh='{mesh_name}' folder='{folder}' loc=({loc.x:.1f},{loc.y:.1f},{loc.z:.1f})")
    log("Done.")

main()
