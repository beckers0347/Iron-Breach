"""
IBPY: ib_assign_npc_animbp.py

Run AFTER you've wired and compiled ABP_NPC_Locomotion's graphs.
Sets every NPC_* actor's skeletal mesh component to "Use Animation
Blueprint" mode with ABP_NPC_Locomotion as its anim class, so they
actually run the Idle/Walk/Run blend instead of standing in ref pose.

Doesn't move, rotate, or rescale anything.

HOW TO RUN
----------
    py "X:/IronBreach/Scripts/ib_assign_npc_animbp.py"
Paste back the full output.
"""

import unreal

ABP_CLASS_PATH = "/Game/Characters/NPCs/Shared/ABP_NPC_Locomotion"


def log(msg):
    unreal.log(f"IBPY: {msg}")


def main():
    log("==== ASSIGN ABP_NPC_Locomotion TO NPC ACTORS ====")

    anim_class = unreal.EditorAssetLibrary.load_blueprint_class(ABP_CLASS_PATH)
    if anim_class is None:
        log(f"ERROR: could not load anim class {ABP_CLASS_PATH} -- "
            "has ABP_NPC_Locomotion been compiled at least once?")
        return

    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    count = 0
    for a in actor_subsystem.get_all_level_actors():
        if not a.get_actor_label().startswith("NPC_"):
            continue
        if not isinstance(a, unreal.SkeletalMeshActor):
            continue
        comp = a.skeletal_mesh_component
        comp.set_animation_mode(unreal.AnimationMode.ANIMATION_BLUEPRINT)
        comp.set_anim_instance_class(anim_class)
        log(f"  '{a.get_actor_label()}': anim class set.")
        count += 1

    log(f"==== DONE. {count} actor(s) updated. Hit Play/Simulate to see them idle; "
        "they only change to walk/run once something moves them. Save the level. ====")


main()
