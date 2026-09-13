import unreal
def log(msg):
    unreal.log(f"IBPY: {msg}")
es = unreal.EditorActorSubsystem()
actors = es.get_all_level_actors()
targets = [a for a in actors if "watchtower" in a.get_actor_label().lower().replace(" ", "").replace("_","") or a.get_actor_label().startswith("04_Watch Tower")]
log(f"selecting {len(targets)} watch tower actors")
es.set_selected_level_actors(targets)
log("=== done ===")
