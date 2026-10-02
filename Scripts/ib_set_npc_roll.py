"""
IBPY: ib_set_npc_roll.py

The NPC_* actors were given roll = -90 to stand the Y-up Ms_Idris mesh up in
its reference pose. Now that the Loco_* animations are scaled correctly, the
animation drives the skeleton Z-up (like the JumpSuit), so that -90 roll tips
the NPCs onto their backs in PIE.

This sets every NPC_* SkeletalMeshActor's roll to TARGET_ROLL (default 0),
keeping location, pitch, yaw and scale. Logs before/after so it can be undone:
set TARGET_ROLL = -90.0 and re-run to revert.

HOW TO RUN (editor, not in PIE):
    py "X:/IronBreach/Scripts/ib_set_npc_roll.py"
Then press Play. Are the NPCs standing upright? Save the level if so.
"""

import unreal

TARGET_ROLL = 0.0   # revert value: -90.0


def log(msg):
    unreal.log(f"IBPY: {msg}")


def main():
    log(f"==== SET NPC ROLL -> {TARGET_ROLL} ====")
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    n = 0
    for a in sub.get_all_level_actors():
        lbl = a.get_actor_label()
        if not lbl.startswith("NPC_") or not isinstance(a, unreal.SkeletalMeshActor):
            continue
        before = a.get_actor_rotation()
        a.set_actor_rotation(
            unreal.Rotator(roll=TARGET_ROLL, pitch=before.pitch, yaw=before.yaw), False)
        after = a.get_actor_rotation()
        loc = a.get_actor_location()
        log(f"'{lbl}': rot(P,Y,R) ({before.pitch:.0f},{before.yaw:.0f},{before.roll:.0f}) -> "
            f"({after.pitch:.0f},{after.yaw:.0f},{after.roll:.0f}); loc=({loc.x:.0f},{loc.y:.0f},{loc.z:.0f})")
        n += 1
    log(f"==== DONE. {n} actor(s) updated. Press Play; if upright, save the level. ====")


main()
