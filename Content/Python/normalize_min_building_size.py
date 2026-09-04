"""
NORMALIZE MINIMUM BUILDING SIZE -- boost only the buildings that are too small
================================================================
IRON BREACH / Unreal Engine 5.8

WHY
---
"some [buildings] are way too small" -- after enlarge_outskirt_buildings.py
(a blanket 1.6x on every Outskirt_* building) there's still a long tail of
buildings, in BOTH Downtown and the Outskirts, whose footprint/height
formula rolled a small result and now reads as a toy-sized shed next to
its neighbors.

THE FIX
-------
Rather than blanket-scale everything again (which would just compound the
last enlarge and blow up buildings that are already a good size), this
checks each Downtown_*/Outskirt_* building's REAL current scale (spawn
code sets world_scale3d directly to footprint_x/footprint_y/height in
meters, so actor scale IS the size) against a minimum footprint and
minimum height. Only buildings below either floor get scaled up -- by the
smallest factor needed to clear both floors at once -- and Z location is
adjusted by the same factor to keep the base grounded (buildings are
spawned with Z = height/2). Buildings already above the minimums are left
completely untouched.

Safe to re-run -- once a building clears the floor it's skipped on the
next run, so this won't compound like the old blanket enlarge script.
Re-run fix_all_city_overlaps.py afterward since some of these will grow
and may re-collide with a close neighbor.

HOW TO RUN IT
-------------
    py "X:/IronBreach/Content/Python/normalize_min_building_size.py"
    py "X:/IronBreach/Content/Python/fix_all_city_overlaps.py"
"""

import unreal

actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

MIN_FOOTPRINT_M = 15.0   # smaller of X/Y footprint
MIN_HEIGHT_M = 20.0


def log(msg):
    print("[NormalizeMinBuildingSize] %s" % msg)


def run():
    all_actors = actor_subsystem.get_all_level_actors()
    buildings = [a for a in all_actors if a.get_actor_label().startswith(("Outskirt_", "Downtown_"))]

    boosted = 0
    for a in buildings:
        scale = a.get_actor_scale3d()
        footprint_min = min(scale.x, scale.y)
        height = scale.z

        factor = 1.0
        if footprint_min < MIN_FOOTPRINT_M:
            factor = max(factor, MIN_FOOTPRINT_M / footprint_min)
        if height < MIN_HEIGHT_M:
            factor = max(factor, MIN_HEIGHT_M / height)

        if factor <= 1.0001:
            continue

        loc = a.get_actor_location()
        new_scale = unreal.Vector(scale.x * factor, scale.y * factor, scale.z * factor)
        a.set_actor_scale3d(new_scale)
        a.set_actor_location(unreal.Vector(loc.x, loc.y, loc.z * factor), False, False)
        boosted += 1
        log("  %s: footprint %.1fx%.1fm, height %.1fm -> scaled by %.2fx" % (
            a.get_actor_label(), scale.x, scale.y, scale.z, factor))

    log("Boosted %d undersized building(s) up to a %.0fm footprint / %.0fm height floor. "
        "%d building(s) were already fine." % (boosted, MIN_FOOTPRINT_M, MIN_HEIGHT_M, len(buildings) - boosted))
    log("Re-run fix_all_city_overlaps.py next to clean up any new overlaps from the size increase. "
        "Save and check the viewport / re-run PIE.")


run()
