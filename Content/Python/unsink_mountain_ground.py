"""
UN-SINK THE MOUNTAIN GROUND PAD -- undo part of the earlier 6m mountain drop
================================================================
IRON BREACH / Unreal Engine 5.8

WHAT ACTUALLY HAPPENED
-----------------------
fix_mountains_and_ground.py moved every actor under the "CG Mainland/Mountains"
folder TREE down 6m -- which, it turns out, includes two subfolders confirmed
to exist in this map: "CG Mainland/Mountains/Ground" and
"CG Mainland/Mountains/Wall". Those aren't mountain peaks -- they're the
ground pad and retaining wall sitting directly under/around the mountain
range. Dragging them down 6m along with the actual peaks (the "Peak_NNN"
actors) sank that ground pad below the existing ocean water plane's surface,
so the water plane became what's visible where the ground used to be --
that's the "changed the ground to water" result, not a material bug. The
M_AI_MountainGround material rebuild in fix_ground_metallic.py was fine; it
just wasn't showing anymore because the actor wearing it was now underwater.

THE FIX
-------
Moves every actor under "CG Mainland/Mountains/Ground" and
"CG Mainland/Mountains/Wall" back UP 6m (undoes just that part of the
original drop). Leaves every actor directly in "CG Mainland/Mountains" itself
(the "Peak_NNN" meshes) exactly where they are now -- those were the ones you
actually asked to move down, and that part worked correctly.

HOW TO RUN IT
-------------
    py "X:/IronBreach/Content/Python/unsink_mountain_ground.py"

Only run this ONCE against the current (already-sunk) state -- it's not
idempotent (each run shifts those actors another 6m up).
"""

import unreal

actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

RESTORE_FOLDERS = (
    "CG Mainland/Mountains/Ground",
    "CG Mainland/Mountains/Wall",
)
RESTORE_UP_CM = 600.0  # undo the 6m drop for these specific subfolders only


def log(msg):
    print("[UnsinkGround] %s" % msg)


def run():
    all_actors = actor_subsystem.get_all_level_actors()
    restored = 0
    for a in all_actors:
        folder = str(a.get_folder_path())
        if any(folder == f or folder.startswith(f + "/") for f in RESTORE_FOLDERS):
            a.add_actor_world_offset(unreal.Vector(0.0, 0.0, RESTORE_UP_CM), False, False)
            restored += 1

    log("Restored %d actor(s) under %s back up %.0fm." % (
        restored, " / ".join(RESTORE_FOLDERS), RESTORE_UP_CM / 100.0))

    if restored == 0:
        log("Nothing matched those folder paths -- if the ground pad actors live under a "
            "different folder name in your checkout, tell me the actual folder path shown "
            "in the Outliner (expand 'CG Mainland > Mountains' and check the subfolder name) "
            "and I'll retarget this.")
    else:
        log("Peak_NNN mountain actors were NOT touched -- they stay at their already-lowered "
            "position. Save the level and check the viewport / re-run PIE.")


run()
