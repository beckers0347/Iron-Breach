"""
IBPY: ib_replace_barracks.py

Imports the procedural "Barracks_02" bunker (static shell + 3 animated skeletal doors),
replaces the existing Tripo Barracks in the open level, and rigs a proximity sensor to each
door (AIBSensorDoor, C++), so doors open when a player pawn walks up and close behind them.

PREREQUISITES
  1. Compile the C++ first (Source/IronBreach/World/IBSensorDoor.h/.cpp) -- BUILD_IronBreach.bat,
     then restart the editor. This script aborts early if the class is not found.
  2. Copy these 4 files into SOURCE_DIR (below):
        SM_Barracks_02.fbx
        SK_Barracks_02_Door_Nose.fbx
        SK_Barracks_02_Door_Side.fbx
        SK_Barracks_02_Door_Hatch.fbx
  3. Open the CarrowGateGarrison level.

HOW TO RUN
  py "X:/IronBreach/Scripts/ib_replace_barracks.py"

WHAT IT DOES (every step logs with the IBPY: prefix)
  [1] Preflight     engine version, FBX files, sensor class, old Barracks found?
  [2] Import        4 FBXs -> /Game/Buildings/Barracks_02/..., renames door anim sequences,
                    maps materials onto your existing M_05_Barracks_* (optional, see flags)
  [3] Placement     reads the OLD Barracks' bounds + door direction, computes position and yaw so
                    the new "02" nose end faces where the old door faced
  [4] Spawn         new building actor + 3 sensor doors, attached to it, tagged IB_Barracks02
  [5] Park old      old mesh, old BP_DoorFrame and hidden blockout colliders are hidden, have
                    collision disabled and are moved to the folder _Replaced_Barracks
                    (NOT deleted -- set DELETE_OLD = True if you want that)
  [6] Verify        new bounds, overlaps with neighbouring buildings, sensor world positions

SAFE TO RE-RUN: actors this script spawned carry the tag IB_Barracks02 and are replaced.
NOTHING IS SAVED AUTOMATICALLY -- review in the viewport, then File > Save All.

To see the runtime door logs in Output Log: the script sets "Log LogIronBreach Verbose".
"""

import importlib
import math
import os
import sys
import unreal

_here = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else "X:/IronBreach/Scripts"
if _here not in sys.path:
    sys.path.insert(0, _here)
import ib_barracks_materials as mats_mod
importlib.reload(mats_mod)

# ---------------------------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------------------------
SOURCE_DIR = "X:/IronBreach/SourceArt/Barracks_02"     # where the 4 FBX files live
DEST_ROOT = "/Game/Buildings/Barracks_02"               # content folder for the imports

STATIC_FBX = "SM_Barracks_02.fbx"
DOOR_FBX = {
    "Nose": "SK_Barracks_02_Door_Nose.fbx",
    "Side": "SK_Barracks_02_Door_Side.fbx",
    "Hatch": "SK_Barracks_02_Door_Hatch.fbx",
}

SENSOR_CLASS_PATH = "/Script/IronBreach.IBSensorDoor"    # AIBSensorDoor

# Old Barracks identification (from ib_place_tripo_meshes / ib_inventory_garrison)
OLD_MESH_PATH_PREFIX = "/Game/TripoModels/Barracks/Barracks."   # note the trailing dot: excludes Barracks_Collision
OLD_LABEL_HINTS = ("Barracks", "SM_Barracks_Tripo")
OLD_DOOR_LABELS = ("05_Barracks_DoorFrame", "Barracks_DoorFrame")
OUTLINER_FOLDER_KEYWORD = "Barracks"                     # blockout pieces live in a folder with this segment
COURTYARD_CENTER = (4087.0, 4399.0)                      # fallback "doors face this" point if no old door found

# New actor settings
NEW_BUILDING_LABEL = "Barracks"
OLD_LABEL_SUFFIX = "_REPLACED"
NEW_FOLDER = "Carrowgate Garrison"
PARK_FOLDER = "_Replaced_Barracks"
PLACE_SCALE = 1.0               # new shell is ~3790 x 2100 x 1925 cm incl. bollards/roof; old was ~1160 x 2460 x 1575
TAG = "IB_Barracks02"

