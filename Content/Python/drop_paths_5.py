"""
DROP WALKWAYS BY 5 MORE UNITS -- roads only, buildings untouched
================================================================
IRON BREACH / Unreal Engine 5.8

Paths are currently sitting at -5 and Shane wants them at -10, so this
shifts just the road/walkway actors (IronBreach/City/Roads folder tree)
down another 5 units in world Z. Buildings are not touched.

HOW TO RUN IT
-------------
    py "X:/IronBreach/Content/Python/drop_paths_5.py"
"""

import unreal

CORRECTION = -5.0

ROAD_FOLDER = "IronBreach/City/Roads"

actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def log(msg):
    print("[DropPaths5] %s" % msg)


def under(folder, root):
    return folder == root or folder.startswith(root + "/")


def run():
    offset = unreal.Vector(0.0, 0.0, CORRECTION)
    moved = 0
    for a in actor_subsystem.get_all_level_actors():
        folder = str(a.get_folder_path())
        if under(folder, ROAD_FOLDER):
            a.add_actor_world_offset(offset, False, False)
            moved += 1

    log("Moved %d road/walkway actor(s) down %.0f more units." % (moved, abs(CORRECTION)))
    log("Done. Save and take a look.")


run()
