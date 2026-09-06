"""Iron Breach -- read-only deep inspection of the Sea_Harbor water body + WaterZone (why isn't it rendering?)."""
import unreal, os
LEVEL = os.environ.get("IB_LEVEL", "/Game/LevelPrototyping/CarrowGateGarrison")
def log(m): unreal.log(f"IBPY: {m}")
unreal.EditorLoadingAndSavingUtils.load_map(LEVEL)
acts = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
log(f"=== sea inspect: {len(acts)} actors ===")

def dump(obj, title, skip=()):
    log(f"--- {title}: {obj.get_class().get_name()} '{obj.get_name()}' ---")
    names = sorted(set(n for n in dir(obj) if not n.startswith("_")))
    for n in names:
        if n in skip or n.startswith(("set_", "get_", "add_", "remove_", "clear_", "find_", "make_", "on_", "k2_", "receive_", "is_", "has_", "can_")):
            continue
        try:
            v = obj.get_editor_property(n)
        except Exception:
            continue
        s = str(v)
        if len(s) > 160: s = s[:160] + "..."
        log(f"    {n} = {s}")

def comps(actor):
    try:
        return actor.get_components_by_class(unreal.ActorComponent)
    except Exception:
        return []

sea = next((a for a in acts if a.get_actor_label() == "Sea_Harbor"), None)
zone = next((a for a in acts if a.get_actor_label() == "WaterZone_Harbor"), None)
zones = [a for a in acts if isinstance(a, unreal.WaterZone)]
bodies = [a for a in acts if isinstance(a, unreal.WaterBody)]
log(f"water zones: {[a.get_actor_label() for a in zones]}   water bodies: {[a.get_actor_label() for a in bodies]}")

if sea:
    log(f"Sea_Harbor loc={sea.get_actor_location()} hidden={sea.is_hidden_ed()} hidden_in_game={sea.get_editor_property('hidden')}")
    o, ext = sea.get_actor_bounds(False)
    log(f"Sea_Harbor bounds center={o} ext={ext}")
    for c in comps(sea):
        log(f"  component: {c.get_class().get_name()} '{c.get_name()}'")
    dump(sea, "Sea_Harbor actor")
    wbc = sea.get_editor_property("water_body_component")
    if wbc:
        dump(wbc, "WaterBodyComponent")
        try: log(f"  get_water_zone() -> {wbc.get_water_zone()}")
        except Exception as e: log(f"  get_water_zone err {str(e)[:80]}")
        try: log(f"  get_water_material() -> {wbc.get_water_material()}")
        except Exception as e: log(f"  get_water_material err {str(e)[:80]}")
        try: log(f"  get_water_waves() -> {wbc.get_water_waves()}")
        except Exception as e: log(f"  get_water_waves err {str(e)[:80]}")
        try: log(f"  get_max_wave_height() -> {wbc.get_max_wave_height()}")
        except Exception as e: log(f"  get_max_wave_height err {str(e)[:80]}")
    spl = sea.get_editor_property("spline_comp")
    if spl:
        n = spl.get_number_of_spline_points()
        log(f"  spline points={n} closed={spl.is_closed_loop()}")
        for i in range(n):
            log(f"    pt{i} {spl.get_location_at_spline_point(i, unreal.SplineCoordinateSpace.WORLD)}")
    ww = None
    try: ww = sea.get_editor_property("water_waves")
    except Exception: pass
    log(f"  actor.water_waves = {ww}")
    if ww:
        dump(ww, "WaterWaves")
        try:
            gen = ww.get_editor_property("gerstner_wave_generator")
            if gen: dump(gen, "GerstnerWaveGenerator")
        except Exception as e: log(f"  gen err {str(e)[:80]}")
        try:
            gw = ww.get_editor_property("gerstner_waves")
            log(f"  gerstner_waves count = {len(gw) if gw is not None else None}")
            if gw:
                for i, w in enumerate(list(gw)[:5]): log(f"    wave{i}: {w}")
        except Exception as e: log(f"  gerstner_waves err {str(e)[:80]}")
        try: log(f"  ww.get_max_wave_height() -> {ww.get_max_wave_height()}")
        except Exception as e: log(f"  ww.get_max_wave_height err {str(e)[:80]}")
else:
    log("Sea_Harbor NOT FOUND")

for z in zones:
    log(f"zone '{z.get_actor_label()}' loc={z.get_actor_location()}")
    for c in comps(z):
        log(f"  component: {c.get_class().get_name()} '{c.get_name()}'")
    dump(z, "WaterZone actor")
    try:
        wm = z.get_editor_property("water_mesh")
        if wm: dump(wm, "WaterMeshComponent")
    except Exception as e: log(f"  water_mesh err {str(e)[:80]}")

# editor defaults the Water placement tool would have applied
try:
    ws = unreal.get_default_object(unreal.WaterEditorSettings)
    for p in ("water_body_ocean_defaults", "water_body_lake_defaults", "water_body_river_defaults", "water_zone_actor_defaults"):
        try:
            v = ws.get_editor_property(p); log(f"WaterEditorSettings.{p} = {v}")
        except Exception as e: log(f"WaterEditorSettings.{p} err {str(e)[:80]}")
except Exception as e:
    log(f"WaterEditorSettings err {str(e)[:100]}")

# plugin content inventory
ar = unreal.AssetRegistryHelpers.get_asset_registry()
assets = ar.get_assets_by_path("/Water", recursive=True)
log(f"/Water assets: {len(assets)}")
for a in assets:
    cls = str(a.asset_class_path.asset_name)
    if cls in ("Material", "MaterialInstanceConstant", "StaticMesh", "WaterWavesAsset", "Texture2D"):
        log(f"  [{cls}] {a.package_name}")

# the other flat planes at z~-430 (Shane's AI water/foam slabs)
for a in acts:
    if isinstance(a, unreal.StaticMeshActor) and a.get_name() in ("StaticMeshActor_1734", "StaticMeshActor_1735"):
        smc = a.static_mesh_component
        mats = []
        try:
            for i in range(smc.get_num_materials()):
                m = smc.get_material(i); mats.append(m.get_name() if m else "None")
        except Exception: pass
        o, ext = a.get_actor_bounds(False)
        log(f"slab {a.get_name()} label='{a.get_actor_label()}' mesh={smc.static_mesh.get_name() if smc.static_mesh else None} mats={mats} center={o} ext={ext} hidden_in_game={a.get_editor_property('hidden')}")
ph = next((a for a in acts if a.get_actor_label() == "Water_Placeholder"), None)
if ph:
    o, ext = ph.get_actor_bounds(False)
    log(f"Water_Placeholder name={ph.get_name()} center={o} ext={ext} hidden_in_game={ph.get_editor_property('hidden')}")
log("=== DONE ===")
