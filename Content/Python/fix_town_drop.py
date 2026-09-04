"""
CORRECT THE TOWN DROP -- undo the accidental -1000 unit drop, leave it at
-10 units total instead
================================================================
IRON BREACH / Unreal Engine 5.8

move_town_down.py used a units-vs-meters mixup and dropped everything
1000 units instead of the 10 Shane actually wanted. This nudges everything
back UP by 990 units, so the net result from where it started is exactly
-10 units, not -1000. X/Y/rotation/scale are untouched, same folders as
before (CG Mainland/City/TownBuildings, IronBreach/City/Roads).

Only run this ONCE, right after the -1000 drop -- it's a one-time
correction, not idempotent (running it twice would overcorrect).

HOW TO RUN IT
-------------
    py "X:/IronBreach/Content/Python/fix_town_drop.py"
"""

import unreal

CORRECTION = 990.0  # move back up this much so net drop = 1000 - 990 = 10

BUILDING_FOLDER = "CG Mainland/City/TownBuildings"
ROAD_FOLDER = "IronBreach/City/Roads"

actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def log(msg):
    print("[FixTownDrop] %s" % msg)


def under(folder, root):
    return folder == root or folder.startswith(root + "/")


def run():
    offset = unreal.Vector(0.0, 0.0, CORRECTION)
    moved = 0
    for a in actor_subsystem.get_all_level_actors():
        folder = str(a.get_folder_path())
        if under(folder, BUILDING_FOLDER) or under(folder, ROAD_FOLDER):
            a.add_actor_world_offset(offset, False, False)
            moved += 1

    log("Moved %d actor(s) up %.0f units -- net drop from original position is now 10 units." % (moved, CORRECTION))
    log("Done. Save and take a look.")


run()