# Behaviour flags
DRY_RUN = False                 # True = preflight + find old + log the plan, change nothing
DO_IMPORT = True
DO_PLACE = True
DO_SENSORS = True
PARK_OLD = True
DELETE_OLD = False              # True = delete the old actors instead of parking them
USE_BARRACKS_MATERIALS = True   # build clean procedural materials (ib_barracks_materials.py) and apply them
USE_PROJECT_MATERIALS = False   # alternative: map slots onto your M_05_Barracks_* (they look dark/camo on this mesh)
PREVIEW_DOORS_OPEN = False      # True = leave the doors posed fully open in the editor viewport
SET_VERBOSE_LOG = True
USE_NANITE = True               # the shell is now ~139k triangles (bolts, bars, rails); Nanite keeps that cheap

MATERIAL_MAP = {
    "Concrete_Weathered": "/Game/Generated_Materials/M_05_Barracks_Concrete",
    "Armor_Paint": "/Game/Generated_Materials/M_05_Barracks_Trim",
    "Door_Metal": "/Game/Generated_Materials/M_05_Barracks_Trim",
}

# Sensor + blocker layout per door. Positions are authored in Blender metres (x, y, z) and converted to
# Unreal actor-local cm with (x, -y, z) * 100. Half extents are in metres, local box axes.
#   sensor: overlap volume that detects pawns        blocker: solid plug that fills the doorway while shut
#   blocker_pitch: tilt in degrees (the nose door lies on the sloped end face, 22.9 deg off vertical)
DOORS = {
    "Nose": {
        "sensor_c": (-17.0, 0.0, 1.6), "sensor_h": (3.5, 3.0, 1.7),
        "blocker_c": (-16.42, 0.0, 1.27), "blocker_h": (0.5, 1.2, 1.6), "blocker_pitch": -22.9,
    },
    "Side": {
        "sensor_c": (-3.3, -8.5, 1.6), "sensor_h": (2.8, 3.5, 1.7),
        "blocker_c": (-3.3, -8.0, 1.6), "blocker_h": (1.2, 0.5, 1.6), "blocker_pitch": 0.0,
    },
    "Hatch": {
        "sensor_c": (3.0, -8.5, 1.0), "sensor_h": (1.8, 2.5, 1.2),
        "blocker_c": (3.0, -8.0, 1.0), "blocker_h": (0.7, 0.5, 0.95), "blocker_pitch": 0.0,
    },
}
CLOSE_DELAY = 1.5
OPEN_SECONDS = {"Nose": 1.0, "Side": 1.0, "Hatch": 0.6}   # full swing; the animation itself is 3 / 3 / 1.5 s
PLAYER_PAWNS_ONLY = True


# ---------------------------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------------------------
def log(msg):
    unreal.log(f"IBPY: {msg}")


def warn(msg):
    unreal.log_warning(f"IBPY: WARNING -- {msg}")


def err(msg):
    unreal.log_error(f"IBPY: ERROR -- {msg}")


def bl_to_ue(p):
    """Blender metres -> Unreal actor-local cm."""
    return unreal.Vector(p[0] * 100.0, -p[1] * 100.0, p[2] * 100.0)


def all_actors():
    return unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()


def folder_segments(actor):
    return [s for s in str(actor.get_folder_path()).split("/") if s]


def mesh_path_of(actor):
    if not isinstance(actor, unreal.StaticMeshActor):
        return ""
    sm = actor.static_mesh_component.static_mesh
    return sm.get_path_name() if sm else ""


def tag_name(actor_tags):
    return [str(t) for t in actor_tags]


def bounds(actor):
    origin, extent = actor.get_actor_bounds(False)
    return origin, extent


def aabb_overlap(o1, e1, o2, e2):
    return (abs(o1.x - o2.x) < e1.x + e2.x and abs(o1.y - o2.y) < e1.y + e2.y and abs(o1.z - o2.z) < e1.z + e2.z)


