"""
DROP ALL TOWN BUILDINGS + WALKWAYS DOWN BY 10m -- pure Z offset only
================================================================
IRON BREACH / Unreal Engine 5.8

WHY
---
Shane hand-moved a bunch of buildings after the last relayout/align pass,
so this does NOT recompute or re-snap anything -- it just takes every
actor's CURRENT transform (X, Y, rotation, scale all untouched) and shifts
it down 10m in world Z. Whatever Shane moved stays exactly where he put it,
just 10m lower, same as everything else.

WHAT IT MOVES
-------------
  - Every town building actor under the "CG Mainland/City/TownBuildings"
    folder tree (Spire, Town Square, the 4 corner Towers, Ruins, and every
    Rowhouse/Warehouse/Apartment/Cottage/Shopfront/Garage fill building).
  - Every walkway/road actor under the "IronBreach/City/Roads" folder tree
    (the perimeter loop, main spine, cross spine, and all building spurs).

Nothing outside those two folder trees is touched.

Safe to re-run -- each run just shifts whatever's currently in those
folders down another 10m, so only run it once per desired drop.

HOW TO RUN IT
-------------
    py "X:/IronBreach/Content/Python/move_town_down.py"
"""

import unreal

M = 100.0
DROP_M = 10.0

BUILDING_FOLDER = "CG Mainland/City/TownBuildings"
ROAD_FOLDER = "IronBreach/City/Roads"

actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def log(msg):
    print("[MoveTownDown] %s" % msg)


def under(folder, root):
    return folder == root or folder.startswith(root + "/")


def run():
    offset = unreal.Vector(0.0, 0.0, -DROP_M * M)
    moved = 0
    for a in actor_subsystem.get_all_level_actors():
        folder = str(a.get_folder_path())
        if under(folder, BUILDING_FOLDER) or under(folder, ROAD_FOLDER):
            a.add_actor_world_offset(offset, False, False)
            moved += 1

    log("Moved %d actor(s) down %.0fm (X/Y/rotation/scale untouched)." % (moved, DROP_M))
    log("Done. Save and take a look.")


run()
