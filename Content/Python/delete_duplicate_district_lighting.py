"""
Delete the duplicate district lighting rig from CarrowGateGarrison
======================================================================
IRON BREACH / Unreal Engine 5.8

WHAT THIS IS
------------
list_env_actors_in_garrison.py confirmed there are two full sets of
SkyLight/SkyAtmosphere/DirectionalLight actors in the level:

  - Carrowgate Garrison/Lighting  -- the garrison's original rig (KEEP):
      DirLight_PreDawn, SkyAtmosphere, SkyLight

  - Lighting (root-level, not nested under Carrowgate Garrison)  -- the
    district blockout's duplicate rig (DELETE), auto-renamed on creation
    since the names collided with the garrison's own:
      DirLight_PreDawn, SkyAtmosphere2, SkyLight2

This is exactly what's causing the "Multiple sky lights are active" / "Multiple
sky atmosphere are active" Map Check errors -- UE only allows one active
SkyLight and one active SkyAtmosphere per world. This script deletes only the
three actors sitting in the exact root-level "Lighting" folder (not the
"Carrowgate Garrison/Lighting" one), leaving the garrison's original rig
untouched.

HOW TO RUN IT
-------------
1. DRY_RUN = True (default below) -- run it and read the Output Log to
   confirm it's only listing the 3 root-level "Lighting" actors, not the
   "Carrowgate Garrison/Lighting" ones.
2. If correct, flip DRY_RUN to False below and run again to actually delete
   them and save the level.

       py "X:/IronBreach/Content/Python/delete_duplicate_district_lighting.py"

Safe to re-run: once deleted, a second run reports 0 found.
"""

import unreal

DRY_RUN = False

# Exact match, NOT startswith -- "Carrowgate Garrison/Lighting" must NOT match.
TARGET_FOLDER = "Lighting"
WATCH_CLASSES = (unreal.SkyLight, unreal.SkyAtmosphere, unreal.DirectionalLight)


def run():
    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    all_actors = actor_subsystem.get_all_level_actors()

    to_delete = []
    for actor in all_actors:
        if not isinstance(actor, WATCH_CLASSES):
            continue
        try:
            folder = str(actor.get_folder_path())
        except Exception:
            continue
        if folder == TARGET_FOLDER:
            to_delete.append(actor)

    unreal.log(f"[Duplicate Lighting Cleanup] {len(to_delete)} actor(s) found in the root-level '{TARGET_FOLDER}' folder.")
    for actor in to_delete:
        unreal.log(f"  - {actor.get_class().get_name()}  label='{actor.get_actor_label()}'")

    if not to_delete:
        unreal.log("[Duplicate Lighting Cleanup] Nothing to delete -- already clean, or the folder was renamed.")
        return

    if DRY_RUN:
        unreal.log(f"[Duplicate Lighting Cleanup] DRY RUN -- no changes made. Set DRY_RUN = False and re-run to actually delete these {len(to_delete)} actor(s).")
        return

    actor_subsystem.destroy_actors(to_delete)
    unreal.EditorLevelLibrary.save_current_level()
    unreal.log(f"[Duplicate Lighting Cleanup] Deleted {len(to_delete)} actor(s) and saved the level.")


run()