# ---------------------------------------------------------------------------------------------
# [1] preflight
# ---------------------------------------------------------------------------------------------
def preflight():
    log(f"[1/6] PREFLIGHT -- engine {unreal.SystemLibrary.get_engine_version()}")
    ok = True
    files = {"static": os.path.join(SOURCE_DIR, STATIC_FBX)}
    for k, f in DOOR_FBX.items():
        files[f"door_{k}"] = os.path.join(SOURCE_DIR, f)
    if DO_IMPORT:
        for k, p in files.items():
            if os.path.isfile(p):
                log(f"  FBX ok   {k}: {p} ({os.path.getsize(p) / 1024:.0f} KB)")
            else:
                err(f"FBX missing {k}: {p}")
                ok = False
    sensor_cls = None
    if DO_SENSORS:
        sensor_cls = unreal.load_class(None, SENSOR_CLASS_PATH)
        if sensor_cls:
            log(f"  sensor class ok: {sensor_cls.get_name()}")
        else:
            err(f"could not load C++ class '{SENSOR_CLASS_PATH}'. Did you add IBSensorDoor.h/.cpp, build, and restart the editor?")
            ok = False
    return ok, files, sensor_cls


# ---------------------------------------------------------------------------------------------
# [2] import
# ---------------------------------------------------------------------------------------------
def _fbx_ui(skeletal):
    ui = unreal.FbxImportUI()
    ui.set_editor_property("import_mesh", True)
    ui.set_editor_property("import_textures", False)
    ui.set_editor_property("import_materials", True)
    ui.set_editor_property("import_as_skeletal", bool(skeletal))
    try:
        ui.set_editor_property(
            "mesh_type_to_import",
            unreal.FBXImportType.FBXIT_SKELETAL_MESH if skeletal else unreal.FBXImportType.FBXIT_STATIC_MESH)
    except Exception as e:  # property name differs between versions; import_as_skeletal is enough
        log(f"  (mesh_type_to_import not set: {e})")
    ui.set_editor_property("automated_import_should_detect_type", False)
    if skeletal:
        ui.set_editor_property("import_animations", True)
        ui.set_editor_property("create_physics_asset", False)
    else:
        ui.set_editor_property("import_animations", False)
        sm = ui.static_mesh_import_data
        sm.set_editor_property("combine_meshes", True)
        sm.set_editor_property("auto_generate_collision", False)     # we ship UCX_ hulls
        sm.set_editor_property("generate_lightmap_u_vs", False)      # Lumen; mesh has one UV set
        sm.set_editor_property("remove_degenerates", True)
        if USE_NANITE:                                               # ~139k tris: let Nanite handle it
            try:
                sm.set_editor_property("build_nanite", True)
            except Exception as e:
                log(f"  (could not enable Nanite on import: {e}) -- tick Enable Nanite Support on the mesh by hand")
    return ui


def import_fbx(path, dest_path, dest_name, skeletal):
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", path)
    task.set_editor_property("destination_path", dest_path)
    task.set_editor_property("destination_name", dest_name)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("replace_existing_settings", True)
    task.set_editor_property("automated", True)
    task.set_editor_property("save", False)
    task.set_editor_property("options", _fbx_ui(skeletal))
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    paths = [str(p) for p in task.get_editor_property("imported_object_paths")]
    assets = []
    for p in paths:
        a = unreal.EditorAssetLibrary.load_asset(p)
        if a:
            assets.append(a)
    log(f"  imported {os.path.basename(path)} -> {len(assets)} asset(s): "
        + ", ".join(f"{a.get_name()}[{a.get_class().get_name()}]" for a in assets))
    return assets


def pick(assets, cls):
    return [a for a in assets if isinstance(a, cls)]


def map_static_materials(mesh):
    if not USE_PROJECT_MATERIALS:
        return
    mats = list(mesh.get_editor_property("static_materials"))
    for i, sm in enumerate(mats):
        slot = str(sm.get_editor_property("imported_material_slot_name"))
        target = MATERIAL_MAP.get(slot)
        if not target:
            log(f"  slot {i} '{slot}': keeping imported material")
            continue
        if unreal.EditorAssetLibrary.does_asset_exist(target):
            mesh.set_material(i, unreal.EditorAssetLibrary.load_asset(target))
            log(f"  slot {i} '{slot}' -> {target}")
        else:
            warn(f"slot {i} '{slot}': {target} not found, keeping imported material")


