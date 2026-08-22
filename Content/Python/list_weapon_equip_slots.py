"""
List every weapon item definition's assigned EquipSlot
=========================================================
IRON BREACH / Unreal Engine 5.8

WHAT THIS IS
------------
Diagnostic for the "picking up a second gun removes the first one" bug report.
The equip system already has 3 real weapon wells (WeaponPrimary/WeaponSpecial/
WeaponHeavy -- see EIBEquipSlot in Items/IBItemTypes.h) and picking up a weapon
routes it into whichever well ITS OWN UIBItemDefinition::EquipSlot says.
Nothing in the pickup/equip code path (UIBInventoryComponent::Equip_OnServer /
SetEquipmentSlot) ever removes an item from the bag -- so if two guns are both
landing in the same well, the most likely explanation is that their
UIBItemDefinition assets both have the SAME EquipSlot value assigned (probably
everything defaulting to Primary, since that's the only well anyone's tested
with so far), not an actual removal bug.

This script only LISTS what every weapon's EquipSlot is currently set to --
it changes nothing. Read the output: if every weapon reports the same slot,
that confirms the diagnosis, and fixing it means deciding (a design call, not
a code bug) which specific weapons should be Primary/Special/Heavy, then
either changing it by hand on each Data Asset (Content Browser -> open the
asset -> Equip Slot dropdown -> Primary/Special/Heavy -> Save) or telling me
the intended mapping so I can write a one-shot migration script matching this
project's existing migrate_*.py pattern.

HOW TO RUN IT
-------------
    py "X:/IronBreach/Content/Python/list_weapon_equip_slots.py"
"""

import unreal

# Every path a weapon Data Asset has shown up under in this project so far.
SEARCH_PATHS = (
    "/Game/Weapons",
    "/Game/IronBreach/Items",
)


def run():
    asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()

    found = 0
    for search_path in SEARCH_PATHS:
        asset_data_list = asset_registry.get_assets_by_path(search_path, recursive=True)
        for asset_data in asset_data_list:
            asset = asset_data.get_asset()
            if asset is None or not asset.get_class().get_name().startswith("IBItemDefinition"):
                # Also catch subclasses (weapon item defs may subclass the base).
                if not isinstance(asset, unreal.Object):
                    continue
                try:
                    equip_slot = asset.get_editor_property("equip_slot")
                except Exception:
                    continue
            else:
                try:
                    equip_slot = asset.get_editor_property("equip_slot")
                except Exception:
                    continue

            try:
                category = asset.get_editor_property("category")
            except Exception:
                category = "?"

            found += 1
            unreal.log(f"[Weapon Slots] {asset.get_name():>28}  category={str(category):<12}  equip_slot={equip_slot}  path={asset_data.package_name}")

    unreal.log(f"[Weapon Slots] {found} item definition asset(s) checked under {', '.join(SEARCH_PATHS)}.")


run()
