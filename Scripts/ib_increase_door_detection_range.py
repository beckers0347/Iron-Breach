"""
Iron Breach -- increase the overlap-detection range on every BP_DoorFrame
instance in CarrowGateGarrison (the six building doors + BP_MainGateDoor).

Runs directly in the editor's Python console:
    exec(open(r"X:\IronBreach\Scripts\ib_increase_door_detection_range.py").read())

Multiplies each instance's current "Door Detection Adjust" value rather than
setting a flat override, so any building that was already hand-tuned keeps
its relative sizing -- just bigger across the board. DETECTION_MULTIPLIER
below controls how much bigger; edit and rerun to taste.

Property-name caveat: "door_detection_adjust" is a best-guess snake_case
translation of the Blueprint variable's display name ("Door Detection
Adjust"), not confirmed live. Every instance is handled independently and
logs OK/FAIL, so a wrong name shows up clearly instead of failing silently.
"""
import os
import traceback
import unreal

EAS = unreal.EditorActorSubsystem()
LEVEL = os.environ.get("IB_LEVEL", "/Game/LevelPrototyping/CarrowGateGarrison")
DOOR_CLASS_NAME = "BP_DoorFrame_C"
DETECTION_PROP_CANDIDATES = ["door_detection_adjust", "detection_adjust", "door_detection_range"]
DETECTION_MULTIPLIER = 1.5


def log(msg):
    unreal.log(f"IBPY: {msg}")


def find_working_prop_name(actor):
    """Try each candidate property name against this actor; return the first
    that reads back a value without throwing, else None."""
    for name in DETECTION_PROP_CANDIDATES:
        try:
            val = actor.get_editor_property(name)
            return name, val
        except Exception:
            continue
    return None, None


def main():
    log(f"=== increasing door detection range x{DETECTION_MULTIPLIER} in {LEVEL} ===")
    unreal.EditorLoadingAndSavingUtils.load_map(LEVEL)

    doors = [a for a in EAS.get_all_level_actors() if a.get_class().get_name() == DOOR_CLASS_NAME]
    log(f"INFO found {len(doors)} BP_DoorFrame instance(s)")

    if not doors:
        log(f"FAIL no actors of class {DOOR_CLASS_NAME} found -- check the class name is right "
            "(Select one of the doors in the editor and check its class in the Details panel header).")
        return

    ok_count = 0
    fail_count = 0
    for actor in doors:
        label = actor.get_actor_label()
        prop_name, current = find_working_prop_name(actor)
        if prop_name is None:
            log(f"FAIL {label}: none of {DETECTION_PROP_CANDIDATES} could be read on this actor -- "
                "check the exact variable name in the Blueprint editor and add it to "
                "DETECTION_PROP_CANDIDATES at the top of this script.")
            fail_count += 1
            continue
        try:
            if isinstance(current, unreal.Vector):
                new_value = unreal.Vector(current.x * DETECTION_MULTIPLIER,
                                           current.y * DETECTION_MULTIPLIER,
                                           current.z * DETECTION_MULTIPLIER)
            else:
                new_value = current * DETECTION_MULTIPLIER
            actor.set_editor_property(prop_name, new_value)
            log(f"OK   {label}: {prop_name} {current} -> {new_value}")
            ok_count += 1
        except Exception as e:
            log(f"FAIL {label}: found {prop_name}={current} but could not set it ({e})")
            fail_count += 1

    saved = unreal.EditorLoadingAndSavingUtils.save_current_level()
    log(f"INFO level save attempted: {saved}")
    log(f"=== done: {ok_count} doors updated, {fail_count} failed ===")


try:
    main()
except Exception:
    log("FAIL unhandled exception")
    unreal.log_error(traceback.format_exc())