def do_import(files):
    log("[2/6] IMPORT")
    result = {"static": None, "doors": {}}

    assets = import_fbx(files["static"], f"{DEST_ROOT}/Static", "SM_Barracks_02", skeletal=False)
    meshes = pick(assets, unreal.StaticMesh)
    if not meshes:
        err("static import produced no StaticMesh -- see Output Log for FBX errors.")
        return None
    mesh = meshes[0]
    result["static"] = mesh
    log(f"  SM_Barracks_02: {mesh.get_num_sections(0)} sections")
    try:
        hulls = mesh.get_editor_property("body_setup").get_editor_property("agg_geom").get_editor_property("convex_elems")
        log(f"  convex collision hulls: {len(hulls)} (expect 11)")
        if len(hulls) != 11:
            warn("collision hull count is not 11 -- UCX_ pieces may not have been picked up; check collision in the Static Mesh editor.")
    except Exception as e:
        log(f"  (could not read hull count: {e}) -- open SM_Barracks_02 and use Show > Simple Collision to confirm 11 hulls")
    log(f"  bounds: {mesh.get_bounds().box_extent} (half extents, cm)")
    map_static_materials(mesh)
    if USE_BARRACKS_MATERIALS:
        result["mats"] = mats_mod.build_all(f"{DEST_ROOT}/Materials")
        mats_mod.apply_to_static_mesh(mesh, result["mats"])

    for key, fname in DOOR_FBX.items():
        name = f"SK_Barracks_02_Door_{key}"
        assets = import_fbx(files[f"door_{key}"], f"{DEST_ROOT}/Doors/{key}", name, skeletal=True)
        sk = pick(assets, unreal.SkeletalMesh)
        anims = pick(assets, unreal.AnimSequence)
        if not sk:
            err(f"door {key}: no SkeletalMesh imported.")
            return None
        if not anims:
            err(f"door {key}: no AnimSequence imported (check FBX animation import).")
            return None
        anim = anims[0]
        old_path = anim.get_path_name().split(".")[0]
        new_name = f"AS_Barracks_02_Door_{key}_Open"
        new_path = f"{DEST_ROOT}/Doors/{key}/{new_name}"
        if old_path != new_path:
            if unreal.EditorAssetLibrary.does_asset_exist(new_path):
                unreal.EditorAssetLibrary.delete_asset(new_path)
            if unreal.EditorAssetLibrary.rename_asset(old_path, new_path):
                anim = unreal.EditorAssetLibrary.load_asset(new_path)
            else:
                warn(f"door {key}: could not rename '{old_path}', using it as-is")
        log(f"  door {key}: anim '{anim.get_name()}' length {anim.get_editor_property('sequence_length'):.2f}s")
        result["doors"][key] = (sk[0], anim)
    return result


def load_existing_imports():
    """When DO_IMPORT is False, reuse assets from a previous run."""
    log("[2/6] IMPORT skipped -- loading assets from a previous run")
    mesh = unreal.EditorAssetLibrary.load_asset(f"{DEST_ROOT}/Static/SM_Barracks_02")
    result = {"static": mesh, "doors": {}}
    if USE_BARRACKS_MATERIALS:
        result["mats"] = mats_mod.build_all(f"{DEST_ROOT}/Materials")
        if mesh:
            mats_mod.apply_to_static_mesh(mesh, result["mats"])
    for key in DOOR_FBX:
        sk = unreal.EditorAssetLibrary.load_asset(f"{DEST_ROOT}/Doors/{key}/SK_Barracks_02_Door_{key}")
        an = unreal.EditorAssetLibrary.load_asset(f"{DEST_ROOT}/Doors/{key}/AS_Barracks_02_Door_{key}_Open")
        if not (sk and an):
            err(f"door {key}: previous import not found")
            return None
        result["doors"][key] = (sk, an)
    if not mesh:
        err("previous SM_Barracks_02 import not found")
        return None
    return result


