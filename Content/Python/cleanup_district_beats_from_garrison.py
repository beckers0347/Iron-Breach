"""
Remove the M1 District/Landfall beat blockout from CarrowGateGarrison
======================================================================
IRON BREACH / Unreal Engine 5.8

WHAT THIS IS
------------
build_m1_district.py appears to have been run while CarrowGateGarrison.umap
was the active level instead of its own map -- every beat folder it builds
(named after the mission design doc's section numbers: 4.2 Dread, 4.3a-d
Burst, 4.4a-d Aftermath) landed inside the garrison level alongside the
original "Carrowgate Garrison" folder (Armory, etc.), at real-world district
scale. That's the huge flat plane reading as an ocean/horizon around the
garrison in the editor.

This script deletes every actor whose folder_path starts with one of the
known beat-folder names below, and leaves everything else in the level
(including the original "Carrowgate Garrison" folder) untouched.

HOW TO RUN IT
-------------
1. Open CarrowGateGarrison in the editor (so it's the active/current level).
2. First pass, DRY_RUN = True (default below): run it and read the printed
   list in the Output Log -- confirms exactly what would be deleted before
   anything actually happens.
3. If the list looks right, change DRY_RUN to False below and run again --
   this time it actually deletes the actors and saves the level.

       py "X:/IronBreach/Content/Python/cleanup_district_beats_from_garrison.py"

Safe to re-run: once the actors are gone, a second run just reports 0 found.
"""

import unreal

DRY_RUN = False

BEAT_FOLDER_PREFIXES = (
    "4.2 Dread - Evac Street",
    "4.3a Burst - Eruption Crater",
    "4.3b Burst - Route Clearing",
    "4.3c Burst - Gun Line",
    "4.3d Burst - Collapse Sprint",
    "4.4a Aftermath - Stairwell",
    "4.4b Aftermath - The Carry",
    "4.4c Aftermath - Hospital Muster",
    "4.4d Aftermath - Sea Wall Glimpse",
)


def run():
    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    all_actors = actor_subsystem.get_all_level_actors()

    to_delete = []
    for actor in all_actors:
        try:
            folder = str(actor.get_folder_path())
        except Exception:
            continue
        if folder.startswith(BEAT_FOLDER_PREFIXES):
            to_delete.append(actor)

    unreal.log(f"[District Cleanup] {len(to_delete)} actor(s) found under M1 District/Landfall beat folders.")
    for actor in to_delete:
        unreal.log(f"  - {actor.get_actor_label()}  (folder: {actor.get_folder_path()})")

    if not to_delete:
        unreal.log("[District Cleanup] Nothing to delete -- already clean, or the beat folders were renamed.")
        return

    if DRY_RUN:
        unreal.log(f"[District Cleanup] DRY RUN -- no changes made. Set DRY_RUN = False and re-run to actually delete these {len(to_delete)} actor(s).")
        return

    actor_subsystem.destroy_actors(to_delete)
    unreal.EditorLevelLibrary.save_current_level()
    unreal.log(f"[District Cleanup] Deleted {len(to_delete)} actor(s) and saved the level.")


run()
