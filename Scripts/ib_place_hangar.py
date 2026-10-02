"""
IBPY: ib_place_hangar.py

Imports the procedural "Hangar_04" mech hangar (hollow static shell + 4 animated skeletal door sets),
places it in the open level and rigs a proximity sensor to every door (AIBSensorDoor, already compiled
for the Barracks -- no new C++).

  Main   4-leaf bi-parting sliding door, 14 x 10 m, leaves slide sideways into the front wall
  Rear   hinged personnel door   (opens outward)
  SideN / SideS   hinged personnel doors (open outward)

PREREQUISITES
  1. AIBSensorDoor is compiled (it is -- the Barracks uses it).
  2. Copy the 5 FBXs into SOURCE_DIR:
        SM_Hangar_04.fbx  SK_Hangar_04_Door_Main.fbx  SK_Hangar_04_Door_Rear.fbx
        SK_Hangar_04_Door_SideN.fbx  SK_Hangar_04_Door_SideS.fbx
  3. Open the CarrowGateGarrison level.

RUN
  py "X:/IronBreach/Scripts/ib_place_hangar.py"

WHERE IT PUTS THE HANGAR (first match wins)
  0. the actor you have SELECTED in the viewport (easiest: click the white cube, then run)
  1. HANGAR_LOCATION / HANGAR_YAW set below (explicit override, cm / degrees)
  2. an actor whose label contains one of PLACEHOLDER_HINTS (the white cube / blockout) -> its footprint centre,
     lowest point as the floor; the placeholder is parked (hidden, no collision), never deleted
  3. the 4 'Reserve_Edge_*' marker actors from ib_layout_garrison.py (hangar reservation outline)
  If none is found nothing is changed and the log tells you what to set. Nothing else in the level is touched.

The hangar faces FACE_DIRECTION (default +X = towards the spine). The building's front is local -X.
Set DRY_RUN = True to only log the plan.

SAFE TO RE-RUN: actors this script spawned carry tag IB_Hangar04 and are replaced. NOTHING IS SAVED --
review, then File > Save All.
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

# ------------------------------------------------------------------------------------------ CONFIG
SOURCE_DIR = "X:/IronBreach/SourceArt/Hangar_04"
DEST_ROOT = "/Game/Buildings/Hangar_04"
STATIC_FBX = "SM_Hangar_04.fbx"
DOOR_KEYS = ("Main", "Rear", "SideN", "SideS")
SENSOR_CLASS_PATH = "/Script/IronBreach.IBSensorDoor"

HANGAR_LOCATION = None            # e.g. (123000.0, 4400.0, 250.0) cm to force a spot; None = auto-detect
HANGAR_YAW = None                 # degrees; None = face FACE_DIRECTION
FACE_DIRECTION = (1.0, 0.0)       # world XY direction the big door faces (towards the spine)
PLACEHOLDER_HINTS = ("hangar", "mech")      # label substrings (case-insensitive) of a placeholder actor
RESERVE_LABEL_PREFIX = "Reserve_Edge_"
PLACE_SCALE = 1.0
TAG = "IB_Hangar04"
LABEL = "Mech_Hangar"
FOLDER = "Carrowgate Garrison"
PARK_FOLDER = "_Replaced_Hangar_Placeholder"

DRY_RUN = False
DO_IMPORT = True
USE_NANITE = True
SET_VERBOSE_LOG = True
CLOSE_DELAY = 3.0                 # the main door is big; wait a little before shutting
PLAYER_PAWNS_ONLY = True
OPEN_SECONDS = {"Main": 3.5, "Rear": 1.0, "SideN": 1.0, "SideS": 1.0}   # animations are 4.0 / 2.0 / 2.0 / 2.0 s

# Blender metres (x, y, z) -> UE local cm (x, -y, z). Half extents in metres.
# Sensors straddle the wall so the door also opens for someone inside.
DOORS = {
    "Main": {"sensor_c": (-17.0, 0.0, 5.0), "sensor_h": (5.0, 8.5, 5.0),
             "blocker_c": (-12.5, 0.0, 5.0), "blocker_h": (0.6, 7.0, 5.0)},
    "Rear": {"sensor_c": (13.0, 0.0, 1.4), "sensor_h": (4.0, 2.5, 1.4),
             "blocker_c": (13.2, 0.0, 1.25), "blocker_h": (0.5, 0.7, 1.25)},
    "SideN": {"sensor_c": (3.0, 14.8, 1.4), "sensor_h": (2.5, 4.0, 1.4),
              "blocker_c": (3.0, 14.9, 1.25), "blocker_h": (0.7, 0.5, 1.25)},
    "SideS": {"sensor_c": (3.0, -14.8, 1.4), "sensor_h": (2.5, 4.0, 1.4),
              "blocker_c": (3.0, -14.9, 1.25), "blocker_h": (0.7, 0.5, 1.25)},
}


# ------------------------------------------------------------------------------------------ helpers
def log(m): unreal.log(f"IBPY: {m}")
def warn(m): unreal.log_warning(f"IBPY: WARNING -- {m}")
def err(m): unreal.log_error(f"IBPY: ERROR -- {m}")


def bl_to_ue(p):
    return unreal.Vector(p[0] * 100.0, -p[1] * 100.0, p[2] * 100.0)


def V(t):
    return unreal.Vector(t[0] * 100.0, t[1] * 100.0, t[2] * 100.0)


def all_actors():
    return unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()


def tags_of(a):
    return [str(t) for t in a.tags]


def bounds(a):
    return a.get_actor_bounds(False)


# ------------------------------------------------------------------------------------------ preflight
def preflight():
    log(f"[1/5] PREFLIGHT -- engine {unreal.SystemLibrary.get_engine_version()}")
    files = {"static": os.path.join(SOURCE_DIR, STATIC_FBX)}
    for k in DOOR_KEYS:
        files[k] = os.path.join(SOURCE_DIR, f"SK_Hangar_04_Door_{k}.fbx")
    ok = True
    if DO_IMPORT:
        for k, p in files.items():
            if os.path.isfile(p):
                log(f"  FBX ok   {k}: {os.path.basename(p)} ({os.path.getsize(p) / 1024:.0f} KB)")
            else:
                err(f"FBX missing {k}: {p}")
                ok = False
    cls = unreal.load_class(None, SENSOR_CLASS_PATH)
    if cls:
        log(f"  sensor class ok: {cls.get_name()}")
    else:
        err(f"could not load '{SENSOR_CLASS_PATH}' -- build the C++ (BUILD_IronBreach.bat) and restart the editor.")
        ok = False
    return ok, files, cls


# ------------------------------------------------------------------------------------------ location
def find_location():
    """Returns (location Vector, yaw, placeholders[list of actors], source string) or None."""
    face_yaw = math.degrees(math.atan2(-FACE_DIRECTION[1], -FACE_DIRECTION[0]))   # local -X -> FACE_DIRECTION
    if HANGAR_LOCATION is not None:
        yaw = face_yaw if HANGAR_YAW is None else HANGAR_YAW
        return unreal.Vector(*HANGAR_LOCATION), yaw, [], "explicit HANGAR_LOCATION"
    prev = [a for a in all_actors() if TAG in tags_of(a) and isinstance(a, unreal.StaticMeshActor)]
    if prev and HANGAR_LOCATION is None:                   # re-run: keep exactly where the hangar already is
        a = prev[0]
        l, r = a.get_actor_location(), a.get_actor_rotation()
        log(f"  re-run: reusing the existing hangar transform ({l.x:.0f},{l.y:.0f},{l.z:.0f}) yaw {r.yaw:.1f}")
        return l, (r.yaw if HANGAR_YAW is None else HANGAR_YAW), [], "previous placement"
    sel = [a for a in unreal.EditorLevelLibrary.get_selected_level_actors() if TAG not in tags_of(a)]
    if sel:
        a = sel[0]
        o, e = bounds(a)
        loc = unreal.Vector(o.x, o.y, o.z - e.z)
        log(f"  using SELECTED actor '{a.get_actor_label()}' ({e.x * 2:.0f} x {e.y * 2:.0f} cm) as the placeholder; floor z {loc.z:.0f}")
        return loc, (face_yaw if HANGAR_YAW is None else HANGAR_YAW), [a], f"selected '{a.get_actor_label()}'"
    actors = [a for a in all_actors() if TAG not in tags_of(a)]
    ph = [a for a in actors
          if isinstance(a, unreal.StaticMeshActor)
          and any(h in a.get_actor_label().lower() for h in PLACEHOLDER_HINTS)
          and "_replaced" not in a.get_actor_label().lower()]
    if ph:
        log("  placeholder candidate(s): " + ", ".join(f"'{a.get_actor_label()}'" for a in ph))
        a = ph[0]
        o, e = bounds(a)
        loc = unreal.Vector(o.x, o.y, o.z - e.z)
        log(f"  placeholder '{a.get_actor_label()}' footprint {e.x * 2:.0f} x {e.y * 2:.0f} cm, floor z {loc.z:.0f}")
        return loc, (face_yaw if HANGAR_YAW is None else HANGAR_YAW), [a], f"placeholder '{a.get_actor_label()}'"
    marks = [a for a in actors if a.get_actor_label().startswith(RESERVE_LABEL_PREFIX)]
    if marks:
        x0 = y0 = z1 = 1e12
        x1 = y1 = -1e12
        z1 = -1e12
        for a in marks:
            o, e = bounds(a)
            x0, x1 = min(x0, o.x - e.x), max(x1, o.x + e.x)
            y0, y1 = min(y0, o.y - e.y), max(y1, o.y + e.y)
            z1 = max(z1, o.z + e.z)
        loc = unreal.Vector((x0 + x1) / 2, (y0 + y1) / 2, z1 - 150.0)       # markers are 150 cm thick, top at deck+1.5 cm
        log(f"  hangar reserve markers: {len(marks)}; outline {x1 - x0:.0f} x {y1 - y0:.0f} cm (hangar needs ~3800 x 3800)")
        return loc, (face_yaw if HANGAR_YAW is None else HANGAR_YAW), [], "Reserve_Edge markers"
    return None


# ------------------------------------------------------------------------------------------ import
def _ui(skeletal):
    ui = unreal.FbxImportUI()
    ui.set_editor_property("import_mesh", True)
    ui.set_editor_property("import_textures", False)
    ui.set_editor_property("import_materials", True)
    ui.set_editor_property("import_as_skeletal", bool(skeletal))
    try:
        ui.set_editor_property("mesh_type_to_import",
                               unreal.FBXImportType.FBXIT_SKELETAL_MESH if skeletal else unreal.FBXImportType.FBXIT_STATIC_MESH)
    except Exception as e:
        log(f"  (mesh_type_to_import not set: {e})")
    ui.set_editor_property("automated_import_should_detect_type", False)
    if skeletal:
        ui.set_editor_property("import_animations", True)
        ui.set_editor_property("create_physics_asset", False)
    else:
        ui.set_editor_property("import_animations", False)
        sm = ui.static_mesh_import_data
        sm.set_editor_property("combine_meshes", True)
        sm.set_editor_property("auto_generate_collision", False)
        sm.set_editor_property("generate_lightmap_u_vs", False)
        sm.set_editor_property("remove_degenerates", True)
        if USE_NANITE:
            try:
                sm.set_editor_property("build_nanite", True)
            except Exception as e:
                log(f"  (Nanite not enabled on import: {e}) -- tick Enable Nanite Support by hand")
    return ui


def import_fbx(path, dest_path, dest_name, skeletal):
    t = unreal.AssetImportTask()
    t.set_editor_property("filename", path)
    t.set_editor_property("destination_path", dest_path)
    t.set_editor_property("destination_name", dest_name)
    t.set_editor_property("replace_existing", True)
    t.set_editor_property("replace_existing_settings", True)
    t.set_editor_property("automated", True)
    t.set_editor_property("save", False)
    t.set_editor_property("options", _ui(skeletal))
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
    assets = [a for a in (unreal.EditorAssetLibrary.load_asset(str(p)) for p in t.get_editor_property("imported_object_paths")) if a]
    log(f"  imported {os.path.basename(path)} -> " + ", ".join(f"{a.get_name()}[{a.get_class().get_name()}]" for a in assets))
    return assets


def do_import(files):
    log("[2/5] IMPORT")
    res = {"doors": {}}
    assets = import_fbx(files["static"], f"{DEST_ROOT}/Static", "SM_Hangar_04", False)
    meshes = [a for a in assets if isinstance(a, unreal.StaticMesh)]
    if not meshes:
        err("static import produced no StaticMesh")
        return None
    mesh = res["static"] = meshes[0]
    try:
        hulls = mesh.get_editor_property("body_setup").get_editor_property("agg_geom").get_editor_property("convex_elems")
        log(f"  convex collision hulls: {len(hulls)} (expect 13)")
        if len(hulls) != 13:
            warn("hull count is not 13 -- check Show > Simple Collision in the Static Mesh editor")
    except Exception as e:
        log(f"  (could not read hull count: {e}) -- check Show > Simple Collision (expect 13)")
    ext = mesh.get_bounds().box_extent
    log(f"  bounds half extents cm: ({ext.x:.0f}, {ext.y:.0f}, {ext.z:.0f})  expect ~(1450, 1685, 1057)")
    res["mats"] = mats_mod.build_all(f"{DEST_ROOT}/Materials", prefix="M_Hangar04_")
    mats_mod.apply_to_static_mesh(mesh, res["mats"])
    for k in DOOR_KEYS:
        name = f"SK_Hangar_04_Door_{k}"
        assets = import_fbx(files[k], f"{DEST_ROOT}/Doors/{k}", name, True)
        sk = [a for a in assets if isinstance(a, unreal.SkeletalMesh)]
        an = [a for a in assets if isinstance(a, unreal.AnimSequence)]
        if not sk or not an:
            err(f"door {k}: missing SkeletalMesh or AnimSequence after import")
            return None
        anim = an[0]
        old = anim.get_path_name().split(".")[0]
        new = f"{DEST_ROOT}/Doors/{k}/AS_Hangar_04_Door_{k}_Open"
        if old != new:
            if unreal.EditorAssetLibrary.does_asset_exist(new):
                unreal.EditorAssetLibrary.delete_asset(new)
            if unreal.EditorAssetLibrary.rename_asset(old, new):
                anim = unreal.EditorAssetLibrary.load_asset(new)
            else:
                warn(f"door {k}: could not rename '{old}'")
        log(f"  door {k}: anim '{anim.get_name()}' {anim.get_editor_property('sequence_length'):.2f}s")
        res["doors"][k] = (sk[0], anim)
    return res


def load_existing():
    log("[2/5] IMPORT skipped -- loading previous assets")
    mesh = unreal.EditorAssetLibrary.load_asset(f"{DEST_ROOT}/Static/SM_Hangar_04")
    if not mesh:
        err("previous SM_Hangar_04 not found")
        return None
    res = {"static": mesh, "doors": {}, "mats": mats_mod.build_all(f"{DEST_ROOT}/Materials", prefix="M_Hangar04_")}
    mats_mod.apply_to_static_mesh(mesh, res["mats"])
    for k in DOOR_KEYS:
        sk = unreal.EditorAssetLibrary.load_asset(f"{DEST_ROOT}/Doors/{k}/SK_Hangar_04_Door_{k}")
        an = unreal.EditorAssetLibrary.load_asset(f"{DEST_ROOT}/Doors/{k}/AS_Hangar_04_Door_{k}_Open")
        if not (sk and an):
            err(f"door {k}: previous import not found")
            return None
        res["doors"][k] = (sk, an)
    return res


# ------------------------------------------------------------------------------------------ spawn
def tag(a):
    a.set_editor_property("tags", [unreal.Name(TAG)])


def spawn(res, cls, loc, yaw):
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    n = 0
    for a in sub.get_all_level_actors():
        if TAG in tags_of(a):
            sub.destroy_actor(a)
            n += 1
    if n:
        log(f"  removed {n} actor(s) from a previous run")
    b = sub.spawn_actor_from_class(unreal.StaticMeshActor, loc, unreal.Rotator(0.0, 0.0, yaw))
    if not b:
        err("spawn of the building failed")
        return None, {}
    b.static_mesh_component.set_static_mesh(res["static"])
    b.set_actor_scale3d(unreal.Vector(PLACE_SCALE, PLACE_SCALE, PLACE_SCALE))
    b.set_actor_label(LABEL)
    try:
        b.set_folder_path(FOLDER)
    except Exception:
        pass
    tag(b)
    log(f"  spawned '{LABEL}' at ({loc.x:.0f},{loc.y:.0f},{loc.z:.0f}) yaw {yaw:.1f}")
    doors = {}
    for k in DOOR_KEYS:
        cfg = DOORS[k]
        sk, anim = res["doors"][k]
        d = sub.spawn_actor_from_class(cls, loc, unreal.Rotator(0.0, 0.0, yaw))
        if not d:
            err(f"spawn of door {k} failed")
            continue
        d.set_actor_scale3d(unreal.Vector(PLACE_SCALE, PLACE_SCALE, PLACE_SCALE))
        d.configure_door(sk, anim)
        d.configure_volumes(bl_to_ue(cfg["sensor_c"]), V(cfg["sensor_h"]), bl_to_ue(cfg["blocker_c"]), V(cfg["blocker_h"]),
                            unreal.Rotator(0.0, 0.0, 0.0))
        d.set_editor_property("close_delay", CLOSE_DELAY if k == "Main" else 1.5)
        d.set_editor_property("open_duration_override", OPEN_SECONDS[k])
        d.set_editor_property("player_pawns_only", PLAYER_PAWNS_ONLY)
        mats_mod.apply_to_component(d.get_editor_property("door_mesh"), res["mats"])
        d.set_actor_label(f"Hangar_Door_{k}")
        try:
            d.set_folder_path(FOLDER + "/Hangar Doors")
        except Exception:
            pass
        tag(d)
        d.attach_to_actor(b, "", unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD,
                          unreal.AttachmentRule.KEEP_WORLD, False)
        doors[k] = d
        log(f"  sensor door '{k}': anim '{anim.get_name()}', open {OPEN_SECONDS[k]}s")
    return b, doors


def park(a):
    a.set_actor_label(a.get_actor_label() + "_REPLACED")
    a.set_actor_hidden_in_game(True)
    a.set_actor_enable_collision(False)
    try:
        a.set_is_temporarily_hidden_in_editor(True)
        a.set_folder_path(PARK_FOLDER)
    except Exception:
        pass
    log(f"  parked placeholder '{a.get_actor_label()}'")


def verify(b, doors):
    log("[5/5] VERIFY")
    o, e = bounds(b)
    log(f"  hangar bounds centre ({o.x:.0f},{o.y:.0f},{o.z:.0f}) half ({e.x:.0f},{e.y:.0f},{e.z:.0f}) cm")
    for k, d in doors.items():
        s = d.get_editor_property("sensor_box").get_world_location()
        bl = d.get_editor_property("blocker_box").get_world_location()
        log(f"  door {k}: sensor ({s.x:.0f},{s.y:.0f},{s.z:.0f}) blocker ({bl.x:.0f},{bl.y:.0f},{bl.z:.0f})")
    log("  PIE: walk to each door; Output Log shows 'SensorDoor ...' lines (LogIronBreach Verbose).")


def main():
    log("=== ib_place_hangar START ===" + ("  [DRY RUN]" if DRY_RUN else ""))
    if SET_VERBOSE_LOG:
        try:
            unreal.SystemLibrary.execute_console_command(None, "Log LogIronBreach Verbose")
        except Exception:
            pass
    ok, files, cls = preflight()
    if not ok:
        err("preflight failed -- nothing changed.")
        return
    log("[3/5] LOCATE")
    found = find_location()
    if not found:
        err("no placeholder (labels containing %s), no '%s*' markers and no HANGAR_LOCATION set -- nothing changed. "
            "SELECT the white cube / reserve actor in the viewport and re-run, or set HANGAR_LOCATION=(x,y,z) in the script (cm; z = floor)."
            % (PLACEHOLDER_HINTS, RESERVE_LABEL_PREFIX))
        return
    loc, yaw, placeholders, src = found
    log(f"  using {src}: ({loc.x:.0f},{loc.y:.0f},{loc.z:.0f}) yaw {yaw:.1f}")
    if DRY_RUN:
        log("DRY RUN: nothing imported or spawned.")
        return
    res = do_import(files) if DO_IMPORT else load_existing()
    if not res:
        err("import failed -- level untouched.")
        return
    log("[4/5] SPAWN")
    b, doors = spawn(res, cls, loc, yaw)
    if not b:
        return
    for p in placeholders:
        park(p)
    verify(b, doors)
    unreal.EditorLevelLibrary.set_selected_level_actors([b] + list(doors.values()))
    log("=== DONE. Nothing saved: review in the viewport, then File > Save All. ===")


main()
