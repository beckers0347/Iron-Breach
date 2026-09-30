import unreal

TARGETS_EXACT = [
    "SM_MessHall_Tripo", "06_Mess Hall_DoorFrame",
]
PREFIXES = ["06_Mess Hall_Collision"]

def log(msg):
    unreal.log(f"IBPY: {msg}")

def main():
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    all_actors = subsystem.get_all_level_actors()
    for a in all_actors:
        label = a.get_actor_label()
        if label in TARGETS_EXACT or any(label.startswith(p) for p in PREFIXES):
            loc = a.get_actor_location()
            rot = a.get_actor_rotation()
            scale = a.get_actor_scale3d()
            log(f"[{a.get_class().get_name()}] {label}  loc=({loc.x:.1f},{loc.y:.1f},{loc.z:.1f}) rot=({rot.roll:.2f},{rot.pitch:.2f},{rot.yaw:.2f}) scale=({scale.x:.2f},{scale.y:.2f},{scale.z:.2f})")

    for label in ["SM_MessHall_Tripo"]:
        for a in all_actors:
            if a.get_actor_label() == label:
                mesh_comp = getattr(a, "static_mesh_component", None) or a.get_component_by_class(unreal.StaticMeshComponent)
                if mesh_comp:
                    lmin, lmax = mesh_comp.get_local_bounds()
                    log(f"[{label}] local_min={lmin} local_max={lmax}")
    log("Done.")

main()
