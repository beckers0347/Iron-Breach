"""
Diagnostic: dump actor state for 04_Watch Tower and 09_Sensor Array after the
Aura conversion pass, to check Shane's report that the level looks unchanged
except roof differences, and that Watch Tower lost roof access.

Run: exec(open(r"X:\IronBreach\Scripts\ib_diag_watchtower_sensorarray.py").read())
"""
import unreal

def log(msg):
    unreal.log(f"IBPY: {msg}")

es = unreal.EditorActorSubsystem()
actors = es.get_all_level_actors()

def dump(prefix):
    matches = [a for a in actors if a.get_actor_label().startswith(prefix)]
    log(f"=== {prefix} -> {len(matches)} actors ===")
    for a in sorted(matches, key=lambda x: x.get_actor_label()):
        label = a.get_actor_label()
        cls = a.get_class().get_name()
        loc = a.get_actor_location()
        vis = a.is_hidden_ed() if hasattr(a, "is_hidden_ed") else "?"
        mesh_info = ""
        try:
            comps = a.get_components_by_class(unreal.StaticMeshComponent)
            for c in comps:
                sm = c.static_mesh
                mesh_info += f" [SM:{sm.get_name() if sm else None}]"
        except Exception:
            pass
        try:
            dcomps = a.get_components_by_class(unreal.DynamicMeshComponent)
            if dcomps:
                mesh_info += f" [DynamicMesh x{len(dcomps)}]"
        except Exception:
            pass
        log(f"  {label} ({cls}) loc={loc} hidden={vis}{mesh_info}")

dump("04_Watch Tower")
dump("09_Sensor Array")
log("=== done ===")