# ---------------------------------------------------------------------------------------------
# [3] find old Barracks + compute placement
# ---------------------------------------------------------------------------------------------
def find_old():
    actors = all_actors()
    cands = [a for a in actors if mesh_path_of(a).startswith(OLD_MESH_PATH_PREFIX) and TAG not in tag_name(a.tags)]
    if not cands:
        log("  no actor uses the old Barracks mesh. Actors with 'arrack' in label:")
        for a in actors:
            if "arrack" in a.get_actor_label():
                log(f"    {a.get_actor_label()}  [{a.get_class().get_name()}]  mesh={mesh_path_of(a)}")
        return None, None, [], actors
    base = lambda a: a.get_actor_label().replace(OLD_LABEL_SUFFIX, "")
    old = next((a for a in cands if base(a) in OLD_LABEL_HINTS), cands[0])
    log(f"  old Barracks: '{old.get_actor_label()}' ({old.get_name()}), {len(cands)} candidate(s)")
    door = next((a for a in actors if a.get_actor_label().replace(OLD_LABEL_SUFFIX, "") in OLD_DOOR_LABELS), None)
    log(f"  old door frame: {door.get_actor_label() if door else 'NOT FOUND (using courtyard fallback)'}")
    pieces = []
    for a in actors:
        if a in (old, door) or not isinstance(a, unreal.StaticMeshActor) or TAG in tag_name(a.tags):
            continue
        if OUTLINER_FOLDER_KEYWORD in folder_segments(a) and a.get_editor_property("hidden"):
            pieces.append(a)
    log(f"  hidden blockout colliders in a '{OUTLINER_FOLDER_KEYWORD}' folder: {len(pieces)}")
    return old, door, pieces, actors


def compute_placement(old, door):
    origin, extent = bounds(old)
    loc = old.get_actor_location()
    floor_z = origin.z - extent.z
    log(f"  old bounds: center=({origin.x:.0f},{origin.y:.0f},{origin.z:.0f}) half=({extent.x:.0f},{extent.y:.0f},{extent.z:.0f})")
    log(f"  old actor pivot z={loc.z:.0f}; lowest point of old bounds z={floor_z:.0f}  -> using the lowest point as floor")
    if door:
        dl = door.get_actor_location()
        dx, dy = dl.x - origin.x, dl.y - origin.y
        src = "old door frame"
    else:
        dx, dy = COURTYARD_CENTER[0] - origin.x, COURTYARD_CENTER[1] - origin.y
        src = "courtyard centre"
    mag = math.hypot(dx, dy)
    if mag < 1.0:
        dx, dy, mag = 0.0, 1.0, 1.0
        warn("door direction undefined; defaulting to +Y")
    dx, dy = dx / mag, dy / mag
    # new building: the nose ('02' end, door on the slope) is local -X; we want local -X to point along (dx,dy)
    yaw = math.degrees(math.atan2(-dy, -dx))
    # mesh pivot is the footprint centre at ground level (bounds centre x offset ~+0.3 m is negligible)
    place = unreal.Vector(origin.x, origin.y, floor_z)
    log(f"  door direction from {src}: ({dx:.2f},{dy:.2f}) -> yaw {yaw:.1f} deg, location ({place.x:.0f},{place.y:.0f},{place.z:.0f})")
    return place, yaw


# ---------------------------------------------------------------------------------------------
# [4] spawn
# ---------------------------------------------------------------------------------------------
def remove_previous_spawns():
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    n = 0
    for a in sub.get_all_level_actors():
        if TAG in tag_name(a.tags):
            sub.destroy_actor(a)
            n += 1
    if n:
        log(f"  removed {n} actor(s) from a previous run of this script")


def tag_actor(a):
    a.set_editor_property("tags", [unreal.Name(TAG)])


