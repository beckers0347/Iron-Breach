import unreal

PREFIX = "08_Command & Comms_Collision"

def log(msg):
    unreal.log(f"IBPY: {msg}")

def main():
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    all_actors = subsystem.get_all_level_actors()
    deleted = 0
    for a in all_actors:
        label = a.get_actor_label()
        if label.startswith(PREFIX):
            ok = subsystem.destroy_actor(a)
            if ok:
                deleted += 1
                log(f"Deleted: {label}")
    log(f"Total deleted: {deleted}")
    log("Done.")

main()
