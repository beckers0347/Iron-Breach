import unreal
def log(msg):
    unreal.log(f"IBPY: {msg}")
es = unreal.EditorActorSubsystem()
actors = es.get_all_level_actors()
a = next((x for x in actors if x.get_actor_label() == "WatchTowerShaft_Wall_S_01"), None)
if a:
    es.set_selected_level_actors([a])
    origin, extent = a.get_actor_bounds(only_colliding_components=False)
    log(f"selected {a.get_actor_label()} loc={a.get_actor_location()} bounds_origin={origin} bounds_extent={extent}")
else:
    log("NOT FOUND")
log("=== done ===")
