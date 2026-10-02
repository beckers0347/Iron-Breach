"""gen_common.py - shared helpers for the Thornfield level generation scripts.

Run inside the Unreal Editor (Python Editor Script Plugin enabled).
Every script does:   sys.path.insert(0, <this folder>);  import gen_common as G
"""
import os
import json
import math
import time
import unreal

TAG_ALL = "GEN_Generated"
_RESULTS = []          # (name, ok, detail) for the VERIFY summary
_LOG_PATH = None
_PROJECT_TAG = "Thornfield"


class GenError(Exception):
    """Raised for fatal generation errors; scripts catch it, log it and stop."""


# --------------------------------------------------------------------------- paths
def tools_root():
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(here)
    if os.path.isdir(os.path.join(root, "config")):
        return root
    return os.path.normpath(os.path.join(unreal.Paths.project_dir(), "LevelGenTools"))


def project_dir():
    return os.path.normpath(unreal.Paths.project_dir())


def config_path(name):
    return os.path.join(tools_root(), "config", name)


# --------------------------------------------------------------------------- logging
def init_log(script_name):
    """Open a per-run log file in LevelGenTools/logs and read the project tag."""
    global _LOG_PATH, _PROJECT_TAG
    _RESULTS.clear()
    try:
        _PROJECT_TAG = load_json("level.json").get("project_tag", _PROJECT_TAG)
    except Exception:
        pass
    logs = os.path.join(tools_root(), "logs")
    os.makedirs(logs, exist_ok=True)
    _LOG_PATH = os.path.join(logs, "%s_%s.log" % (script_name, time.strftime("%Y%m%d_%H%M%S")))
    log("=== %s start ===" % script_name)
    return _LOG_PATH


def _write(line):
    if _LOG_PATH:
        try:
            with open(_LOG_PATH, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception:
            pass


def log(msg):
    line = "[%s] %s" % (_PROJECT_TAG, msg)
    unreal.log(line)
    _write(line)


def warn(msg):
    line = "[%s] WARN: %s" % (_PROJECT_TAG, msg)
    unreal.log_warning(line)
    _write(line)


def err(msg):
    line = "[%s] ERROR: %s" % (_PROJECT_TAG, msg)
    unreal.log_error(line)
    _write(line)


def verify(name, ok, detail=""):
    """Print and record one VERIFY line. Returns ok."""
    status = "PASS" if ok else "FAIL"
    line = "VERIFY: %s %s%s" % (name, status, (" (%s)" % detail) if detail else "")
    (log if ok else err)(line)
    _RESULTS.append((name, bool(ok), detail))
    return bool(ok)


def summary():
    """Print the final tally. Returns True when nothing failed."""
    fails = [r for r in _RESULTS if not r[1]]
    log("SUMMARY: %d checks, %d PASS, %d FAIL" % (len(_RESULTS), len(_RESULTS) - len(fails), len(fails)))
    for name, _, detail in fails:
        err("  FAILED: %s %s" % (name, detail))
    if _LOG_PATH:
        log("Log file: %s" % _LOG_PATH)
    return not fails


# --------------------------------------------------------------------------- config
def load_json(name):
    path = config_path(name)
    if not os.path.isfile(path):
        raise GenError("Config file missing: %s" % path)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# --------------------------------------------------------------------------- assets
def assert_asset_exists(path):
    """Return the loaded asset or raise GenError (never guess paths)."""
    if not path:
        raise GenError("Empty asset path")
    if not unreal.EditorAssetLibrary.does_asset_exist(path):
        raise GenError("Asset does not exist: %s" % path)
    asset = unreal.EditorAssetLibrary.load_asset(path)
    if asset is None:
        raise GenError("Asset failed to load: %s" % path)
    return asset


def get_bounds(asset):
    """Return (size, origin) as unreal.Vector for a StaticMesh, in cm."""
    try:
        box = asset.get_bounding_box()
        size = box.max - box.min
        origin = (box.max + box.min) * 0.5
        return size, origin
    except Exception:
        b = asset.get_bounds()
        return b.box_extent * 2.0, b.origin


def fmt_size(v):
    return "%.0fx%.0fx%.0f" % (v.x, v.y, v.z)


# --------------------------------------------------------------------------- actors
def actor_subsystem():
    return unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def tag_actor(actor, phase):
    tags = [str(t) for t in actor.tags]
    for t in (TAG_ALL, "GEN_Phase%s" % phase):
        if t not in tags:
            tags.append(t)
    actor.set_editor_property("tags", [unreal.Name(t) for t in tags])
    try:
        actor.set_folder_path("Generated/Phase%s" % phase)
    except Exception:
        pass


def actors_with_tag(tag):
    out = []
    for a in actor_subsystem().get_all_level_actors():
        if unreal.Name(tag) in a.tags:
            out.append(a)
    return out


def delete_actors_with_tag(tag):
    """Delete every level actor carrying the tag. Returns the number removed."""
    subsys = actor_subsystem()
    victims = actors_with_tag(tag)
    for a in victims:
        subsys.destroy_actor(a)
    return len(victims)


def cleanup_phase(phase):
    n = delete_actors_with_tag("GEN_Phase%s" % phase)
    log("Cleanup: removed %d previous GEN_Phase%s actors" % (n, phase))
    return n


def spawn_static_mesh(path, loc, rot, scale, label, phase):
    """Spawn a StaticMeshActor showing the mesh at `path`.
    loc = (x,y,z) cm, rot = (pitch,yaw,roll) deg, scale = (x,y,z)."""
    mesh = assert_asset_exists(path)
    actor = actor_subsystem().spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(*loc), unreal.Rotator(roll=rot[2], pitch=rot[0], yaw=rot[1]))
    if actor is None:
        raise GenError("Spawn failed for %s" % path)
    actor.static_mesh_component.set_static_mesh(mesh)
    actor.set_actor_scale3d(unreal.Vector(*scale))
    actor.set_actor_label(label)
    tag_actor(actor, phase)
    return actor


def spawn_by_class(cls, loc, rot, label, phase):
    actor = actor_subsystem().spawn_actor_from_class(
        cls, unreal.Vector(*loc), unreal.Rotator(roll=rot[2], pitch=rot[0], yaw=rot[1]))
    if actor is None:
        raise GenError("Spawn failed for class %s" % cls)
    actor.set_actor_label(label)
    tag_actor(actor, phase)
    return actor


# --------------------------------------------------------------------------- math
def plan_to_world(level, x, y):
    """Plan coords (cm, +Y north) -> UE world (cm). UE is left-handed, so a plan that is
    viewed from above with north up needs north = -Y."""
    if level.get("plan_flip_y"):
        return x, level["bounds_cm"]["max"][1] - y
    return x, y



def facing_to_yaw(layout, facing, offset_deg, native_front_yaw_deg):
    """UE yaw (deg) that turns a mesh whose native front is native_front_yaw_deg
    so that it faces compass direction `facing` (+ offset)."""
    vx, vy = layout["facing_vectors"][facing]
    target = math.degrees(math.atan2(vy, vx))
    return target - native_front_yaw_deg + offset_deg
