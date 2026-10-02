"""
IBPY: ib_barracks_lights.py

Adds interior lighting to the placed Barracks_02:
  * 12 ceiling light strips (emissive bars, built from engine cubes + M_Barracks02_Light_Strip)
  * 8 warm point lights under them (Movable, so they work with Lumen -- no light baking)
  * 5 small exterior lamp lights at the wall lamps beside the doors (no shadows)

Everything is positioned in the building's own space (Blender metres -> Unreal cm), attached to the
Barracks building actor, and tagged so a re-run replaces the previous lights.

HOW TO RUN (level loaded, building already placed by ib_replace_barracks.py):
  py "X:/IronBreach/Scripts/ib_barracks_lights.py"

Tune LIGHT_LUMENS / ATTENUATION / CAST_SHADOWS below and re-run. Nothing is saved automatically.
"""
import math
import unreal

TAG = "IB_Barracks02"            # same tag as the building: ib_replace_barracks.py also clears the lights
LIGHT_TAG = "IB_Barracks02_Light"
DEST_ROOT = "/Game/Buildings/Barracks_02"
BUILDING_MESH_NAME = "SM_Barracks_02"
FOLDER = "Carrowgate Garrison/Barracks Lights"

# interior layout (Blender metres, building space: x length with the nose at -X, y width, z up)
CEILING_Z = 11.7                 # strips hang just under the 11.8 m roof slab
STRIP_XS = [-7.0, -1.0, 5.0, 11.0]
STRIP_YS = [-4.5, 0.0, 4.5]
STRIP_LEN = 4.0                  # m, along X
POINT_LIGHT_Z = 10.9
POINT_LIGHT_ROWS = [-4.5, 4.5]   # y rows that get a real light (centre row is emissive only)

LIGHT_LUMENS = 4000.0
ATTENUATION = 1300.0             # cm
SOURCE_RADIUS = 20.0
CAST_SHADOWS = True              # set False if the extra shadow-casting lights cost too much
WARM = unreal.Color(255, 238, 210, 255)
EXT_LUMENS = 900.0
EXT_ATTENUATION = 700.0

# exterior lamps (match detail_pass.py): side door pair, hatch, nose pair
HY, NOSE_K, HX, SIDE_X, HATCH_X = 8.5, 5.5 / 13.0, 17.5, -3.3, 3.0


def log(msg):
    unreal.log(f"IBPY: {msg}")


def warn(msg):
    unreal.log_warning(f"IBPY: WARNING -- {msg}")


def bl(p):
    return unreal.Vector(p[0] * 100.0, -p[1] * 100.0, p[2] * 100.0)   # Blender m -> UE local cm


def find_building(actors):
    for a in actors:
        if isinstance(a, unreal.StaticMeshActor) and TAG in [str(t) for t in a.tags]:
            sm = a.static_mesh_component.static_mesh
            if sm and sm.get_name() == BUILDING_MESH_NAME:
                return a
    return None


def tag(a):
    a.set_editor_property("tags", [unreal.Name(TAG), unreal.Name(LIGHT_TAG)])


def attach(a, building):
    a.attach_to_actor(building, "", unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD,
                      unreal.AttachmentRule.KEEP_WORLD, False)


def set_prop(obj, name, value):
    try:
        obj.set_editor_property(name, value)
    except Exception as e:
        warn(f"could not set {name}: {e}")


def spawn_point(sub, building, local_cm, lumens, atten, shadows, label):
    world = building.get_actor_transform().transform_location(local_cm)
    a = sub.spawn_actor_from_class(unreal.PointLight, world, unreal.Rotator(0, 0, 0))
    if not a:
        warn(f"could not spawn {label}")
        return None
    comp = a.get_editor_property("light_component")
    try:
        comp.set_mobility(unreal.ComponentMobility.MOVABLE)          # Lumen: no baking needed
    except Exception as e:
        warn(f"mobility not set on {label}: {e}")
    set_prop(comp, "intensity_units", unreal.LightUnits.LUMENS)
    set_prop(comp, "intensity", lumens)
    set_prop(comp, "light_color", WARM)
    set_prop(comp, "attenuation_radius", atten)
    set_prop(comp, "source_radius", SOURCE_RADIUS if shadows else 4.0)
    set_prop(comp, "cast_shadows", shadows)
    a.set_actor_label(label)
    try:
        a.set_folder_path(FOLDER)
    except Exception:
        pass
    tag(a)
    attach(a, building)
    return a


