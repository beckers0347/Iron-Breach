"""
List SkyLight / SkyAtmosphere / DirectionalLight actors in the active level
=============================================================================
IRON BREACH / Unreal Engine 5.8

WHAT THIS IS
------------
Diagnostic companion to cleanup_district_beats_from_garrison.py. The "Multiple
sky lights are active" / "Multiple sky atmosphere are active" Map Check errors
mean CarrowGateGarrison now has two of each -- almost certainly because
build_m1_district.py's own environment setup (SkyLight/SkyAtmosphere/
DirectionalLight, matching the "Pre-dawn. Overcast." lighting note in the
district concept doc) got created directly in this level instead of its own
map, alongside whatever the garrison already had.

This script only LISTS -- it doesn't delete anything. Read the output, decide
which SkyLight/SkyAtmosphere to keep (the original garrison's) and which to
delete (the district's), then either delete them by hand in the Outliner or
tell me the folder paths/labels it prints and I'll write a targeted deletion
script the same way cleanup_district_beats_from_garrison.py handles the beat
folders.

HOW TO RUN IT
-------------
    py "X:/IronBreach/Content/Python/list_env_actors_in_garrison.py"

Run with CarrowGateGarrison open and active.
"""

import unreal

WATCH_CLASSES = (unreal.SkyLight, unreal.SkyAtmosphere, unreal.DirectionalLight)


def run():
    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    all_actors = actor_subsystem.get_all_level_actors()

    found = 0
    for actor in all_actors:
        if not isinstance(actor, WATCH_CLASSES):
            continue
        found += 1
        try:
            folder = str(actor.get_folder_path())
        except Exception:
            folder = "(root)"
        loc = actor.get_actor_location()
        unreal.log(
            f"[Env Actors] {actor.get_class().get_name():>16}  label='{actor.get_actor_label()}'  "
            f"folder='{folder or '(root)'}'  location=({loc.x:.0f}, {loc.y:.0f}, {loc.z:.0f})"
        )

    unreal.log(f"[Env Actors] {found} SkyLight/SkyAtmosphere/DirectionalLight actor(s) total in the current level.")


run()
