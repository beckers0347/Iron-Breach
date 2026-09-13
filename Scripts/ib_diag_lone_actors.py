import unreal
def log(msg):
    unreal.log(f"IBPY: {msg}")
es = unreal.EditorActorSubsystem()
actors = es.get_all_level_actors()
for prefix in ["06_Mess Hall", "07_Armory", "08_Command & Comms"]:
    matches = [a for a in actors if a.get_actor_label().startswith(prefix)]
    for a in matches:
        log(f"{prefix}: lone actor = {a.get_actor_label()} ({a.get_class().get_name()}) loc={a.get_actor_location()}")

# Check world partition state
world = unreal.EditorLevelLibrary.get_editor_world() if hasattr(unreal, "EditorLevelLibrary") else None
log(f"world = {world}")
try:
    wp_sub = unreal.get_editor_subsystem(unreal.WorldPartitionSubsystem)
    log(f"WorldPartitionSubsystem = {wp_sub}")
except Exception as e:
    log(f"no WorldPartitionSubsystem: {e}")
log("=== done ===")
