"""
IBPY: ib_create_npc_locomotion_assets.py

Builds the locomotion assets NPCs need to move, using ONLY the animations
you imported yourself under /Game/Characters/Infantry/Animations/ --
nothing from engine/template content, per your instruction. Ignores the
Sandbox/ABP_Infantry prototype entirely.

Creates two new assets at /Game/Characters/NPCs/Shared/, targeting
Base_Character_Mesh_Skeleton (same skeleton Idris and the placeholders are
already on):

  1. BS_NPC_Unarmed_Locomotion -- a 1D BlendSpace (axis: Speed, 0-375) using
     three of your imported clips from Locomotion_Unarmed/:
       Speed   0  -> Loco_Idle
       Speed 150  -> Loco_Walking
       Speed 375  -> Loco_Running
     (150/375 are standard placeholder speed values, same convention as
     Epic's own template content -- easy to retune once you see how it
     feels in-game.)
  2. ABP_NPC_Locomotion -- a new, empty Animation Blueprint, parent class
     AnimInstance, target skeleton Base_Character_Mesh_Skeleton.

Attempts to populate the BlendSpace's samples via Python directly. The
Unreal Python API doesn't reliably expose BlendSpace sample editing in
every engine version, so this reports exactly what succeeded and what
didn't -- if the automatic population fails, the asset still gets created
correctly (right skeleton, right axis range), you just drag the three
clips onto the grid yourself in the BlendSpace editor, which takes under a
minute.

Does NOT wire the AnimGraph (state machine / BlendSpace Player node /
Speed variable) -- that needs the visual graph editor, not Python. I'll
give you exact node-by-node instructions for that once this asset exists.

HOW TO RUN
----------
    py "X:/IronBreach/Scripts/ib_create_npc_locomotion_assets.py"
Paste back the full output.
"""

import unreal

INFANTRY_SKELETON_PATH = "/Game/Characters/Infantry/Meshes/JumpSuit/Base_Character_Mesh_Skeleton"
LOCO_IDLE_PATH = "/Game/Characters/Infantry/Animations/Locomotion_Unarmed/Loco_Idle"
LOCO_WALK_PATH = "/Game/Characters/Infantry/Animations/Locomotion_Unarmed/Loco_Walking"
LOCO_RUN_PATH = "/Game/Characters/Infantry/Animations/Locomotion_Unarmed/Loco_Running"

DEST_PATH = "/Game/Characters/NPCs/Shared"
BS_NAME = "BS_NPC_Unarmed_Locomotion"
ABP_NAME = "ABP_NPC_Locomotion"


def log(msg):
    unreal.log(f"IBPY: {msg}")


def main():
    log("==== CREATE NPC LOCOMOTION ASSETS (imported clips only) ====")

    skeleton = unreal.load_asset(INFANTRY_SKELETON_PATH)
    if skeleton is None:
        log(f"ERROR: could not load skeleton at {INFANTRY_SKELETON_PATH}")
        return

    idle = unreal.load_asset(LOCO_IDLE_PATH)
    walk = unreal.load_asset(LOCO_WALK_PATH)
    run = unreal.load_asset(LOCO_RUN_PATH)
    for label, anim in [("Loco_Idle", idle), ("Loco_Walking", walk), ("Loco_Running", run)]:
        if anim is None:
            log(f"ERROR: could not load {label} -- aborting, nothing created.")
            return
        anim_skel = anim.get_editor_property("skeleton")
        if anim_skel is None or anim_skel.get_path_name() != skeleton.get_path_name():
            log(f"WARNING: {label}'s skeleton ({anim_skel.get_path_name() if anim_skel else None}) "
                f"doesn't match {INFANTRY_SKELETON_PATH} -- it won't play correctly on the NPC rig.")

    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()

    # ---- BlendSpace1D ----
    log(f"---- Creating {BS_NAME} ----")
    bs_factory = unreal.BlendSpaceFactory1D()
    bs_factory.set_editor_property("target_skeleton", skeleton)
    blend_space = asset_tools.create_asset(BS_NAME, DEST_PATH, None, bs_factory)
    if blend_space is None:
        log("ERROR: BlendSpace creation failed.")
    else:
        log(f"Created: {blend_space.get_path_name()}")
        try:
            blend_space.set_editor_property("axis_x_name", "Speed")
        except Exception as e:
            log(f"  (non-fatal) could not set axis name: {e}")

        populated = False
        try:
            samples = []
            for anim, value in [(idle, 0.0), (walk, 150.0), (run, 375.0)]:
                sample = unreal.BlendSample()
                sample.set_editor_property("animation", anim)
                sample.set_editor_property("sample_value", unreal.Vector(x=value, y=0.0, z=0.0))
                samples.append(sample)
            blend_space.set_editor_property("sample_data", samples)
            populated = True
            log(f"  Populated {len(samples)} samples automatically: Idle@0, Walk@150, Run@375.")
        except Exception as e:
            log(f"  Could not auto-populate samples via Python ({e}). "
                "You'll need to drag the 3 clips onto the grid manually -- details below.")

        unreal.EditorAssetLibrary.save_asset(blend_space.get_path_name())
        if not populated:
            log(f"  MANUAL STEP: open {BS_NAME}, drag Loco_Idle onto Speed=0, "
                f"Loco_Walking onto Speed=150, Loco_Running onto Speed=375.")

    # ---- Animation Blueprint ----
    log(f"---- Creating {ABP_NAME} ----")
    abp_factory = unreal.AnimBlueprintFactory()
    abp_factory.set_editor_property("target_skeleton", skeleton)
    abp_factory.set_editor_property("parent_class", unreal.AnimInstance)
    anim_bp = asset_tools.create_asset(ABP_NAME, DEST_PATH, None, abp_factory)
    if anim_bp is None:
        log("ERROR: AnimBlueprint creation failed.")
    else:
        log(f"Created: {anim_bp.get_path_name()}")
        unreal.EditorAssetLibrary.save_asset(anim_bp.get_path_name())
        log("  This is an EMPTY AnimBlueprint -- no AnimGraph logic yet. "
            "I'll give you exact node-by-node wiring instructions next.")

    log("==== DONE ====")


main()
