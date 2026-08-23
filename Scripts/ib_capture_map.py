"""
Iron Breach — map zone capture (MENUS_UI_WIRING §7, scripted).
Targets the DEMO map (Lvl_FirstPerson — fully loads in a commandlet, unlike
world-partitioned Lvl_Plains). Computes the zone rect from actor bounds,
takes a straight-down ortho SceneCapture into a render-target ASSET, bakes it
to a static texture (synchronous — no async png export), fills DA_Map_Carrow
and places an IBMapZoneInfo actor. Idempotent.
"""
import traceback
import unreal

AT = unreal.AssetToolsHelpers.get_asset_tools()
EAL = unreal.EditorAssetLibrary

MAP_PACKAGE = "/Game/FirstPerson/Lvl_FirstPerson"
MAPS_DIR    = "/Game/IronBreach/Maps"
RT_NAME     = "RT_MapCapture"
TEX_NAME    = "T_Map_Carrow"
DA_NAME     = "DA_Map_Carrow"
ZONE_NAME   = "Carrow Exclusion Zone"
RT_SIZE     = 2048

def log(msg):
    unreal.log(f"IBPY: {msg}")

def step(name, fn):
    try:
        result = fn()
        log(f"OK   {name}")
        return result
    except Exception:
        log(f"FAIL {name}")
        unreal.log_error(traceback.format_exc())
        return None

def find_fn(obj, candidates):
    """API names drift between engine versions — resolve at runtime."""
    for c in candidates:
        if hasattr(obj, c):
            return getattr(obj, c)
    flat = {n.replace("_", ""): n for n in dir(obj)}
    for c in candidates:
        key = c.replace("_", "")
        if key in flat:
            return getattr(obj, flat[key])
    matches = [n for n in dir(obj) if "render_target" in n or "static_texture" in n]
    raise RuntimeError(f"none of {candidates} found; candidates on object: {matches}")

log("=== map capture pass starting ===")

if not EAL.does_directory_exist(MAPS_DIR):
    EAL.make_directory(MAPS_DIR)

# ---- 1. Load the demo level ----
def load_map():
    unreal.EditorLoadingAndSavingUtils.load_map(MAP_PACKAGE)
    return unreal.EditorLevelLibrary.get_editor_world()

world = step("load demo map", load_map)
if not world:
    raise SystemExit(0)

# ---- 2. Zone rect from what's actually in the level ----
def compute_bounds():
    actor_ss = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    mn = [None, None]
    mx = [None, None]
    counted = 0
    for a in actor_ss.get_all_level_actors():
        if not isinstance(a, unreal.StaticMeshActor):
            continue
        origin, extent = a.get_actor_bounds(False)
        # Skip planet-scale props (sky spheres) that would blow the rect out.
        if extent.x > 50000 or extent.y > 50000:
            continue
        counted += 1
        for i, (o, e) in enumerate(((origin.x, extent.x), (origin.y, extent.y))):
            lo, hi = o - e, o + e
            mn[i] = lo if mn[i] is None else min(mn[i], lo)
            mx[i] = hi if mx[i] is None else max(mx[i], hi)
    if counted == 0 or mn[0] is None:
        log("WARN no usable bounds — falling back to ±10000")
        return (-10000.0, -10000.0), (10000.0, 10000.0)
    # Square it (ortho capture is square) + 10% margin.
    cx, cy = (mn[0] + mx[0]) / 2.0, (mn[1] + mx[1]) / 2.0
    half = max(mx[0] - mn[0], mx[1] - mn[1]) * 0.55
    log(f"bounds from {counted} actors: center=({cx:.0f},{cy:.0f}) half={half:.0f}")
    return (cx - half, cy - half), (cx + half, cy + half)

rect = step("compute zone rect", compute_bounds)
WORLD_MIN, WORLD_MAX = rect if rect else ((-10000.0, -10000.0), (10000.0, 10000.0))

