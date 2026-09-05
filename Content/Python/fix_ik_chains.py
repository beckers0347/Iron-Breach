"""
Fix-up script v2: adds the retarget bone chains to IK_ChaosArmor and
IK_StarterArmor using the REAL add_retarget_chain signature (confirmed via
introspecting the engine's own docstring this time instead of guessing):

    controller.add_retarget_chain(chain_name, start_bone_name, end_bone_name, goal_name) -> Name

No BoneChain/BoneReference struct construction needed at all -- just plain
Name arguments.

HOW TO RUN IT
-------------
    py "X:/IronBreach/Content/Python/fix_ik_chains.py"
"""

import unreal

IKRIG_DIR = "/Game/Characters/Infantry/Animations/Retargeting"
RIG_NAMES = ["IK_ChaosArmor", "IK_StarterArmor"]

CHAINS = [
    ("Spine", "Spine", "Spine2"),
    ("Neck", "Neck", "Neck"),
    ("Head", "Head", "HeadTop_End"),
    ("LeftArm", "LeftShoulder", "LeftHand"),
    ("RightArm", "RightShoulder", "RightHand"),
    ("LeftLeg", "LeftUpLeg", "LeftFoot"),
    ("RightLeg", "RightUpLeg", "RightFoot"),
]

for rig_name in RIG_NAMES:
    rig = unreal.EditorAssetLibrary.load_asset(f"{IKRIG_DIR}/{rig_name}.{rig_name}")
    if rig is None:
        unreal.log_error(f"[FixChains] Could not load {rig_name}")
        continue

    controller = unreal.IKRigController.get_controller(rig)
    if controller is None:
        unreal.log_error(f"[FixChains] Could not get controller for {rig_name}")
        continue

    # Clear any partially-created chains from earlier failed attempts first.
    existing_chains = list(controller.get_retarget_chains())
    for chain_info in existing_chains:
        try:
            existing_name = chain_info.get_editor_property("chain_name")
            controller.remove_retarget_chain(existing_name)
        except Exception as e:
            unreal.log_warning(f"[FixChains] {rig_name}: could not remove old chain: {e}")

    for chain_name, start_bone, end_bone in CHAINS:
        try:
            result_name = controller.add_retarget_chain(
                unreal.Name(chain_name), unreal.Name(start_bone), unreal.Name(end_bone), unreal.Name("")
            )
            unreal.log(f"[FixChains] {rig_name}: added chain '{chain_name}' ({start_bone} -> {end_bone}) -> {result_name}")
        except Exception as e:
            unreal.log_error(f"[FixChains] {rig_name}: FAILED adding chain '{chain_name}': {e}")

    unreal.EditorAssetLibrary.save_loaded_asset(rig)
    unreal.log(f"[FixChains] Saved {rig_name}")

unreal.log("[FixChains] Done. Check IK_ChaosArmor and IK_StarterArmor in their editors -- "
           "each should now show 7 bone chains in the Skeleton/Chains view.")
