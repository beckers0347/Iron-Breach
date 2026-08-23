"""
Item-into-Visual migration (Phase 2 of 3)
=================================================================================
IRON BREACH / Unreal Engine 5.8

WHAT THIS IS
------------
Weapon setup used to mean wiring THREE assets per weapon: DA_Item_* (the thing
the rack/inventory actually reference), plus its DA_Combat_*/DA_Visual_* pair.
UWeaponVisualData is now itself a UIBItemDefinition subclass (see Combat/
WeaponVisualData.h) -- it carries the item-facing fields (DisplayName, Icon,
EquipSlot, Rarity, Stats, MaxStack, ...) directly, alongside its existing
weapon-facing fields (mesh, scale, alignment) and its CombatData link (damage/
fire-rate/range/ADS, on the sibling UWeaponCombatData asset). One asset -- the
Visual one -- now covers everything a weapon needs to be attached to the rack,
inventory, or a loadout list.

This supersedes migrate_ads_to_combat.py -- this script does everything that one
did (wires VisualData.CombatData, copies Ads across) PLUS copies each old
DA_Item_*'s own fields onto its paired VisualData asset. Safe to run whether or
not migrate_ads_to_combat.py already ran (the Combat-link step below skips
anything already wired, exactly like that script did).

This is Phase 2 of 3:

  Phase 1 (already landed): UWeaponVisualData now inherits UIBItemDefinition
  (gaining DisplayName/Icon/EquipSlot/etc. as new, so-far-unset inherited
  fields) and still carries CombatData (link) alongside UWeaponCombatData's new
  Ads field. The OLD UIBItemDefinition::CombatData/VisualData fields and
  UWeaponVisualData's OLD Ads field all still exist, purely so this script can
  read them.

  Phase 2 (this script): for every legacy DA_Item_* with VisualData set, copies
  that item's own fields onto the VisualData asset (which now has somewhere to
  put them), and wires VisualData.CombatData / copies Ads exactly as the
  previous script did.

  Phase 3 (separate handoff, do NOT apply until you've verified this script's
  output AND re-pointed your weapon rack instance(s) at the new Visual assets):
  removes UIBItemDefinition::CombatData/VisualData and UWeaponVisualData::Ads
  for good, and retargets AIBCharacter_Infantry (and anywhere else that read
  Item.Definition->VisualData) to Cast<UWeaponVisualData>(Item.Definition)
  instead, since the item IS the weapon asset now.

WHAT IT DOES
------------
1. Finds every UIBItemDefinition instance under /Game that is NOT itself a
   UWeaponVisualData (i.e. the legacy DA_Item_* wrapper assets) and whose
   (deprecated) VisualData is set.
2. For each one, onto the paired VisualData asset:
     - Copies DisplayName, Description, Flavor, Category, Rarity, EquipSlot,
       Icon, MaxStack, BaseClearanceRating, Stats, bShowInLedger from the item.
     - If VisualData.CombatData is unset, points it at the item's (deprecated)
       CombatData and copies VisualData's old Ads struct onto CombatData.Ads
       (same step migrate_ads_to_combat.py did). Skipped if already wired, so a
       manual Ads tweak made after an earlier run is never stomped.
3. Saves every VisualData/CombatData asset it touched.

WHAT IT DOES NOT DO
-------------------
Your weapon rack instance(s) in the level still point their StockedWeapons
entries at the OLD DA_Item_* assets. Since those are placed-actor properties,
not Content Browser assets, this script can't safely bulk-edit them -- after
running this and confirming the copy looks right, open each BP_WeaponRack
instance and re-point StockedWeapons at the DA_Visual_* assets directly (they
work as drop-in replacements everywhere a UIBItemDefinition was expected). Same
for anywhere else a DA_Item_* weapon is hand-referenced (a loadout default, a
loot table entry, etc.).

HOW TO RUN IT
-------------
1. Confirm the editor compiled cleanly with the Phase 1 changes.
2. From the Output Log console (~) or the Python console tab:
       py "X:/IronBreach/Content/Python/migrate_item_into_visual.py"
3. Read the Output Log, then spot-check one weapon in the Content Browser --
   DA_Visual_ArmCannon should now show a real DisplayName/Icon/EquipSlot (copied
   from DA_Item_ArmCannon, or whatever the arm cannon's item asset is named) and
   CombatData pointing at DA_Combat_ArmCannon with the old ADS values on it.
4. Re-point your weapon rack instance(s)' StockedWeapons at the DA_Visual_*
   assets (see "WHAT IT DOES NOT DO" above).
5. Only once both of those look right, apply the Phase 3 C++ changes and rebuild.

Safe to re-run: field copies are simple overwrites (idempotent -- copying the
same values again is a no-op), and the CombatData-link step skips anything
already wired, so re-running after hand-editing a migrated VisualData asset's
Ads won't stomp it.
"""

