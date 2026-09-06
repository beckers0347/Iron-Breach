"""Read-only probe: what Water-plugin Python API exists in 5.8, and does a freshly spawned lake get info meshes? (no save)"""
import unreal, os
def log(m): unreal.log(f"IBPY: {m}")
LEVEL = os.environ.get("IB_LEVEL", "/Game/LevelPrototyping/CarrowGateGarrison")
names = sorted(n for n in dir(unreal) if "water" in n.lower())
log(f"unreal.* water names ({len(names)}): " + ", ".join(names))
for n in names:
    cls = getattr(unreal, n)
    try:
        ms = sorted(m for m in dir(cls) if not m.startswith("_") and m not in dir(unreal.Object) and m not in dir(unreal.Actor) and m not in dir(unreal.SceneComponent))
    except Exception:
        ms = []
    if ms: log(f"  {n}: " + ", ".join(ms)[:900])
unreal.EditorLoadingAndSavingUtils.load_map(LEVEL)
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
world = unreal.EditorLevelLibrary.get_editor_world()
for sub in ("WaterSubsystem",):
    try:
        s = unreal.get_editor_subsystem(getattr(unreal, sub)) if hasattr(unreal, sub) else None
        log(f"editor subsystem {sub}: {s}")
    except Exception as e: log(f"editor subsystem {sub}: {str(e)[:80]}")
try:
    ws = unreal.WaterSubsystem.get_water_subsystem(world) if hasattr(unreal.WaterSubsystem, "get_water_subsystem") else None
    log(f"WaterSubsystem via static getter: {ws}")
except Exception as e: log(f"WaterSubsystem getter err {str(e)[:80]}")
try:
    ws = world.get_subsystem(unreal.WaterSubsystem)
    log(f"world.get_subsystem(WaterSubsystem) -> {ws}")
    if ws: log("  methods: " + ", ".join(m for m in dir(ws) if not m.startswith("_") and m not in dir(unreal.Object))[:800])
except Exception as e: log(f"world.get_subsystem err {str(e)[:80]}")

def mesh_state(actor, tag):
    for c in actor.get_components_by_class(unreal.StaticMeshComponent):
        try: sm = c.static_mesh
        except Exception: sm = None
        log(f"  [{tag}] {c.get_class().get_name()} '{c.get_name()}' mesh={sm.get_name() if sm else None} outer={sm.get_outer().get_name() if sm else None}")
# a fresh default lake, spawned the way the placement tool would (no spline edits)
tmp = EAS.spawn_actor_from_class(unreal.WaterBodyLake, unreal.Vector(0, 0, 10000), unreal.Rotator(0,0,0))
tmp.set_actor_label("ZZ_TempLakeProbe")
mesh_state(tmp, "fresh spawn")
tmp.set_actor_location(unreal.Vector(0, 0, 10001), False, False)
mesh_state(tmp, "after move")
wbc = tmp.get_editor_property("water_body_component")
wbc.set_editor_property("shape_dilation", 4096.0)
mesh_state(tmp, "after prop edit")
sea = next((a for a in EAS.get_all_level_actors() if a.get_actor_label()=="Sea_Harbor"), None)
if sea:
    mesh_state(sea, "Sea_Harbor now")
    dup = EAS.duplicate_actor(sea, world, unreal.Vector(0,0,0))
    if dup:
        dup.set_actor_label("ZZ_SeaDupProbe")
        mesh_state(dup, "Sea_Harbor duplicate")
        EAS.destroy_actor(dup)
EAS.destroy_actor(tmp)
log("=== PROBE DONE (nothing saved) ===")
