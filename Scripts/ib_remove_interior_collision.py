"""
IBPY: ib_remove_interior_collision.py

Removes a building's previously-generated interior collision BlockingVolumes
(the ones spawned by ib_auto_interior_collision.py, labeled
"<prefix>_Collision_...") so the shell can be rebuilt cleanly from scratch
without leaving duplicate/overlapping volumes behind.

HOW TO RUN:
  py "X:\IronBreach\Scripts\ib_remove_interior_collision.py"

Nothing is saved automatically -- review in the viewport, then save the
level yourself once you're happy.
"""

import unreal

# Prefix(es) to clear out before a rebuild.
PREFIXES_TO_CLEAR = ["07_Armory"]


def log(msg):
    unreal.log(f"IBPY: {msg}")


def main():
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    all_actors = subsystem.get_all_level_actors()

    to_remove = []
    for a in all_actors:
        label = a.get_actor_label()
        for prefix in PREFIXES_TO_CLEAR:
            if label.startswith(f"{prefix}_Collision_"):
                to_remove.append(a)
                break

    log(f"Found {len(to_remove)} interior collision actor(s) to remove for prefixes {PREFIXES_TO_CLEAR}.")
    for a in to_remove:
        log(f"  Destroying: {a.get_actor_label()}")
        subsystem.destroy_actor(a)

    log(f"Done. Removed {len(to_remove)} actor(s). Review in viewport, then save the level yourself when ready.")


main()
