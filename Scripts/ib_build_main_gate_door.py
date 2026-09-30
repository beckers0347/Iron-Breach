"""
Iron Breach -- add an automatic double door to the Main Gate archway.

Runs headless (zzcharwatch: "py ib_build_main_gate_door.py"). Idempotent: if
BP_MainGateDoor already exists in the level, this repositions/reconfigures
it instead of spawning a duplicate.

What this does:
  1. Finds 01_Main Gate_Pylon_L / _Pylon_R / _Lintel in CarrowGateGarrison.
  2. Computes the gate opening's width/center/facing from those actors.
  3. Spawns (or updates) a BP_DoorFrame instance there -- the same parametric
     door Blueprint already driving the automatic open/close on all six
     buildings (overlap-triggered, Timeline-animated, supports a two-leaf
     "split door").
  4. Best-effort sets its exposed instance properties (Split Door, Door Size,
     Draw Door Frame, etc.) to fit the gate.

IMPORTANT: BP_DoorFrame's Blueprint-exposed variable names were read from the
asset's friendly display strings (e.g. "Draw Door Frame?"), not confirmed
live against the Python API's actual snake_case property names -- Unreal
usually derives them predictably (spaces -> underscores, lowercased,
punctuation stripped) but that's a best guess, not a guarantee. Every
property set below is wrapped individually and logged OK/FAIL so nothing
here fails silently -- check the log output and fix any FAIL lines by hand
in the Details panel (they'll be listed clearly at the end).
"""
import os
import traceback
import unreal

EAL = unreal.EditorAssetLibrary
EAS = unreal.EditorActorSubsystem()

LEVEL = os.environ.get("IB_LEVEL", "/Game/LevelPrototyping/CarrowGateGarrison")
DOORFRAME_BP_PATH = "/Game/LevelPrototyping/Interactable/Door/BP_DoorFrame"
NEW_DOOR_LABEL = "BP_MainGateDoor"

# Fallback sizing used only where the gate geometry can't tell us -- these are
# guesses (~4m wide leaf pair, ~4.5m tall), meant to get close enough to look
# at in the editor and adjust, not to be exactly right.
DEFAULT_DOOR_HEIGHT_CM = 450.0
DEFAULT_DOOR_THICKNESS_CM = 15.0
DEFAULT_FRAME_SCALE = 1.0


def log(msg):
    unreal.log(f"IBPY: {msg}")


def find_actor_by_label(actors, label):
    for a in actors:
        if a.get_actor_label() == label:
            return a
    return None


def try_set(actor, prop_name, value, results):
    """Best-effort set_editor_property; records OK/FAIL for the summary."""
    try:
        actor.set_editor_property(prop_name, value)
        results.append((prop_name, value, True, None))
        log(f"OK   set {prop_name} = {value}")
    except Exception as e:
        results.append((prop_name, value, False, str(e)))
        log(f"FAIL set {prop_name} = {value}  ({e})")


