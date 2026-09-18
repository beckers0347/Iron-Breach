"""
IBPY: ib_diag_doorway_blocked.py

READ-ONLY. You said you can start walking into a doorway but then get
stopped -- that means the carved opening exists (good, the boolean
subtract worked) but something is blocking further in, most likely
because the cutter box's depth wasn't enough to clear ALL the geometry
along that path (an interior wall, a secondary structural mesh, or the
"fill_holes" cap where the cutter's far end stopped short still inside
solid geometry).

This traces INTO each building from its current DoorFrame actor's live
position/rotation and reports exactly where (if anywhere) it hits solid
collision -- so we can see how much farther the cutter needs to reach,
rather than guessing at a bigger depth number blind.

For each building+door pair, it:
  1. Reads the door actor's CURRENT world location/rotation (after your
     manual repositioning -- this does NOT use any hardcoded/stale
     coordinates).
  2. Traces a line from a bit above floor height, starting just outside
     the door on each side (forward and backward along the door's own
     forward axis), continuing a long distance (3000cm) into the
     building, using the SAME complex collision your buildings actually
     use (trace_complex=True).
  3. Logs the first hit (if any) on each side: distance from the door,
     world location, and which actor/component was hit.

This tells us, per building: which direction actually leads inward, how
far the player can currently walk before hitting something, and (once we
compare that to the DOOR_CUT_DEPTH_CM used) how much deeper the cutter
needs to reach to clear it.

Touches nothing.

HOW TO RUN:
  py "X:/IronBreach/Scripts/ib_diag_doorway_blocked.py"
Paste back the full output.
"""

import unreal

DOOR_ACTOR_LABELS = [
    "Medical_DoorFrame",
    "Barracks_DoorFrame",
    "Armory_DoorFrame",
    "Command_DoorFrame",
    "Mess_Hall_DoorFrame",
]

TRACE_DISTANCE_CM = 3000.0
TRACE_HEIGHT_OFFSET_CM = 100.0  # roughly chest height above the door actor's own Z
START_BACKOFF_CM = 150.0        # start the trace a bit before the door so we don't false-hit the door frame itself


def log(msg):
    unreal.log(f"IBPY: {msg}")


def get_actor_by_label(label):
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for a in subsystem.get_all_level_actors():
        if a.get_actor_label() == label:
            return a
    return None


def get_prop_any(obj, names, default=None):
    """Different UE Python-binding versions expose HitResult fields under
    slightly different snake_case names -- try each candidate rather than
    guess wrong and crash again."""
    for n in names:
        try:
            return obj.get_editor_property(n)
        except Exception:
            continue
    return default


def trace_direction(world, start, direction, label):
    end = start + direction * TRACE_DISTANCE_CM
    result = unreal.SystemLibrary.line_trace_single(
        world,
        start,
        end,
        unreal.TraceTypeQuery.ECC_VISIBILITY,
        True,   # trace_complex -- use the real complex-as-simple geometry
        [],     # actors_to_ignore
        unreal.DrawDebugTrace.NONE,
        True,   # ignore_self (there's no "self" here, harmless)
        unreal.LinearColor(1, 0, 0, 1),
        unreal.LinearColor(0, 1, 0, 1),
        0.0,
    )
    # line_trace_single returns either (bool, HitResult) or just HitResult
    # depending on binding version -- handle both.
    if isinstance(result, tuple):
        success, hit_result = result
    else:
        hit_result = result
        success = None

    is_blocking = get_prop_any(hit_result, ["blocking_hit", "b_blocking_hit"], False)
    if success is not None:
        is_blocking = bool(is_blocking) or bool(success)

    if is_blocking:
        hit_loc = get_prop_any(hit_result, ["location", "impact_point"])
        hit_actor = get_prop_any(hit_result, ["hit_actor", "actor"])
        hit_component = get_prop_any(hit_result, ["hit_component", "component"])
        if hit_loc is not None:
            hit_dist = (unreal.Vector(hit_loc.x, hit_loc.y, hit_loc.z) - start).length()
            loc_str = f"({hit_loc.x:.1f},{hit_loc.y:.1f},{hit_loc.z:.1f})"
        else:
            hit_dist = float("nan")
            loc_str = "?"
        hit_actor_label = hit_actor.get_actor_label() if hit_actor else "?"
        hit_comp_name = hit_component.get_name() if hit_component else "?"
        log(f"    [{label}] HIT at distance={hit_dist:.1f}cm, loc={loc_str}, "
            f"actor='{hit_actor_label}' component='{hit_comp_name}'")
    else:
        log(f"    [{label}] NO HIT within {TRACE_DISTANCE_CM:.0f}cm -- clear that far.")


def main():
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()

    for door_label in DOOR_ACTOR_LABELS:
        door = get_actor_by_label(door_label)
        if not door:
            log(f"[{door_label}] SKIPPED -- door actor not found.")
            continue

        door_loc = door.get_actor_location()
        forward = door.get_actor_forward_vector()
        trace_z = door_loc.z + TRACE_HEIGHT_OFFSET_CM

        log(f"[{door_label}] door_loc=({door_loc.x:.1f},{door_loc.y:.1f},{door_loc.z:.1f}) "
            f"forward=({forward.x:.2f},{forward.y:.2f},{forward.z:.2f})")

        start_fwd = unreal.Vector(
            door_loc.x - forward.x * START_BACKOFF_CM,
            door_loc.y - forward.y * START_BACKOFF_CM,
            trace_z,
        )
        trace_direction(world, start_fwd, unreal.Vector(forward.x, forward.y, 0.0), "+forward")

        start_bwd = unreal.Vector(
            door_loc.x + forward.x * START_BACKOFF_CM,
            door_loc.y + forward.y * START_BACKOFF_CM,
            trace_z,
        )
        trace_direction(world, start_bwd, unreal.Vector(-forward.x, -forward.y, 0.0), "-forward")

    log("Done. Nothing was modified.")


main()
