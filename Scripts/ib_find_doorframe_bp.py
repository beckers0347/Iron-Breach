"""
IBPY: ib_find_doorframe_bp.py

READ-ONLY. Since the Garrison rebuild has zero DoorFrame actors placed
now, this checks whether the DoorFrame Blueprint CLASS itself (used
earlier for the doors you and I scripted before) still exists as an
asset in the project -- even though no instances of it are in the level
right now. If it exists, we can reuse it (just place new instances at
each building). If not, we'll need to rebuild it from scratch.

Searches the asset registry for any Blueprint asset whose name contains
"door" (case-insensitive), anywhere in the project.

HOW TO RUN:
  py "X:/IronBreach/Scripts/ib_find_doorframe_bp.py"
"""

import unreal


def log(msg):
    unreal.log(f"IBPY: {msg}")


def main():
    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    filter_ = unreal.ARFilter(
        class_names=["Blueprint"],
        package_paths=["/Game"],
        recursive_paths=True,
        recursive_classes=True,
    )
    assets = registry.get_assets(filter_)
    log(f"Total Blueprint assets in /Game: {len(assets)}")

    matches = [a for a in assets if "door" in str(a.asset_name).lower()]
    log(f"---- Blueprint assets with 'door' in the name: {len(matches)} ----")
    for a in matches:
        log(f"  {a.package_name} (asset_name='{a.asset_name}')")

    if not matches:
        log("No door-related Blueprint found. We'll need to rebuild the DoorFrame "
            "Blueprint (trigger box + reference geometry) from scratch.")

    log("Done. Nothing was modified.")


main()
