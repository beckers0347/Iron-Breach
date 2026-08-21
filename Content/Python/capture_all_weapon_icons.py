"""
Batch-capture an Icon for every UWeaponVisualData asset
=================================================================================
IRON BREACH / Unreal Engine 5.8

WHY
---
"Capture Icon From Mesh" (the right-click content-browser action) only ever
worked one weapon at a time, and until the C++ fix that shipped alongside this
script it didn't even do that -- ItemIconCaptureLibrary::CaptureItemIcon read
Definition->VisualData (the OLD trio-architecture link from a separate
DA_Item_* wrapper to its DA_Visual_*), which is null for every new-style weapon
where the DA_Visual_* IS the item directly. That's why only one weapon (an
old, not-yet-migrated DA_Item_*) ever had a working icon -- it's now fixed to
resolve VisualData as Definition itself first, falling back to the legacy link.

This script runs that fixed capture across every UWeaponVisualData asset in
one pass instead of right-clicking each one by hand.

HOW TO RUN IT
-------------
1. Make sure the editor has rebuilt with the ItemIconCaptureLibrary.cpp fix.
2. From the Output Log console (~) or the Python console tab:
       py "X:/IronBreach/Content/Python/capture_all_weapon_icons.py"
3. Read the Output Log for a per-weapon success/failure line. A weapon fails
   here only if it has no ViewmodelMesh assigned yet -- that's a content gap
   (add the mesh), not a bug.
4. LightIntensity/ExposureBias below are the same starting points the manual
   tool uses -- if a particular icon comes back too dark/blown out, re-run
   CaptureItemIcon for just that one weapon with adjusted values (see
   ItemIconCaptureLibrary.h) rather than re-running this whole script with
   different numbers for everyone.

Safe to re-run: each capture overwrites that weapon's existing generated icon
texture and Icon reference, logging what it does.
"""

import unreal

# Same defaults as the manual "Capture Icon From Mesh" menu action.
RESOLUTION = 256
LIGHT_INTENSITY = 15000.0
EXPOSURE_BIAS = 2.0

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
    unreal.log(f"[IconCapture] Found {len(weapons)} UWeaponVisualData asset(s).")

    captured = 0
    failed = 0

    for weapon in weapons:
        icon = unreal.ItemIconCaptureLibrary.capture_item_icon(
            weapon, RESOLUTION, LIGHT_INTENSITY, EXPOSURE_BIAS, unreal.Rotator(0, 0, 0)
        )
        if icon:
            unreal.log(f"[IconCapture] {weapon.get_name()}: captured -> {icon.get_name()}")
            captured += 1
        else:
            unreal.log_warning(
                f"[IconCapture] {weapon.get_name()}: capture failed -- see the toast/warning "
                f"above for the reason (usually a missing ViewmodelMesh)."
            )
            failed += 1

    unreal.log(f"[IconCapture] Done. {captured} captured, {failed} failed out of {len(weapons)}.")


run()
