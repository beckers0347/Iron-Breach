import unreal
def log(msg):
    unreal.log(f"IBPY: {msg}")

es = unreal.EditorActorSubsystem()
actors = es.get_all_level_actors()
hits = [a for a in actors if "sensorarray" in a.get_actor_label().lower().replace(" ", "") or a.get_actor_label().startswith("09_Sensor Array")]
log(f"=== name-match sensor array: {len(hits)} actors ===")
for a in sorted(hits, key=lambda x: x.get_actor_label()):
    origin, extent = a.get_actor_bounds(only_colliding_components=False)
    log(f"  {a.get_actor_label()} ({a.get_class().get_name()}) loc={a.get_actor_location()} bounds_origin={origin} bounds_extent={extent}")
log("=== done ===")
