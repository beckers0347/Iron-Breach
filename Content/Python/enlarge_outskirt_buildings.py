"""
ENLARGE THE OUTSKIRT BUILDINGS -- scale up footprint + height in place
================================================================
IRON BREACH / Unreal Engine 5.8

WHY
---
build_outskirts()'s size formula (footprint 9-18m, height ~5-37m tapering
down toward the fringe) is a lot smaller than downtown's (up to 78m+ with
tower bonuses), so a lot of outskirt buildings read as squat/toy-sized
next to their neighbors -- confirmed by you on Outskirt_019's cluster.

THE FIX
-------
Scales every Outskirt_* actor's world scale by SCALE_FACTOR in all 3 axes,
and adjusts each one's Z location proportionally (spawn_building always
sets Z = height/2, i.e. buildings are grounded at world Z=0 with their
pivot at true center -- multiplying both scale.z and location.z by the
same factor keeps the base planted at the same spot instead of sinking
into or floating above the ground). Position X/Y is untouched.

Bigger footprints mean some buildings that were fine after
fix_outskirt_overlaps.py may now touch again -- re-run that script after
this one to clean up any new overlaps from the size increase.

Safe to re-run, BUT each run compounds the previous one's scale-up (this
does not track an original baseline) -- only run it once per size change
you want.

HOW TO RUN IT
-------------
    py "X:/IronBreach/Content/Python/enlarge_outskirt_buildings.py"
    py "X:/IronBreach/Content/Python/fix_outskirt_overlaps.py"
"""

import unreal

actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

SCALE_FACTOR = 1.6


def log(msg):
    print("[EnlargeOutskirtBuildings] %s" % msg)


def run():
    all_actors = actor_subsystem.get_all_level_actors()
    buildings = [a for a in all_actors if a.get_actor_label().startswith("Outskirt_")]
    log("Enlarging %d Outskirt_* building(s) by %.1fx (footprint + height, grounded in place)..." % (
        len(buildings), SCALE_FACTOR))

    for a in buildings:
        scale = a.get_actor_scale3d()
        loc = a.get_actor_location()
        new_scale = unreal.Vector(scale.x * SCALE_FACTOR, scale.y * SCALE_FACTOR, scale.z * SCALE_FACTOR)
        a.set_actor_scale3d(new_scale)
        a.set_actor_location(unreal.Vector(loc.x, loc.y, loc.z * SCALE_FACTOR), False, False)

    log("Done. Buildings are bigger but may now overlap each other or the roads again -- "
        "run fix_outskirt_overlaps.py next to clean that up.")


run()