def main():
    log(f"=== main gate door: loading {LEVEL} ===")
    unreal.EditorLoadingAndSavingUtils.load_map(LEVEL)

    actors = EAS.get_all_level_actors()

    pylon_l = find_actor_by_label(actors, "01_Main Gate_Pylon_L")
    pylon_r = find_actor_by_label(actors, "01_Main Gate_Pylon_R")
    lintel = find_actor_by_label(actors, "01_Main Gate_Lintel")

    if not pylon_l or not pylon_r:
        log("FAIL could not find 01_Main Gate_Pylon_L and/or _Pylon_R by actor label -- "
            "check the exact labels in the Outliner (Main Gate naming may differ from "
            "what this script expects) and adjust the find_actor_by_label calls above.")
        return

    loc_l = pylon_l.get_actor_location()
    loc_r = pylon_r.get_actor_location()
    ref_actor = lintel if lintel else pylon_l
    ref_rot = ref_actor.get_actor_rotation()

    center = unreal.Vector(
        (loc_l.x + loc_r.x) / 2.0,
        (loc_l.y + loc_r.y) / 2.0,
        (loc_l.z + loc_r.z) / 2.0,
    )
    gate_width = ((loc_l.x - loc_r.x) ** 2 + (loc_l.y - loc_r.y) ** 2) ** 0.5
    gate_height = DEFAULT_DOOR_HEIGHT_CM
    if lintel:
        lintel_z = lintel.get_actor_location().z
        computed_height = abs(lintel_z - min(loc_l.z, loc_r.z))
        if computed_height > 50.0:  # sanity floor -- ignore obviously-wrong reads
            gate_height = computed_height

    log(f"INFO Pylon_L={loc_l}  Pylon_R={loc_r}")
    log(f"INFO computed center={center}  width={gate_width:.1f}cm  height={gate_height:.1f}cm  rot={ref_rot}")

    # --- find or spawn the door actor -----------------------------------
    door_bp = EAL.load_asset(DOORFRAME_BP_PATH) if EAL.does_asset_exist(DOORFRAME_BP_PATH) else None
    if not door_bp:
        log(f"FAIL BP_DoorFrame not found at {DOORFRAME_BP_PATH} -- check the path.")
        return

    existing = find_actor_by_label(EAS.get_all_level_actors(), NEW_DOOR_LABEL)
    if existing:
        log(f"INFO {NEW_DOOR_LABEL} already exists -- repositioning/reconfiguring it instead of spawning a duplicate.")
        door_actor = existing
        door_actor.set_actor_location(center, False, False)
        door_actor.set_actor_rotation(ref_rot, False)
    else:
        door_actor = EAS.spawn_actor_from_object(door_bp, center, ref_rot)
        if not door_actor:
            log("FAIL spawn_actor_from_object returned None")
            return
        door_actor.set_actor_label(NEW_DOOR_LABEL)
        log(f"OK   spawned {NEW_DOOR_LABEL} at {center}")

    # The door leaf's default orientation reads 90 degrees off from the gate's
    # facing (confirmed visually: it was lying across the walkway instead of
    # spanning the opening) -- correct that here rather than relying on a
    # guessed rotation. If this comes out backwards after a rerun, flip the
    # sign on ROTATION_CORRECTION_YAW below and rerun again.
    ROTATION_CORRECTION_YAW = 90.0
    corrected_rot = unreal.Rotator(ref_rot.roll, ref_rot.pitch, ref_rot.yaw + ROTATION_CORRECTION_YAW)
    door_actor.set_actor_rotation(corrected_rot, False)
    log(f"OK   corrected rotation to {corrected_rot}")

    # Grow the door to fill the gate opening using a guaranteed core Actor API
    # (set_actor_scale3d) instead of a guessed Blueprint variable name -- this
    # measures the door's current world-space bounds and scales it up so its
    # width/height actually match the archway, regardless of what BP_DoorFrame
    # calls its own size properties internally.
    origin, extent = door_actor.get_actor_bounds(False)
    current_width = extent.y * 2.0   # across the opening
    current_height = extent.z * 2.0  # floor to lintel
    current_scale = door_actor.get_actor_scale3d()
    if current_width > 1.0 and current_height > 1.0:
        width_factor = gate_width / current_width
        height_factor = gate_height / current_height
        new_scale = unreal.Vector(current_scale.x, current_scale.y * width_factor, current_scale.z * height_factor)
        door_actor.set_actor_scale3d(new_scale)
        log(f"OK   grew door: bounds were {current_width:.1f}x{current_height:.1f}cm, "
            f"target {gate_width:.1f}x{gate_height:.1f}cm, new scale={new_scale}")
    else:
        log(f"FAIL door bounds read too small to scale from ({current_width:.1f}x{current_height:.1f}) -- "
            "grow it by hand via the Scale tool instead.")

    # --- best-effort property configuration ------------------------------
    # Guessed snake_case names for BP_DoorFrame's exposed variables (see the
    # module docstring -- verify against FAIL lines below).
    results = []
    try_set(door_actor, "split_door", True, results)
    try_set(door_actor, "draw_door_frame", False, results)
    try_set(door_actor, "door_frame_scale", DEFAULT_FRAME_SCALE, results)
    try_set(door_actor, "door_thickness", DEFAULT_DOOR_THICKNESS_CM, results)
    try_set(door_actor, "door_size", unreal.Vector(gate_width, DEFAULT_DOOR_THICKNESS_CM, gate_height), results)

    saved = EAL.save_asset(LEVEL) if EAL.does_asset_exist(LEVEL) else unreal.EditorLoadingAndSavingUtils.save_current_level()
    log(f"INFO level save attempted: {saved}")

    ok_count = sum(1 for _, _, ok, _ in results if ok)
    fail_count = len(results) - ok_count
    log(f"=== main gate door done: {ok_count} properties set, {fail_count} failed ===")
    if fail_count:
        log("=== FAILED PROPERTIES -- set these by hand in the Details panel: ===")
        for name, value, ok, err in results:
            if not ok:
                log(f"    {name} (tried to set {value}) -- {err}")


try:
    main()
except Exception:
    log("FAIL unhandled exception")
    unreal.log_error(traceback.format_exc())
