import unreal

def log(msg):
    unreal.log(f"IBPY: {msg}")

es = unreal.EditorActorSubsystem()
actors = es.get_all_level_actors()

BUILDINGS = [
    "04_Watch Tower",
    "05_Barracks",
    "06_Mess Hall",
    "07_Armory",
    "08_Command & Comms",
    "09_Sensor Array",
]

for prefix in BUILDINGS:
    matches = [a for a in actors if a.get_actor_label().startswith(prefix)]
    cube_count = 0
    dynmesh_count = 0
    other_count = 0
    has_roof = False
    for a in matches:
        label = a.get_actor_label().lower()
        if "roof" in label:
            has_roof = True
        try:
            dcomps = a.get_components_by_class(unreal.DynamicMeshComponent)
        except Exception:
            dcomps = []
        if dcomps:
            dynmesh_count += 1
            continue
        try:
            comps = a.get_components_by_class(unreal.StaticMeshComponent)
            is_cube = any(c.static_mesh and c.static_mesh.get_name() == "Cube" for c in comps)
        except Exception:
            is_cube = False
        if is_cube:
            cube_count += 1
        else:
            other_count += 1
    log(f"{prefix}: total={len(matches)} cube_primitives={cube_count} dynamic_mesh={dynmesh_count} other={other_count} has_roof_named_actor={has_roof}")
log("=== done ===")
