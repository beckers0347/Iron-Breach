"""
Reparent ABP_InfantryTripo3D to the new native AnimInstance
================================================================
IRON BREACH / Unreal Engine 5.8

WHAT THIS IS
------------
RUN THIS ONLY AFTER a successful C++ compile that includes
UIBAnimInstance_Infantry (Source/IronBreach/Infantry/IBAnimInstance_Infantry.h
/.cpp) -- the class has to actually exist in the loaded module before this can
find it.

Points ABP_InfantryTripo3D's parent class at UIBAnimInstance_Infantry instead
of the default AnimInstance, the same thing you'd do by hand via Class
Settings -> Parent Class in the ABP editor. Once this runs, the AnimGraph's
Blueprint variable list picks up Speed/Direction/bIsInAir/bIsCrouching/
bIsSprinting/bIsCarrying/bIsArmed/bIsAiming/ActiveWeaponSlot/bIsDead as
already-populated Get nodes -- build the state machine/blend spaces against
those and drop the InfantryTripo3D AnimSequences in.

HOW TO RUN IT
-------------
    py "X:/IronBreach/Content/Python/reparent_infantry_animbp.py"

Safe to re-run.
"""

import unreal

ABP_PATH = "/Game/Characters/Infantry/InfantryTripo3D/ABP_InfantryTripo3D.ABP_InfantryTripo3D"
NEW_PARENT_CLASS_PATH = "/Script/IronBreach.IBAnimInstance_Infantry"


def run():
    anim_bp = unreal.EditorAssetLibrary.load_asset(ABP_PATH)
    if anim_bp is None:
        unreal.log_error(f"[Infantry ABP Reparent] {ABP_PATH} not found -- run "
                          "build_infantry_tripo3d_animbp.py first if it hasn't been created yet.")
        return

    new_parent = unreal.load_class(None, NEW_PARENT_CLASS_PATH)
    if new_parent is None:
        unreal.log_error(f"[Infantry ABP Reparent] Could not load class {NEW_PARENT_CLASS_PATH} -- "
                          "make sure the C++ build actually succeeded (UIBAnimInstance_Infantry compiled "
                          "into the IronBreach module) before running this.")
        return

    current_parent = anim_bp.get_editor_property("parent_class")
    if current_parent == new_parent:
        unreal.log(f"[Infantry ABP Reparent] {ABP_PATH} already parented to {NEW_PARENT_CLASS_PATH} -- no change.")
        return

    unreal.BlueprintEditorLibrary.reparent_blueprint(anim_bp, new_parent)
    unreal.BlueprintEditorLibrary.compile_blueprint(anim_bp)
    unreal.EditorAssetLibrary.save_loaded_asset(anim_bp)
    unreal.log(f"[Infantry ABP Reparent] {ABP_PATH} reparented {current_parent} -> {NEW_PARENT_CLASS_PATH} and recompiled.")


run()
