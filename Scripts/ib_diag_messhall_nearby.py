import unreal
import math

CENTER_X, CENTER_Y = 3000.0, 8556.5
RADIUS = 2500.0

def log(msg):
    unreal.log(f"IBPY: {msg}")

def main():
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    all_actors = subsystem.get_all_level_actors()
    count = 0
    for a in all_actors:
        loc = a.get_actor_location()
        d = math.hypot(loc.x - CENTER_X, loc.y - CENTER_Y)
        if d <= RADIUS:
            label = a.get_actor_label()
            cls = a.get_class().get_name()
            folder = str(a.get_folder_path())
            scale = a.get_actor_scale3d()
            comp = getattr(a, "static_mesh_component", None) or a.get_component_by_class(unreal.StaticMeshComponent)
            mesh_name = ""
            bounds_str = ""
            if comp:
                sm = comp.get_editor_property("static_mesh")
                mesh_name = sm.get_name() if sm else "None"
                try:
                    lmin, lmax = comp.get_local_bounds()
                    bounds_str = f" mesh_local_min={lmin} mesh_local_max={lmax}"
                except Exception as e:
                    bounds_str = f" (bounds err: {e})"
            log(f"d={d:.0f} [{cls}] label='{label}' folder='{folder}' mesh='{mesh_name}' loc=({loc.x:.1f},{loc.y:.1f},{loc.z:.1f}) scale=({scale.x:.2f},{scale.y:.2f},{scale.z:.2f}){bounds_str}")
            count += 1
    log(f"Total nearby actors: {count}")
    log("Done.")

main()