def ceiling_above(building, local_cm):
    """Sanity check: trace straight up from the light; the roof slab should be within ~1.5 m."""
    try:
        start = building.get_actor_transform().transform_location(local_cm)
        end = unreal.Vector(start.x, start.y, start.z + 250.0)
        res = unreal.SystemLibrary.line_trace_single(
            unreal.EditorLevelLibrary.get_editor_world(), start, end, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,
            False, [], unreal.DrawDebugTrace.NONE, True)
        hit = res[0] if isinstance(res, tuple) else res.get_editor_property("blocking_hit")
        return bool(hit)
    except Exception:
        return None


def main():
    log("=== ib_barracks_lights START ===")
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors = sub.get_all_level_actors()

    building = find_building(actors)
    if not building:
        warn("Barracks_02 building (tag IB_Barracks02, mesh SM_Barracks_02) not found -- run ib_replace_barracks.py first.")
        return
    log(f"[1/5] building: '{building.get_actor_label()}' at {building.get_actor_location()} yaw "
        f"{building.get_actor_rotation().yaw:.1f}")

    removed = 0
    for a in actors:
        if LIGHT_TAG in [str(t) for t in a.tags]:
            sub.destroy_actor(a)
            removed += 1
    log(f"[2/5] removed {removed} previous light actor(s)")

    mat = unreal.EditorAssetLibrary.load_asset(f"{DEST_ROOT}/Materials/M_Barracks02_Light_Strip")
    cube = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cube")
    if not mat:
        warn("M_Barracks02_Light_Strip not found (run ib_barracks_tune.py first) -- strips will use the default material.")

    log(f"[3/5] ceiling strips ({len(STRIP_XS) * len(STRIP_YS)})")
    n = 0
    for x in STRIP_XS:
        for y in STRIP_YS:
            world = building.get_actor_transform().transform_location(bl((x, y, CEILING_Z)))
            a = sub.spawn_actor_from_class(unreal.StaticMeshActor, world, building.get_actor_rotation())
            if not a:
                continue
            a.static_mesh_component.set_static_mesh(cube)
            if mat:
                a.static_mesh_component.set_material(0, mat)
            a.set_actor_scale3d(unreal.Vector(STRIP_LEN, 0.25, 0.07))
            a.set_actor_enable_collision(False)
            a.static_mesh_component.set_editor_property("cast_shadow", False)
            a.set_actor_label(f"Barracks_Strip_{n:02d}")
            try:
                a.set_folder_path(FOLDER)
            except Exception:
                pass
            tag(a)
            attach(a, building)
            n += 1
    log(f"  placed {n} strips")

    log("[4/5] interior point lights")
    m = 0
    for x in STRIP_XS:
        for y in POINT_LIGHT_ROWS:
            local = bl((x, y, POINT_LIGHT_Z))
            if spawn_point(sub, building, local, LIGHT_LUMENS, ATTENUATION, CAST_SHADOWS, f"Barracks_Light_{m:02d}"):
                roof = ceiling_above(building, local)
                log(f"  Barracks_Light_{m:02d} local ({x:.1f},{y:.1f},{POINT_LIGHT_Z:.1f}) m  roof above: "
                    f"{'yes' if roof else ('NO -- outside the shell?' if roof is False else 'check skipped')}")
                m += 1

    log("[5/5] exterior lamp lights")
    k = NOSE_K / math.sqrt(1 + NOSE_K ** 2)
    c = 1 / math.sqrt(1 + NOSE_K ** 2)

    def nose(u, v, w):                                   # frame on the sloped face (see detail_pass.nose_frame)
        return (-HX + v * k - w * c, -u, v * c + w * k)

    ext = [(SIDE_X - 1.55, -HY - 0.55, 4.0), (SIDE_X + 1.55, -HY - 0.55, 4.0), (HATCH_X, -HY - 0.55, 2.75),
           nose(-1.9, 3.9, 0.6), nose(1.9, 3.9, 0.6)]
    for i, p in enumerate(ext):
        spawn_point(sub, building, bl(p), EXT_LUMENS, EXT_ATTENUATION, False, f"Barracks_LampLight_{i:02d}")
    log(f"  placed {len(ext)} lamp lights")

    log(f"=== DONE: {n} strips, {m} interior lights, {len(ext)} lamp lights. Nothing saved -- File > Save All when happy. ===")
    log("If it is too dark/bright: change LIGHT_LUMENS, or set exposure. Too expensive: CAST_SHADOWS = False.")


main()
