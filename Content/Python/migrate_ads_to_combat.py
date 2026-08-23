"""
ADS-to-Combat migration + single-asset weapon wiring (Phase 2 of 3)
=================================================================================
IRON BREACH / Unreal Engine 5.8

WHAT THIS IS
------------
Weapon setup used to require wiring TWO separate assets everywhere a weapon was
referenced: UIBItemDefinition::CombatData AND UIBItemDefinition::VisualData. This
collapses that to ONE: UWeaponVisualData now carries a CombatData link of its own,
so attaching the Visual asset (to an item, the weapon rack, a future loadout list)
is enough -- Combat comes along through that link. ADS tuning moves with it, from
UWeaponVisualData::Ads onto UWeaponCombatData::Ads (zoom/spread/handling is a
combat-feel concern, same bucket as damage/fire-rate/range).

This is Phase 2 of 3:

  Phase 1 (already landed): added UWeaponVisualData::CombatData (new link field)
  and UWeaponCombatData::Ads (new field), ALONGSIDE the old UWeaponVisualData::Ads
  and UIBItemDefinition::CombatData, which still exist purely so this script can
  read them.

  Phase 2 (this script): for every item that still has both the old CombatData
  and VisualData set, wires VisualData.CombatData -> that same Combat asset, and
  copies VisualData's old Ads values onto CombatData.Ads.

  Phase 3 (separate handoff, do NOT apply until you've verified this script's
  output): removes UWeaponVisualData::Ads and UIBItemDefinition::CombatData for
  good, and retargets every consumer (HitscanWeaponComponent, AIBCharacter_Infantry,
  AIBCharacter_Enemy, AIBMech_Base/IBGunnerSeat) to take a single UWeaponVisualData*
  and resolve Combat through its CombatData link instead of a separate parameter.

Only run this between a Phase-1 compile and the Phase-3 changes -- it needs the
OLD field (UIBItemDefinition::CombatData, still readable) and the NEW fields
(UWeaponVisualData::CombatData, UWeaponCombatData::Ads, both writable) to all
exist in the same editor session, which is only true in that window.

WHAT IT DOES
------------
1. Finds every UIBItemDefinition instance under /Game whose (deprecated)
   CombatData is set.
2. For each one:
     - If its VisualData.CombatData is unset, points it at the item's CombatData
       and copies VisualData's old Ads struct onto CombatData.Ads.
     - If VisualData.CombatData is ALREADY set (e.g. a previous run of this
       script, or hand-wired since), leaves both alone -- doesn't re-copy Ads,
       so a manual tweak made after a first run is never stomped.
3. Saves every VisualData/CombatData asset it touched.

HOW TO RUN IT
-------------
1. Confirm the editor compiled cleanly with the Phase 1 changes.
2. From the Output Log console (~) or the Python console tab:
       py "X:/IronBreach/Content/Python/migrate_ads_to_combat.py"
3. Read the Output Log. Spot-check one weapon in the Content Browser --
   DA_Visual_ArmCannon's CombatData should now point at DA_Combat_ArmCannon,
   and DA_Combat_ArmCannon's new Ads block should match what DA_Visual_ArmCannon's
   (deprecated) Ads block used to show.
4. Only once that looks right, apply the Phase 3 C++ changes and rebuild.

Safe to re-run: a VisualData asset whose CombatData link is already set is left
alone entirely (no re-copy of Ads), so re-running after hand-tuning Ads on a
Combat asset won't stomp it.
"""

import unreal

registry = unreal.AssetRegistryHelpers.get_asset_registry()


def safe(fn, label):
    try:
        return fn()
    except Exception as e:  # noqa: BLE001
        unreal.log_warning(f"[ADS Migration] Skipped '{label}': {e}")
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
    old_combat = item.get_editor_property("combat_data")
    visual = item.get_editor_property("visual_data")

    if old_combat is None:
        return False  # nothing set on this item -- not a migration candidate

    if visual is None:
        unreal.log_warning(
            f"[ADS Migration] {item.get_name()}: has CombatData ({old_combat.get_name()}) "
            f"but no VisualData -- can't wire the link, skipping.")
        return False

    existing_link = visual.get_editor_property("combat_data")
    if existing_link is not None:
        unreal.log(
            f"[ADS Migration] {visual.get_name()}.CombatData already set to "
            f"{existing_link.get_name()} -- leaving it (and its Ads) alone.")
        return False

    visual.set_editor_property("combat_data", old_combat)
    old_combat.set_editor_property("ads", visual.get_editor_property("ads"))

    unreal.EditorAssetLibrary.save_loaded_asset(visual)
    unreal.EditorAssetLibrary.save_loaded_asset(old_combat)

    unreal.log(
        f"[ADS Migration] {visual.get_name()}: CombatData -> {old_combat.get_name()}, "
        f"Ads copied across.")
    return True


def run():
    items = [i for i in find_assets_of_class("IBItemDefinition") if i is not None]
    unreal.log(f"[ADS Migration] Scanning {len(items)} item definition(s).")

    migrated = 0
    for item in items:
        if safe(lambda i=item: migrate_one(i), f"migrate {item.get_name()}"):
            migrated += 1

    unreal.log(
        f"[ADS Migration] Done. {migrated} weapon(s) wired (VisualData.CombatData set, "
        f"Ads copied). Verify DA_Visual_ArmCannon / DA_Combat_ArmCannon in the Content "
        f"Browser before applying the Phase 3 C++ changes that remove the deprecated fields."
    )


run()