# ---- 3. Render-target ASSET (so the static bake has a home) ----
def make_rt():
    full = f"{MAPS_DIR}/{RT_NAME}"
    if EAL.does_asset_exist(full):
        rt = EAL.load_asset(full)
    else:
        factory = unreal.TextureRenderTargetFactoryNew()
        rt = AT.create_asset(RT_NAME, MAPS_DIR, unreal.TextureRenderTarget2D, factory)
    rt.set_editor_property("size_x", RT_SIZE)
    rt.set_editor_property("size_y", RT_SIZE)
    return rt

rt = step("render target asset", make_rt)

# ---- 4. Ortho top-down capture ----
def capture():
    actor_ss = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    cx = (WORLD_MIN[0] + WORLD_MAX[0]) / 2.0
    cy = (WORLD_MIN[1] + WORLD_MAX[1]) / 2.0
    loc = unreal.Vector(cx, cy, 25000.0)
    rot = unreal.Rotator(0.0, -90.0, 0.0)  # pitch straight down
    cap_actor = actor_ss.spawn_actor_from_class(unreal.SceneCapture2D, loc, rot)
    cap = cap_actor.capture_component2d
    cap.set_editor_property("projection_type", unreal.CameraProjectionMode.ORTHOGRAPHIC)
    cap.set_editor_property("ortho_width", WORLD_MAX[0] - WORLD_MIN[0])
    cap.set_editor_property("texture_target", rt)
    cap.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
    cap.set_editor_property("capture_every_frame", False)
    cap.capture_scene()
    actor_ss.destroy_actor(cap_actor)
    return True

step("ortho capture", capture)

# ---- 5. Bake to a static texture (synchronous, editor-only) ----
def bake_texture():
    if EAL.does_asset_exist(f"{MAPS_DIR}/{TEX_NAME}"):
        EAL.delete_asset(f"{MAPS_DIR}/{TEX_NAME}")  # rebake clean
    bake = find_fn(unreal.RenderingLibrary, [
        "render_target_create_static_texture2d_editor_only",
        "render_target_create_static_texture_editor_only"])
    tex = bake(rt, TEX_NAME)
    if not tex:
        raise RuntimeError("bake returned null")
    return tex

tex = step("bake static texture", bake_texture) if rt else None

# ---- 6. DA_Map_Carrow ----
def make_zone_data():
    full = f"{MAPS_DIR}/{DA_NAME}"
    if EAL.does_asset_exist(full):
        da = EAL.load_asset(full)
    else:
        factory = unreal.DataAssetFactory()
        factory.set_editor_property("data_asset_class", unreal.IBMapZoneData)
        da = AT.create_asset(DA_NAME, MAPS_DIR, unreal.IBMapZoneData, factory)
    da.set_editor_property("zone_name", ZONE_NAME)
    if tex:
        da.set_editor_property("map_texture", tex)
    da.set_editor_property("world_min", unreal.Vector2D(WORLD_MIN[0], WORLD_MIN[1]))
    da.set_editor_property("world_max", unreal.Vector2D(WORLD_MAX[0], WORLD_MAX[1]))
    return da

zone_da = step("DA_Map_Carrow", make_zone_data)

# ---- 7. IBMapZoneInfo in the demo level ----
def place_zone_info():
    actor_ss = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    existing = [a for a in actor_ss.get_all_level_actors() if isinstance(a, unreal.IBMapZoneInfo)]
    info = existing[0] if existing else actor_ss.spawn_actor_from_class(
        unreal.IBMapZoneInfo, unreal.Vector(0.0, 0.0, 0.0), unreal.Rotator(0.0, 0.0, 0.0))
    info.set_editor_property("zone_data", zone_da)
    log(f"zone info actor: {'reused' if existing else 'spawned'}")
    return info

if zone_da:
    step("IBMapZoneInfo in level", place_zone_info)

# ---- 8. Save ----
step("save", lambda: unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True))
log("=== map capture pass done ===")
