"""
ArmCannon dead-asset cleanup
=================================================================================
IRON BREACH / Unreal Engine 5.8

WHY THIS EXISTS
----------------
The editor logs this on every launch:

    LogLinker: Warning: Unable to load DA_ArmCannon with outer Package
    /Game/Weapons/MechWeapons/DA_ArmCannon because its class (WeaponDataAsset)
    does not exist

Investigation (done outside the editor, by scanning the .uasset files' raw
string tables -- see chat log for the full trail):

  - UWeaponDataAsset was removed from C++ when the weapon data split shipped
    (see migrate_weapon_data_split.py). Two .uasset files are still on disk
    with that now-nonexistent class and can never load again:
        /Game/Weapons/MechWeapons/DA_ArmCannon
        /Game/Sandbox/DA_ArmCannon        (an older duplicate/prototype)
    Both are confirmed dead weight -- nothing else in Content references
    either by path except BP_Mech (see below), and BP_Mech's reference can't
    resolve either way since the class is gone, so deleting these two files
    changes nothing else that currently works.

  - The already-migrated replacements, DA_Combat_ArmCannon and
    DA_Visual_ArmCannon (same folder, valid WeaponCombatData/WeaponVisualData
    classes, real copied values), are NOT referenced by anything in Content
    yet -- not by an IBItemDefinition, not by BP_Mech. Nothing currently
    wires the mech's cannon to real weapon data at all.

  - BP_Mech itself has its own Blueprint variable, `ArmCannon`
    (compiler-generated as ArmCannon_GEN_VARIABLE), typed as the dead
    UWeaponDataAsset, defaulting to the now-unloadable
    /Game/Weapons/MechWeapons/DA_ArmCannon. BP_Mech has NO references anywhere
    to WeaponComponent, CombatData, or VisualData -- meaning the mech cannon's
    firing logic never goes through UHitscanWeaponComponent /
    IDamageableInterface at all. This is almost certainly the actual root
    cause of the known bug ("ArmCannon bypasses armor/organs, uses generic
    Apply Damage instead of Handle Take Damage") noted in
    Docs/KAIJU_FIGHT_WIRING.md and UPDATELOG-2026-08-07.md: the cannon was
    never hooked into the shared combat pipeline in the first place, and its
    one piece of weapon data is a dead reference on top of that.

WHAT THIS SCRIPT DOES
----------------------
1. Deletes the two confirmed-dead WeaponDataAsset instances (safe: unloadable,
   unreferenced by anything that still works).
2. Prints a checklist for the BP_Mech fix, which is a Blueprint Event Graph
   change and can't be done safely from a script -- open BP_Mech and:
     a. Delete the orphaned `ArmCannon` variable (Class Defaults / My Blueprint
        panel will show it flagged as an unknown/missing type).
     b. Add a UHitscanWeaponComponent (or route firing through one already on
        the hull) and call SetWeaponData(DA_Combat_ArmCannon, DA_Visual_ArmCannon)
        the same way AIBCharacter_Infantry::BeginPlay does.
     c. Find wherever the cannon currently applies damage (an "Apply Damage"
        node per the Aug 7 updatelog) and replace it with the
        IDamageableInterface::HandleTakeDamage call HitscanWeaponComponent
        already uses for infantry, so armor/organ phases apply correctly.

HOW TO RUN IT
-------------
From the already-open editor's Output Log console (~) or Python console tab:
    py "X:/IronBreach/Content/Python/fix_armcannon_dead_asset_refs.py"
"""

import unreal

DEAD_ASSETS = [
    "/Game/Weapons/MechWeapons/DA_ArmCannon",
    "/Game/Sandbox/DA_ArmCannon",
]


def run():
    for path in DEAD_ASSETS:
        if unreal.EditorAssetLibrary.does_asset_exist(path):
            deleted = unreal.EditorAssetLibrary.delete_asset(path)
            unreal.log(f"[ArmCannon Cleanup] Deleted {path}: {deleted}")
        else:
            unreal.log(f"[ArmCannon Cleanup] {path} not found (already removed) -- skipping.")

    unreal.log(
        "[ArmCannon Cleanup] Dead-asset cleanup done. REMAINING MANUAL STEP: "
        "open BP_Mech (Characters/Mech/Blueprints/Class/BP_Mech) and (1) delete "
        "the orphaned 'ArmCannon' variable, (2) wire its firing logic through a "
        "UHitscanWeaponComponent using DA_Combat_ArmCannon / DA_Visual_ArmCannon "
        "(Weapons/MechWeapons/), (3) replace its damage-application node with "
        "HandleTakeDamage (IDamageableInterface) so armor/organ phases apply. "
        "See this script's module docstring for the full trail."
    )


run()
