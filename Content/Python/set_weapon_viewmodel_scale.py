"""
Batch-set ViewmodelScale on every UWeaponVisualData asset
=================================================================================
IRON BREACH / Unreal Engine 5.8

WHY
---
Every DA_Visual_* weapon's ViewmodelScale was still sitting at or near the
default (1.0) -- full world scale -- which reads as enormous in the first-person
view. ViewmodelScale's ClampMin used to be 0.01, which silently clamped any
smaller value you tried to type in back up to 0.01 -- so if these meshes were
authored at mech/kaiju scale and reused for the infantry viewmodel, there was no
way to dial them down far enough. That floor is now 0.0001 (WeaponVisualData.h).

This script gives every weapon a much smaller uniform starting scale in one
pass instead of hand-editing dozens of assets. It is NOT a precision fix --
different weapon meshes were very likely authored at different sizes, so some
will still look off after this runs. Once you rebuild, you can nudge each one
individually with the details panel WHILE PIE IS RUNNING and see it update
immediately (WeaponVisualData::OnVisualDataChanged / the live-tune fix) --
no more restart-PIE-to-check loop.

HOW TO RUN IT
-------------
1. Edit TARGET_SCALE below if you want a different starting point.
2. From the Output Log console (~) or the Python console tab:
       py "X:/IronBreach/Content/Python/set_weapon_viewmodel_scale.py"
3. Read the Output Log for the old -> new value on every weapon it touched.
4. Enter PIE and live-tune any weapon that's still off, per the note above.

Safe to re-run: it's a plain overwrite of ViewmodelScale on every
UWeaponVisualData asset found under /Game, logging what it changes.
"""

import unreal

# Edit this before running if 0.05 isn't the right starting point for your
# meshes. All three axes (X/Y/Z) are set uniformly.
TARGET_SCALE = 0.05

registry = unreal.AssetRegistryHelpers.get_asset_registry()


def find_assets_of_class(class_name):
    ar_filter = unreal.ARFilter(
        class_names=[class_name],
        recursive_classes=True,
        package_paths=["/Game"],
        recursive_paths=True,
    )
    return [d.get_asset() for d in registry.get_assets(ar_filter)]


def run():
    weapons = [w for w in find_assets_of_class("WeaponVisualData") if w is not None]
    unreal.log(f"[ViewmodelScale] Found {len(weapons)} UWeaponVisualData asset(s).")

    new_scale = unreal.Vector(TARGET_SCALE, TARGET_SCALE, TARGET_SCALE)
    changed = 0

    for weapon in weapons:
        try:
            old_scale = weapon.get_editor_property("viewmodel_scale")
            weapon.set_editor_property("viewmodel_scale", new_scale)
            unreal.EditorAssetLibrary.save_loaded_asset(weapon)
            unreal.log(f"[ViewmodelScale] {weapon.get_name()}: {old_scale} -> {new_scale}")
            changed += 1
        except Exception as e:  # noqa: BLE001
            unreal.log_warning(f"[ViewmodelScale] Skipped '{weapon.get_name()}': {e}")

    unreal.log(
        f"[ViewmodelScale] Done. {changed} weapon(s) set to {new_scale}. "
        f"Enter PIE and live-tune any that still look wrong -- edits to a weapon's "
        f"DA_Visual_* now apply immediately while PIE is running."
    )


run()
