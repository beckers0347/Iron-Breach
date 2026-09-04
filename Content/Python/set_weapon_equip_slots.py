"""
Spread the 5 weapon types across Primary/Special/Heavy
==========================================================
IRON BREACH / Unreal Engine 5.8

WHAT THIS IS
------------
Fixes the "picking up a second gun evicts the first one" bug. list_weapon_
equip_slots.py confirmed all 5 weapon Data Assets (Sniper, SMG, Shotgun,
Rifle, Pistol) had EquipSlot hardcoded to WeaponPrimary -- so any two guns
always fought over the same well no matter what you were carrying.

Shane's chosen mapping (design call, not a code bug fix):
  - WeaponPrimary: Rifle, SMG        -- the main all-rounders
  - WeaponSpecial: Shotgun, Pistol, Sniper -- situational/close-range, and
    Sniper lands here for now rather than Heavy, since Heavy is being held
    open for Rocket Launchers once those exist. Revisit Sniper's slot then
    if it turns out Special is too crowded once Rocket Launchers ship.
  - WeaponHeavy: (nothing yet -- reserved for Rocket Launchers)

Two guns of the SAME type (two rifles, two SMGs) will still evict each other
-- that's inherent to a fixed type->slot model with only 3 wells for 5 types,
not something this script changes. If that turns out to matter in practice,
the alternative is a "first open slot, any gun" model instead of fixed
type->slot, which is a bigger change to Equip_OnServer, not a data tweak --
flag it if you hit that case and want to revisit.

HOW TO RUN IT
-------------
    py "X:/IronBreach/Content/Python/set_weapon_equip_slots.py"

Safe to re-run: it just sets these 5 assets' EquipSlot to the mapping above
every time, so a re-run always converges on the same state.
"""

import unreal

# (asset path, target EquipSlot)
SLOT_ASSIGNMENTS = (
    ("/Game/Weapons/Generated/Rifle/DA_Visual_Rifle_B",     unreal.IBEquipSlot.WEAPON_PRIMARY),
    ("/Game/Weapons/Generated/SMG/DA_Visual_SMG_B",         unreal.IBEquipSlot.WEAPON_PRIMARY),
    ("/Game/Weapons/Generated/Shotgun/DA_Visual_Shotgun_B", unreal.IBEquipSlot.WEAPON_SPECIAL),
    ("/Game/Weapons/Generated/Pistol/DA_Visual_Pistol_B",   unreal.IBEquipSlot.WEAPON_SPECIAL),
    ("/Game/Weapons/Generated/Sniper/DA_Visual_Sniper_B",   unreal.IBEquipSlot.WEAPON_SPECIAL),
)


def run():
    updated = 0
    for asset_path, target_slot in SLOT_ASSIGNMENTS:
        asset = unreal.EditorAssetLibrary.load_asset(asset_path)
        if asset is None:
            unreal.log_error(f"[Weapon Slots] Could not load {asset_path} -- skipped.")
            continue

        current_slot = asset.get_editor_property("equip_slot")
        if current_slot == target_slot:
            unreal.log(f"[Weapon Slots] {asset.get_name()}: already {target_slot} -- no change.")
            continue

        asset.set_editor_property("equip_slot", target_slot)
        unreal.EditorAssetLibrary.save_loaded_asset(asset)
        unreal.log(f"[Weapon Slots] {asset.get_name()}: {current_slot} -> {target_slot}")
        updated += 1

    unreal.log(f"[Weapon Slots] Done. {updated} asset(s) changed, {len(SLOT_ASSIGNMENTS) - updated} already correct.")


run()
