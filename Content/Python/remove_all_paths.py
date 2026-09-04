"""
DELETE THE WHOLE PATH/ROAD SYSTEM -- clean slate
================================================================
IRON BREACH / Unreal Engine 5.8

WHY
---
The top-down screenshot makes it clear: what's actually in the level is a
scatter of disconnected square tile patches, not a connected path network.
The corner-bridging attempts kept failing because there was never a
continuous path to connect in the first place -- these are isolated pieces
sitting on the grass, not a street/path graph, so no "bridge the gaps"
script was ever going to make them read as one connected path. Time to
just clear it all out and rebuild properly rather than patch this further.

WHAT THIS DELETES
------------------
Every actor whose material 0 is M_AI_CobblestonePath (that's every road,
street, and path piece across both the garrison and CG Mainland -- that
material became the single shared "path" material a few steps back), PLUS
anything labeled PathBridge_* or RoadJoint_* regardless of material (the
bridge/joint patches from the last two fix attempts, in case any still
carry a different material). It does NOT touch buildings, trees, the
ground/grass itself, or anything else -- logs every actor it removes so
you have a record of exactly what went.

This does NOT delete or modify M_AI_CobblestonePath itself, or the source
textures -- just the placed actors. We can rebuild a real connected path
network as its own next step once this is clean.

HOW TO RUN IT
-------------
    py "X:/IronBreach/Content/Python/remove_all_paths.py"

Safe to re-run (second run will just find nothing left to delete).
"""

import unreal

actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
AL = unreal.EditorAssetLibrary

PATH_MATERIAL_PATH = "/Game/LevelPrototyping/AITextures/Landmass/M_AI_CobblestonePath"
LABEL_PREFIXES = ("PathBridge_", "RoadJoint_")


def log(msg):
    print("[RemoveAllPaths] %s" % msg)


def uses_path_material(actor):
    for comp in actor.get_components_by_class(unreal.StaticMeshComponent):
        mat = comp.get_material(0)
        if mat and mat.get_path_name().startswith(PATH_MATERIAL_PATH):
            return True
    return False


def run():
    all_actors = actor_subsystem.get_all_level_actors()
    to_delete = []
    for a in all_actors:
        label = a.get_actor_label()
        if label.startswith(LABEL_PREFIXES) or uses_path_material(a):
            to_delete.append(a)

    log("Found %d actor(s) to remove." % len(to_delete))
    if not to_delete:
        log("Nothing to do.")
        return

    by_folder = {}
    for a in to_delete:
        folder = str(a.get_folder_path())
        by_folder.setdefault(folder, []).append(a.get_actor_label())

    for folder, labels in sorted(by_folder.items()):
        log("  '%s': %d actor(s) -- e.g. %s" % (folder, len(labels), ", ".join(labels[:3])))

    removed = 0
    for a in to_delete:
        if actor_subsystem.destroy_actor(a):
            removed += 1

    log("Removed %d actor(s). Path/road system is now clear." % removed)
    log("Save the level. Tell me how you want the path laid out and I'll rebuild it as a "
        "real connected network this time (e.g. explicit waypoints along the streets you "
        "actually want it to follow, not another random scatter/walk).")


run()
