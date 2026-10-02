"""
IBPY: ib_diag_trace_sanity.py

READ-ONLY. Two diagnostic runs in a row (ib_diag_doorway_blocked.py) got
ZERO hits for every single trace across all 5 buildings, all heights,
all lateral offsets, even after you saved/reopened the level -- that
ruled out "stale physics state." Getting literally zero hits everywhere,
including traces that should cross a building's own far exterior wall,
points at the trace call itself silently finding nothing, not at these
buildings actually being wide open.

Suspicion: switching from the deprecated `TraceTypeQuery.TRACE_TYPE_QUERY1`
to `TraceTypeQuery.ECC_VISIBILITY` (as that deprecation warning suggested)
may have broken it -- those might not resolve to the same actual trace
channel in this engine build's Python bindings.

This script is a pure sanity check, nothing building-specific:
  1. Traces straight down through a KNOWN-solid target -- the
     'Water_Placeholder' ground actor (an Engine Cube, simple collision,
     should be trivially easy to hit) -- using BOTH channel values
     (TRACE_TYPE_QUERY1 and ECC_VISIBILITY), so we can see which one (if
     either) is actually working at all.
  2. Repeats that against 'CityGround_00' as a second known-solid target.
  3. Also traces straight down through one Garrison building (Armory) at
     its own location, both channel values, trace_complex True and False,
     to see whether Nanite/complex collision is the differentiator.

Touches nothing.

HOW TO RUN:
  py "X:/IronBreach/Scripts/ib_diag_trace_sanity.py"
Paste back the full output.
"""

import unreal


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


def try_trace(world, start, end, channel, channel_name, trace_complex):
    result = unreal.SystemLibrary.line_trace_single(
        world, start, end, channel, trace_complex, [],
        unreal.DrawDebugTrace.NONE, True,
        unreal.LinearColor(1, 0, 0, 1), unreal.LinearColor(0, 1, 0, 1), 0.0,
    )
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
        loc_str = f"({hit_loc.x:.1f},{hit_loc.y:.1f},{hit_loc.z:.1f})" if hit_loc else "?"
        actor_label = hit_actor.get_actor_label() if hit_actor else "?"
        log(f"      channel={channel_name} trace_complex={trace_complex}: HIT loc={loc_str} actor='{actor_label}'")
    else:
        log(f"      channel={channel_name} trace_complex={trace_complex}: NO HIT")


def main():
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()

    channels = [
        (unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, "TRACE_TYPE_QUERY1"),
        (unreal.TraceTypeQuery.ECC_VISIBILITY, "ECC_VISIBILITY"),
    ]

    control_targets = ["Water_Placeholder", "CityGround_00"]
    for label in control_targets:
        actor = get_actor_by_label(label)
        if not actor:
            log(f"[{label}] SKIPPED -- not found.")
            continue
        loc = actor.get_actor_location()
        start = unreal.Vector(loc.x, loc.y, loc.z + 500.0)
        end = unreal.Vector(loc.x, loc.y, loc.z - 500.0)
        log(f"[{label}] control trace straight down through ({loc.x:.1f},{loc.y:.1f},{loc.z:.1f}):")
        for channel, channel_name in channels:
            try_trace(world, start, end, channel, channel_name, False)

    armory = get_actor_by_label("Armory")
    if armory:
        loc = armory.get_actor_location()
        start = unreal.Vector(loc.x, loc.y, loc.z + 1000.0)
        end = unreal.Vector(loc.x, loc.y, loc.z - 500.0)
        log(f"[Armory] trace straight down through building location ({loc.x:.1f},{loc.y:.1f},{loc.z:.1f}):")
        for channel, channel_name in channels:
            for tc in (True, False):
                try_trace(world, start, end, channel, channel_name, tc)
    else:
        log("[Armory] SKIPPED -- not found.")

    log("Done. Nothing was modified.")


main()
