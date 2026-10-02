"""
IBPY: ib_test_jumpsuit_abp.py

Deciding experiment for the "NPCs grow huge + lie down in PIE" bug.

Step 6 of ib_diagnose_npc_growth.py showed:
  - JumpSuit mesh Hips ref pose : rot(P,Y,R)=(0,-90,90), scale 1.8, standing (Z-up)
  - Idris mesh   Hips ref pose  : rot(P,Y,R)=(0,0,-180), loc Y=89.7, scale 1.7  (Y-up, lying)
  - Loco_* Hips track @t=0      : scale 1000, rot ~(0,0,90), loc Z~55424
Both meshes' bind poses are far from the animation's Hips track, so the
question is: does a plain JumpSuit mesh ALSO blow up with ABP_NPC_Locomotion?
  - If the JumpSuit test actor stays normal in PIE -> the problem is the Idris
    mesh's bind pose/orientation (and the roll=-90 hack on the NPC actors).
  - If the JumpSuit test actor also grows/lies down -> the problem is the
    Loco_* animations / ABP, not Idris.

What this does:
  1. Logs location + rotation of every NPC_* actor (the roll=-90 hack).
  2. Spawns ZZ_TEST_JumpSuit_ABP: JumpSuit mesh + ABP_NPC_Locomotion,
     300 cm to the side of NPC_Idris, rotation 0,0,0.
  3. Set REMOVE_TEST = True and re-run to delete it afterwards.
Nothing else in the level is changed.

HOW TO RUN (editor, not in PIE):
    py "X:/IronBreach/Scripts/ib_test_jumpsuit_abp.py"
Then press Play, look at ZZ_TEST_JumpSuit_ABP vs the NPCs, and tell me what happens.
If it's floating/buried, nudge its Z in the Details panel.
"""

import unreal

REMOVE_TEST = False

TEST_LABEL = "ZZ_TEST_JumpSuit_ABP"
MESH_PATH = "/Game/Characters/Infantry/Meshes/JumpSuit/Base_Character_Mesh"
ABP_PATH = "/Game/Characters/NPCs/Shared/ABP_NPC_Locomotion"
SIDE_OFFSET = unreal.Vector(0.0, 300.0, 0.0)


def log(msg):
    unreal.log(f"IBPY: {msg}")


def main():
    log("==== JUMPSUIT + ABP TEST ====")
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors = sub.get_all_level_actors()

    if REMOVE_TEST:
        n = 0
        for a in actors:
            if a.get_actor_label() == TEST_LABEL:
                sub.destroy_actor(a)
                n += 1
        log(f"removed {n} test actor(s). ==== DONE ====")
        return

    idris = None
    for a in actors:
        lbl = a.get_actor_label()
        if lbl.startswith("NPC_") and isinstance(a, unreal.SkeletalMeshActor):
            loc = a.get_actor_location()
            rot = a.get_actor_rotation()
            log(f"'{lbl}': loc=({loc.x:.1f},{loc.y:.1f},{loc.z:.1f}) "
                f"rot(P,Y,R)=({rot.pitch:.1f},{rot.yaw:.1f},{rot.roll:.1f})")
            if lbl == "NPC_Idris":
                idris = a
        if lbl == TEST_LABEL:
            log(f"ERROR: '{TEST_LABEL}' already exists; set REMOVE_TEST=True and re-run first.")
            return

    mesh = unreal.load_asset(MESH_PATH)
    anim_class = unreal.EditorAssetLibrary.load_blueprint_class(ABP_PATH)
    if mesh is None or anim_class is None:
        log(f"ERROR: mesh={mesh} anim_class={anim_class}")
        return

    base = idris.get_actor_location() if idris else unreal.Vector(0, 0, 0)
    spawn_loc = unreal.Vector(base.x + SIDE_OFFSET.x, base.y + SIDE_OFFSET.y, base.z + SIDE_OFFSET.z)
    test = sub.spawn_actor_from_class(
        unreal.SkeletalMeshActor, spawn_loc, unreal.Rotator(roll=0.0, pitch=0.0, yaw=0.0))
    if test is None:
        log("ERROR: spawn failed")
        return
    test.set_actor_label(TEST_LABEL)
    comp = test.skeletal_mesh_component
    comp.set_skinned_asset_and_update(mesh)
    comp.set_animation_mode(unreal.AnimationMode.ANIMATION_BLUEPRINT)
    comp.set_anim_instance_class(anim_class)
    log(f"spawned '{TEST_LABEL}' at ({spawn_loc.x:.1f},{spawn_loc.y:.1f},{spawn_loc.z:.1f}) "
        "with JumpSuit mesh + ABP_NPC_Locomotion.")
    log("==== DONE. Press Play: does the test actor stay normal size and upright? ====")


main()
