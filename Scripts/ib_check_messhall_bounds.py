import unreal
def log(msg):
    unreal.log(f"IBPY: {msg}")

es = unreal.EditorActorSubsystem()
actors = es.get_all_level_actors()
targets = [a for a in actors if a.get_actor_label() in ("06_MessHall_Model_Opaque", "06_MessHall_Model_Glass", "06_MessHall_ModelRoot")]
for a in targets:
    origin, extent = a.get_actor_bounds(only_colliding_components=False)
    log(f"{a.get_actor_label()}: transform_loc={a.get_actor_location()} bounds_origin={origin} bounds_extent={extent}")
log("=== done ===")
