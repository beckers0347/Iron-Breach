import unreal

def log(msg):
    unreal.log(f"IBPY: {msg}")

def main():
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    all_actors = subsystem.get_all_level_actors()
    for a in all_actors:
        label = a.get_actor_label()
        if label == "SM_Command_Tripo" or label.startswith("08_Command & Comms_Collision"):
            loc = a.get_actor_location()
            rot = a.get_actor_rotation()
            scale = a.get_actor_scale3d()
            log(f"[{a.get_class().get_name()}] {label}  loc=({loc.x:.1f},{loc.y:.1f},{loc.z:.1f}) rot=({rot.roll:.2f},{rot.pitch:.2f},{rot.yaw:.2f}) scale=({scale.x:.1f},{scale.y:.1f},{scale.z:.1f})")
    log("Done.")

main()