def spawn_building(mesh, place, yaw):
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    a = sub.spawn_actor_from_class(unreal.StaticMeshActor, place, unreal.Rotator(0.0, 0.0, yaw))
    if not a:
        err("spawn of the new building failed")
        return None
    a.static_mesh_component.set_static_mesh(mesh)
    a.set_actor_scale3d(unreal.Vector(PLACE_SCALE, PLACE_SCALE, PLACE_SCALE))
    a.set_actor_label(NEW_BUILDING_LABEL)
    try:
        a.set_folder_path(NEW_FOLDER)
    except Exception as e:
        log(f"  (folder not set: {e})")
    tag_actor(a)
    log(f"  spawned '{a.get_actor_label()}' at {place} yaw {yaw:.1f} scale {PLACE_SCALE}")
    return a


def spawn_doors(building, sensor_cls, imports, place, yaw):
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    doors = {}
    for key, cfg in DOORS.items():
        sk, anim = imports["doors"][key]
        d = sub.spawn_actor_from_class(sensor_cls, place, unreal.Rotator(0.0, 0.0, yaw))
        if not d:
            err(f"spawn of sensor door '{key}' failed")
            continue
        d.set_actor_scale3d(unreal.Vector(PLACE_SCALE, PLACE_SCALE, PLACE_SCALE))
        d.configure_door(sk, anim)
        d.configure_volumes(
            bl_to_ue(cfg["sensor_c"]),
            unreal.Vector(cfg["sensor_h"][0] * 100.0, cfg["sensor_h"][1] * 100.0, cfg["sensor_h"][2] * 100.0),
            bl_to_ue(cfg["blocker_c"]),
            unreal.Vector(cfg["blocker_h"][0] * 100.0, cfg["blocker_h"][1] * 100.0, cfg["blocker_h"][2] * 100.0),
            unreal.Rotator(0.0, cfg["blocker_pitch"], 0.0))
        d.set_editor_property("close_delay", CLOSE_DELAY)
        d.set_editor_property("open_duration_override", OPEN_SECONDS.get(key, 0.0))
        d.set_editor_property("player_pawns_only", PLAYER_PAWNS_ONLY)
        if PREVIEW_DOORS_OPEN:
            d.set_editor_property("editor_preview_progress", 1.0)
        if USE_BARRACKS_MATERIALS and imports.get("mats"):
            mats_mod.apply_to_component(d.get_editor_property("door_mesh"), imports["mats"])
        elif USE_PROJECT_MATERIALS:
            comp = d.get_editor_property("door_mesh")
            for i, slot in enumerate(comp.get_material_slot_names()):
                target = MATERIAL_MAP.get(str(slot))
                if target and unreal.EditorAssetLibrary.does_asset_exist(target):
                    comp.set_material(i, unreal.EditorAssetLibrary.load_asset(target))
                    log(f"    door {key} slot '{slot}' -> {target}")
        d.set_actor_label(f"Barracks_Door_{key}")
        try:
            d.set_folder_path(NEW_FOLDER + "/Barracks Doors")
        except Exception:
            pass
        tag_actor(d)
        d.attach_to_actor(building, "", unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD,
                          unreal.AttachmentRule.KEEP_WORLD, False)
        doors[key] = d
        log(f"  spawned sensor door '{key}': anim '{anim.get_name()}', close_delay {CLOSE_DELAY}s, player only={PLAYER_PAWNS_ONLY}")
    return doors


# ---------------------------------------------------------------------------------------------
# [5] park old
# ---------------------------------------------------------------------------------------------
def retire(actor, rename=True):
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    label = actor.get_actor_label()
    if DELETE_OLD:
        sub.destroy_actor(actor)
        log(f"  deleted '{label}'")
        return
    if rename and not label.endswith(OLD_LABEL_SUFFIX):
        actor.set_actor_label(label + OLD_LABEL_SUFFIX)
    actor.set_actor_hidden_in_game(True)
    actor.set_actor_enable_collision(False)
    try:
        actor.set_is_temporarily_hidden_in_editor(True)
    except Exception:
        pass
    try:
        actor.set_folder_path(PARK_FOLDER)
    except Exception:
        pass
    log(f"  parked '{label}' (hidden, collision off) in '{PARK_FOLDER}'")