import unreal

registry = unreal.AssetRegistryHelpers.get_asset_registry()

ITEM_FIELDS = [
    "display_name",
    "description",
    "flavor",
    "category",
    "rarity",
    "equip_slot",
    "icon",
    "max_stack",
    "base_clearance_rating",
    "stats",
    "show_in_ledger",
]


def safe(fn, label):
    try:
        return fn()
    except Exception as e:  # noqa: BLE001
        unreal.log_warning(f"[Item->Visual Migration] Skipped '{label}': {e}")
        return None


def find_assets_of_class(class_name):
    ar_filter = unreal.ARFilter(
        class_names=[class_name],
        recursive_classes=True,
        package_paths=["/Game"],
        recursive_paths=True,
    )
    return [d.get_asset() for d in registry.get_assets(ar_filter)]


def migrate_one(item):
    # A UWeaponVisualData instance is itself a UIBItemDefinition -- skip it here,
    # it's a destination in this script, not a legacy wrapper to migrate FROM.
    if isinstance(item, unreal.WeaponVisualData):
        return False

    visual = item.get_editor_property("visual_data")
    if visual is None:
        return False  # not a weapon item, or never had a VisualData link -- nothing to do

    copied_fields = []
    for field in ITEM_FIELDS:
        value = item.get_editor_property(field)
        visual.set_editor_property(field, value)
        copied_fields.append(field)
    unreal.EditorAssetLibrary.save_loaded_asset(visual)
    unreal.log(f"[Item->Visual Migration] {visual.get_name()}: copied {len(copied_fields)} field(s) from {item.get_name()}.")

    old_combat = item.get_editor_property("legacy_combat_data")
    if old_combat is not None:
        existing_link = visual.get_editor_property("combat_data")
        if existing_link is None:
            visual.set_editor_property("combat_data", old_combat)
            old_combat.set_editor_property("ads", visual.get_editor_property("ads"))
            unreal.EditorAssetLibrary.save_loaded_asset(visual)
            unreal.EditorAssetLibrary.save_loaded_asset(old_combat)
            unreal.log(
                f"[Item->Visual Migration] {visual.get_name()}: CombatData -> {old_combat.get_name()}, Ads copied across.")
        else:
            unreal.log(
                f"[Item->Visual Migration] {visual.get_name()}.CombatData already set to "
                f"{existing_link.get_name()} -- leaving it (and its Ads) alone.")

    return True


def run():
    items = [i for i in find_assets_of_class("IBItemDefinition") if i is not None]
    unreal.log(f"[Item->Visual Migration] Scanning {len(items)} item definition(s) (includes VisualData assets themselves -- those are skipped as destinations).")

    migrated = 0
    for item in items:
        if safe(lambda i=item: migrate_one(i), f"migrate {item.get_name()}"):
            migrated += 1

    unreal.log(
        f"[Item->Visual Migration] Done. {migrated} weapon(s) migrated onto their VisualData asset. "
        f"Verify in the Content Browser, then re-point your weapon rack instance(s)' StockedWeapons at "
        f"the DA_Visual_* assets directly before applying the Phase 3 C++ changes."
    )


run()
