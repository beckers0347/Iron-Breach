"""
FORCE-ASSIGN THE GROUND MATERIAL BY FOLDER (not by guessing its current material)
================================================================
IRON BREACH / Unreal Engine 5.8

WHY THIS ONE'S DIFFERENT
--------------------------
The last two ground fixes both worked by finding actors whose CURRENT
material matched a specific asset, then swapping it. Both guesses were
wrong: fix_mountains_and_ground.py looked for "MI_Landmass_Ground", but
PALETTE["ground"] in build_carrowgate_mainland.py actually falls back to
FALLBACK_GROUND (M_AI_Ground -- the SAME material already retextured for the
garrison's own walls/concrete, since that asset already existed when this
level was built) whenever M_AI_Ground exists in the project, which it does.
So the ground was never on the placeholder I was searching for -- rebuilding
M_AI_MountainGround changed an asset nothing on screen was using.

This script skips the guessing entirely: it logs every ground actor's
CURRENT material (so we know for certain this time, not by inference), then
force-assigns M_AI_MountainGround directly to every actor under the two
folders build_carrowgate_mainland.py actually uses for ground --
"CG Mainland/City/Ground" and "CG Mainland/Mountains/Ground" -- regardless
of what material they were wearing before.

HOW TO RUN IT
-------------
    py "X:/IronBreach/Content/Python/force_ground_material.py"

Read the DIAGNOSTIC lines first (before the assignment) -- if the "current
material" logged there is something unexpected again, paste it back rather
than assuming this run fixed it.
"""

import unreal

AL = unreal.EditorAssetLibrary
actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

GROUND_MATERIAL_PATH = "/Game/LevelPrototyping/AITextures/Landmass/M_AI_MountainGround"
GROUND_FOLDERS = (
    "CG Mainland/City/Ground",
    "CG Mainland/Mountains/Ground",
)


def log(msg):
    print("[ForceGround] %s" % msg)


def is_under_any(actor, folders):
    folder = str(actor.get_folder_path())
    return any(folder == f or folder.startswith(f + "/") for f in folders)


def run():
    if not AL.does_asset_exist(GROUND_MATERIAL_PATH):
        log("SKIPPED -- %s doesn't exist. Run fix_mountains_and_ground.py first." % GROUND_MATERIAL_PATH)
        return
    ground_mat = AL.load_asset(GROUND_MATERIAL_PATH)

    all_actors = actor_subsystem.get_all_level_actors()
    targets = [a for a in all_actors if isinstance(a, unreal.StaticMeshActor) and is_under_any(a, GROUND_FOLDERS)]

    log("Found %d ground actor(s) under %s." % (len(targets), " / ".join(GROUND_FOLDERS)))

    # Diagnostic: what were they actually wearing? (grouped, so it's readable)
    current_mats = {}
    for a in targets:
        comp = a.static_mesh_component
        mat = comp.get_material(0) if comp else None
        name = mat.get_name() if mat else "(none)"
        current_mats.setdefault(name, 0)
        current_mats[name] += 1
    for name, count in sorted(current_mats.items(), key=lambda kv: -kv[1]):
        log("  currently wearing: %5d x  %s" % (count, name))

    # Force-assign, no more guessing.
    assigned = 0
    for a in targets:
        comp = a.static_mesh_component
        if comp:
            comp.set_material(0, ground_mat)
            assigned += 1

    log("Force-assigned M_AI_MountainGround to %d actor(s)." % assigned)
    log("Save the level (Ctrl+S) and check the viewport / re-run PIE.")


run()