# ---------------------------------------------------------------------------------------------
# [6] verify
# ---------------------------------------------------------------------------------------------
def verify(building, doors, actors):
    log("[6/6] VERIFY")
    o, e = bounds(building)
    log(f"  new building bounds: center=({o.x:.0f},{o.y:.0f},{o.z:.0f}) half=({e.x:.0f},{e.y:.0f},{e.z:.0f}) "
        f"(expect ~1894 x 1050 x 963 cm for yaw 0; swapped X/Y near +-90)")
    hits = 0
    for a in actors:
        if a == building or TAG in tag_name(a.tags) or not isinstance(a, unreal.StaticMeshActor):
            continue
        if not mesh_path_of(a).startswith("/Game/TripoModels/"):
            continue
        if mesh_path_of(a).startswith(OLD_MESH_PATH_PREFIX):
            continue
        o2, e2 = bounds(a)
        if aabb_overlap(o, e, o2, e2):
            hits += 1
            warn(f"new Barracks bounds overlap '{a.get_actor_label()}' -- move/rotate the new Barracks or the neighbour")
    if not hits:
        log("  no overlap with the other Tripo garrison buildings (bounding boxes).")
    for key, d in doors.items():
        sensor = d.get_editor_property("sensor_box")
        blocker = d.get_editor_property("blocker_box")
        sl = sensor.get_world_location()
        bl = blocker.get_world_location()
        inside = abs(sl.x - o.x) < e.x + 600 and abs(sl.y - o.y) < e.y + 600
        log(f"  door {key}: sensor world ({sl.x:.0f},{sl.y:.0f},{sl.z:.0f}) blocker world ({bl.x:.0f},{bl.y:.0f},{bl.z:.0f}) "
            f"{'OK near building' if inside else 'WARNING far from building'}")
    log("  Walk up to each door in PIE: the Output Log shows 'SensorDoor ...' lines (LogIronBreach, Verbose).")


# ---------------------------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------------------------
def main():
    log("=== ib_replace_barracks START ===" + ("  [DRY RUN]" if DRY_RUN else ""))
    if SET_VERBOSE_LOG:
        try:
            unreal.SystemLibrary.execute_console_command(None, "Log LogIronBreach Verbose")
        except Exception:
            pass

    ok, files, sensor_cls = preflight()
    if not ok:
        err("preflight failed -- nothing was changed.")
        return

    log("[3/6] LOCATE OLD BARRACKS")
    old, door, pieces, actors = find_old()
    if not old:
        err("old Barracks not found -- nothing was changed. (Set OLD_MESH_PATH_PREFIX if the mesh moved.)")
        return
    place, yaw = compute_placement(old, door)

    if DRY_RUN:
        log("DRY RUN: would import 4 FBXs, spawn the building + 3 sensor doors, and park "
            f"{1 + (1 if door else 0) + len(pieces)} old actor(s). Nothing changed.")
        return

    if DO_IMPORT:
        imports = do_import(files)
    else:
        imports = load_existing_imports()
    if not imports:
        err("import step failed -- old Barracks left untouched.")
        return

    if not DO_PLACE:
        log("DO_PLACE False -- stopping after import.")
        return

    log("[4/6] SPAWN")
    remove_previous_spawns()
    building = spawn_building(imports["static"], place, yaw)
    if not building:
        err("could not spawn building -- old Barracks left untouched.")
        return
    doors = {}
    if DO_SENSORS:
        doors = spawn_doors(building, sensor_cls, imports, place, yaw)

    log("[5/6] PARK OLD" + (" (DELETE)" if DELETE_OLD else ""))
    if PARK_OLD:
        retire(old)
        if door:
            retire(door)
        for p in pieces:
            retire(p, rename=False)
    else:
        log("  PARK_OLD False -- old actors left as they were (they will overlap the new building).")

    verify(building, doors, actors)

    unreal.EditorLevelLibrary.set_selected_level_actors([building] + list(doors.values()))
    log("=== DONE. Nothing saved: review in the viewport, then File > Save All. ===")
    log("Reminder: inventory scripts (ib_inventory_garrison.py) still list the old mesh path /Game/TripoModels/Barracks/Barracks.")


main()
