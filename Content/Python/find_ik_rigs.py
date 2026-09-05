"""
Search the project for any existing IK Rig / IK Retargeter assets, and check
whether Chaos_Armor_Skeleton already has one set up. Needed before building
an IK Retargeter for Starter Armor -- IK Retargeting needs an IK Rig asset
for BOTH the source skeleton (Chaos_Armor_Skeleton) and the target skeleton
(the armor's own), and if Chaos_Armor already has one from an earlier
pipeline (e.g. the Landfall evacuee work), reusing it is much less work than
building a fresh one from scratch.

HOW TO RUN IT
-------------
    py "X:/IronBreach/Content/Python/find_ik_rigs.py"

Prints every IK Rig and IK Retargeter asset found in the project, and which
skeleton each IK Rig is built for.
"""

import unreal

asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()

for class_name in ("IKRigDefinition", "RetargetChainSettings", "IKRetargeter"):
    ar_filter = unreal.ARFilter(
        class_names=[class_name],
        package_paths=["/Game"],
        recursive_paths=True,
        recursive_classes=True,
    )
    assets = asset_registry.get_assets(ar_filter)
    unreal.log(f"[FindIKRigs] {class_name}: {len(assets)} found")
    for a in assets:
        unreal.log(f"[FindIKRigs]   {a.package_name}")
        try:
            obj = a.get_asset()
            skel = obj.get_editor_property("preview_mesh") if obj else None
            unreal.log(f"[FindIKRigs]     preview_mesh: {skel}")
        except Exception as e:
            unreal.log(f"[FindIKRigs]     (couldn't read preview_mesh: {e})")
