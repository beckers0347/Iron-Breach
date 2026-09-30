import unreal
def log(msg):
    unreal.log(f"IBPY: {msg}")

es = unreal.EditorActorSubsystem()
actors = es.get_all_level_actors()

# name-based search, case-insensitive, no location restriction
hits = [a for a in actors if "messhall" in a.get_actor_label().lower().replace(" ", "")]
log(f"=== name-match 'messhall' (any spacing): {len(hits)} actors ===")
for a in sorted(hits, key=lambda x: x.get_actor_label()):
    log(f"  {a.get_actor_label()} ({a.get_class().get_name()}) loc={a.get_actor_location()}")

# also widen radius search around the doorframe location
center = unreal.Vector(3000.0, 7806.5, 500.0)
for radius in [3000.0, 6000.0]:
    near = [a for a in actors if ((a.get_actor_location().x-center.x)**2 + (a.get_actor_location().y-center.y)**2)**0.5 <= radius]
    log(f"=== within {radius}cm of Mess Hall door: {len(near)} actors ===")
log("=== done ===")
