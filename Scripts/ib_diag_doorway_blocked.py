"""
IBPY: ib_diag_doorway_blocked.py  (v2)

READ-ONLY. v1 traced along each door actor's own forward vector and got
"NO HIT" in both directions for all 5 buildings -- which itself is the
finding: after you manually repositioned the doors, a door's own forward
axis apparently no longer points through the wall (probably roughly
parallel to it now), so that trace never actually crossed the building
mass. That explains nothing about the real block.

v2 traces toward each building's own known center instead (from the
last ib_survey_garrison.py run -- reliable ground truth, independent of
door rotation), which is guaranteed to actually cross the building. For
each door it:
  1. Traces from just outside the door, straight toward the building's
     center and out the far side (5000cm, long enough to clear any of
     these buildings twice over).
  2. Repeats that at 3 heights (ankle/chest/head, relative to the door's
     own Z) and 3 lateral offsets (centerline, and +/-80cm to each side,
     roughly capsule-width) -- 9 traces per door -- so a narrow blocking
     sliver near one edge of the doorway isn't missed by a single
     centerline trace.
  3. Logs every hit: distance from the door, world location, which
     actor/component. A short first-hit distance on some traces but not
     others tells us whether it's a full wall (all 9 hit close) or a
     narrow snag (only the offset traces hit, or only one height).

Touches nothing.

HOW TO RUN:
  py "X:/IronBreach/Scripts/ib_diag_doorway_blocked.py"
Paste back the full output.
"""

import math
import unreal

# name -> (door_actor_label, building_center_xy) -- centers from the last
# ib_survey_garrison.py run, independent of door position/rotation.
BUILDINGS = [
    {"name": "Medical", "door_actor": "Medical_DoorFrame", "center_xy": (9397.6, 6241.2)},
    {"name": "Barracks", "door_actor": "Barracks_DoorFrame", "center_xy": (3310.0, -1604.0)},
    {"name": "Armory", "door_actor": "Armory_DoorFrame", "center_xy": (6893.0, 8733.0)},
    {"name": "Command", "door_actor": "Command_DoorFrame", "center_xy": (518.0, 5770.0)},
    {"name": "Mess_Hall", "door_actor": "Mess_Hall_DoorFrame", "center_xy": (318.0, 2854.0)},
]

TRACE_DISTANCE_CM = 5000.0
START_BACKOFF_CM = 150.0
HEIGHT_OFFSETS_CM = [30.0, 100.0, 170.0]   # ankle / chest / head, above door actor's own Z
LATERAL_OFFSETS_CM = [-80.0, 0.0, 80.0]    # left / center / right of the travel line


def log(msg):
    unreal.log(f"IBPY: {msg}")


def get_actor_by_label(label):
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for a in subsystem.get_all_level_actors():
        if a.get_actor_label() == label:
            return a
    return None


def get_prop_any(obj, names, default=None):
    for n in names:
        try:
            return obj.get_editor_property(n)
        except Exception:
            continue
    return default


def trace_segment(world, start, end, tag):
    result = unreal.SystemLibrary.line_trace_single(
        world,
        start,
        end,
        unreal.TraceTypeQuery.ECC_VISIBILITY,
        True,   # trace_complex
        [],
        unreal.DrawDebugTrace.NONE,
        True,
        unreal.LinearColor(1, 0, 0, 1),
        unreal.LinearColor(0, 1, 0, 1),
        0.0,
    )
    if isinstance(result, tuple):
        success, hit_result = result
    else:
        hit_result = result
        success = None

    is_blocking = get_prop_any(hit_result, ["blocking_hit", "b_blocking_hit"], False)
    if success is not None:
        is_blocking = bool(is_blocking) or bool(success)

    if not is_blocking:
        log(f"    {tag}: NO HIT within {TRACE_DISTANCE_CM:.0f}cm.")
        return

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
    log(f"    {tag}: HIT at distance={hit_dist:.1f}cm, loc={loc_str}, actor='{hit_actor_label}' component='{hit_comp_name}'")


def main():
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()

    for b in BUILDINGS:
        name = b["name"]
        door = get_actor_by_label(b["door_actor"])
        if not door:
            log(f"[{name}] SKIPPED -- door actor '{b['door_actor']}' not found.")
            continue

        door_loc = door.get_actor_location()
        cx, cy = b["center_xy"]
        dir_x = cx - door_loc.x
        dir_y = cy - door_loc.y
        mag = math.sqrt(dir_x * dir_x + dir_y * dir_y)
        if mag < 1.0:
            log(f"[{name}] SKIPPED -- door is essentially at the building center, no clear direction.")
            continue
        dir_x /= mag
        dir_y /= mag
        # perpendicular (for lateral offsets), in the XY plane
        perp_x, perp_y = -dir_y, dir_x

        log(f"[{name}] door_loc=({door_loc.x:.1f},{door_loc.y:.1f},{door_loc.z:.1f}) "
            f"-> building_center=({cx:.1f},{cy:.1f}) inward_dir=({dir_x:.2f},{dir_y:.2f})")

        for h in HEIGHT_OFFSETS_CM:
            z = door_loc.z + h
            for lat in LATERAL_OFFSETS_CM:
                start = unreal.Vector(
                    door_loc.x - dir_x * START_BACKOFF_CM + perp_x * lat,
                    door_loc.y - dir_y * START_BACKOFF_CM + perp_y * lat,
                    z,
                )
                end = unreal.Vector(
                    start.x + dir_x * TRACE_DISTANCE_CM,
                    start.y + dir_y * TRACE_DISTANCE_CM,
                    z,
                )
                tag = f"h={h:.0f}cm lat={lat:+.0f}cm"
                trace_segment(world, start, end, tag)

    log("Done. Nothing was modified.")


main()
