"""
Weapon Data Asset split -- migration script (Phase 2 of 3)
=================================================================================
IRON BREACH / Unreal Engine 5.8

WHAT THIS IS
------------
UWeaponDataAsset is being split into UWeaponCombatData (BaseDamage/MaxRange/
FireRate -- power scaling) and UWeaponVisualData (mesh/scale/offset/effects/
ADS -- presentation). This is Phase 2 of 3:

  Phase 1 (already landed): added the two new classes, and two new fields --
  CombatData, VisualData -- onto UIBItemDefinition, ALONGSIDE the old
  WeaponData field, which still exists purely so this script can read it.

  Phase 2 (this script): copies every existing UWeaponDataAsset's values into
  a new DA_Combat_*/DA_Visual_* pair, and points every UIBItemDefinition's new
  CombatData/VisualData fields at the right pair.

  Phase 3 (separate handoff, do NOT apply until you've verified this script's
  output): removes UWeaponDataAsset and IBItemDefinition::WeaponData for good,
  and retargets HitscanWeaponComponent / AIBCharacter_Infantry / the Weapon
  Generator editor tools onto the split classes exclusively.

Only run this between a Phase-1 compile and the Phase-3 changes -- it needs
the OLD class (still readable) and the NEW classes (writable) to both exist
in the same editor session, which is only true in that window.

WHAT IT DOES
------------
1. Finds every UWeaponDataAsset instance under /Game (7 as of this writing:
   DA_Pistol_B, DA_Rifle_B, DA_Rifle_C, DA_Shotgun_B, DA_SMG_B, DA_Sniper_B,
   DA_ArmCannon).
2. For each one, creates a DA_Combat_<Name> and DA_Visual_<Name> asset in the
   SAME folder as the original (e.g. DA_Pistol_B -> DA_Combat_Pistol_B +
   DA_Visual_Pistol_B, right next to it), copying:
     - Combat: BaseDamage, MaxRange, FireRate
     - Visual: WeaponName, MFXTracer, FireSound, Ads, ViewmodelScale,
       ViewmodelLocationOffset, ViewmodelRotationOffset, ViewmodelMesh
3. Finds every UIBItemDefinition whose (deprecated) WeaponData is set and
   points its CombatData/VisualData fields at the matching pair from step 2.
4. Saves everything it touched.

HOW TO RUN IT
-------------
1. Confirm the editor compiled cleanly with the Phase 1 changes.
2. From the Output Log console (~) or the Python console tab:
       py "X:/IronBreach/Content/Python/migrate_weapon_data_split.py"
3. Read the Output Log. Check the Content Browser: each weapon folder should
   now have a DA_Combat_* / DA_Visual_* pair next to the original DA_*.
   Spot-check DA_Combat_ArmCannon / DA_Visual_ArmCannon especially -- the mech
   cannon is the one most likely to carry real hand-authored mesh/FX/ADS
   values worth eyeballing before trusting the copy.
4. Only once that looks right, apply the Phase 3 C++ changes and rebuild.

Safe to re-run: does_asset_exist checks mean a second run reuses whatever
already exists rather than duplicating -- but it will NOT re-copy values into
an asset that already exists, so hand edits you've made to a migrated
DA_Combat_*/DA_Visual_* since the last run are left alone, not stomped.
"""

import unreal

asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
registry = unreal.AssetRegistryHelpers.get_asset_registry()


def safe(fn, label):
    try:
        return fn()
    except Exception as e:  # noqa: BLE001
        unreal.log_warning(f"[Weapon DA Split] Skipped '{label}': {e}")
        return None


def find_assets_of_class(class_name):
    ar_filter = unreal.ARFilter(
        class_names=[class_name],
        recursive_classes=True,
        package_paths=["/Game"],
        recursive_paths=True,
    )
    return [d.get_asset() for d in registry.get_assets(ar_filter)]


def strip_da_prefix(name):
    return name[3:] if name.startswith("DA_") else name


def create_data_asset(folder, name, klass):
    full_path = f"{folder}/{name}"
    if unreal.EditorAssetLibrary.does_asset_exist(full_path):
        return unreal.EditorAssetLibrary.load_asset(full_path), False
    factory = unreal.DataAssetFactory()
    factory.set_editor_property("data_asset_class", klass)
    new_asset = asset_tools.create_asset(name, folder, klass, factory)
    return new_asset, True


def migrate_one(old_da):
    old_name = old_da.get_name()
    folder = str(old_da.get_outermost().get_name()).rsplit("/", 1)[0]
    base_name = strip_da_prefix(old_name)

    combat, combat_new = create_data_asset(folder, f"DA_Combat_{base_name}", unreal.WeaponCombatData)
    visual, visual_new = create_data_asset(folder, f"DA_Visual_{base_name}", unreal.WeaponVisualData)

    if combat_new:
        combat.set_editor_property("base_damage", old_da.get_editor_property("base_damage"))
        combat.set_editor_property("max_range", old_da.get_editor_property("max_range"))
        combat.set_editor_property("fire_rate", old_da.get_editor_property("fire_rate"))
        unreal.EditorAssetLibrary.save_loaded_asset(combat)
        unreal.log(f"[Weapon DA Split] Created {combat.get_path_name()}")
    else:
        unreal.log(f"[Weapon DA Split] {combat.get_path_name()} already exists -- left as-is.")

    if visual_new:
        visual.set_editor_property("weapon_name", old_da.get_editor_property("weapon_name"))
        visual.set_editor_property("mfx_tracer", old_da.get_editor_property("mfx_tracer"))
        visual.set_editor_property("fire_sound", old_da.get_editor_property("fire_sound"))
        visual.set_editor_property("ads", old_da.get_editor_property("ads"))
        visual.set_editor_property("viewmodel_scale", old_da.get_editor_property("viewmodel_scale"))
        visual.set_editor_property("viewmodel_location_offset", old_da.get_editor_property("viewmodel_location_offset"))
        visual.set_editor_property("viewmodel_rotation_offset", old_da.get_editor_property("viewmodel_rotation_offset"))
        visual.set_editor_property("viewmodel_mesh", old_da.get_editor_property("viewmodel_mesh"))
        unreal.EditorAssetLibrary.save_loaded_asset(visual)
        unreal.log(f"[Weapon DA Split] Created {visual.get_path_name()}")
    else:
        unreal.log(f"[Weapon DA Split] {visual.get_path_name()} already exists -- left as-is.")

    return combat, visual


def run():
    old_weapons = [w for w in find_assets_of_class("WeaponDataAsset") if w is not None]
    unreal.log(f"[Weapon DA Split] Found {len(old_weapons)} existing UWeaponDataAsset instance(s).")

    pair_by_old_path = {}
    for old_da in old_weapons:
        result = safe(lambda o=old_da: migrate_one(o), f"migrate {old_da.get_name()}")
        if result:
            pair_by_old_path[old_da.get_path_name()] = result

    items = [i for i in find_assets_of_class("IBItemDefinition") if i is not None]
    relinked = 0
    for item in items:
        def relink(item=item):
            old_weapon_data = item.get_editor_property("weapon_data")
            if old_weapon_data is None:
                return False
            pair = pair_by_old_path.get(old_weapon_data.get_path_name())
            if not pair:
                unreal.log_warning(
                    f"[Weapon DA Split] {item.get_name()}: WeaponData points at "
                    f"{old_weapon_data.get_path_name()}, which wasn't migrated above -- skipping.")
                return False
            combat, visual = pair
            item.set_editor_property("combat_data", combat)
            item.set_editor_property("visual_data", visual)
            unreal.EditorAssetLibrary.save_loaded_asset(item)
            unreal.log(f"[Weapon DA Split] {item.get_name()}: CombatData/VisualData set from {old_weapon_data.get_name()}.")
            return True

        if safe(relink, f"relink {item.get_name()}"):
            relinked += 1

    unreal.log(
        f"[Weapon DA Split] Done. {len(pair_by_old_path)} weapon(s) split, {relinked} item definition(s) relinked. "
        f"Verify in the Content Browser -- especially DA_Combat_ArmCannon/DA_Visual_ArmCannon -- "
        f"before applying the Phase 3 C++ changes that remove the old class."
    )


run()
