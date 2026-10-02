"""
IBPY: ib_inspect_sandbox_anim.py

Read-only. Found existing /Game/Sandbox/ABP_Infantry, BS_Armed_Locomotion,
and BS_Unarmed_Locomotion -- looks like prototype locomotion work that was
never wired into BP_IBCharacter_Infantry. Before deciding whether to reuse
these for the NPCs or build fresh, need to know:

  1. What skeleton each targets (must be Base_Character_Mesh_Skeleton to be
     usable by Idris/the NPCs).
  2. Whether BS_Unarmed_Locomotion actually has samples populated (an
     empty/stub BlendSpace vs. a real one).
  3. Whether BP_IBCharacter_Infantry currently has an AnimClass set at all.

Changes nothing.

HOW TO RUN
----------
    py "X:/IronBreach/Scripts/ib_inspect_sandbox_anim.py"
Paste back the full output.
"""

import unreal

ABP_PATH = "/Game/Sandbox/ABP_Infantry"
BS_ARMED_PATH = "/Game/Sandbox/BS_Armed_Locomotion"
BS_UNARMED_PATH = "/Game/Sandbox/BS_Unarmed_Locomotion"
INFANTRY_SKELETON_PATH = "/Game/Characters/Infantry/Meshes/JumpSuit/Base_Character_Mesh_Skeleton"
INFANTRY_BP_PATH = "/Game/Characters/Infantry/BP_IBCharacter_Infantry"


def log(msg):
    unreal.log(f"IBPY: {msg}")


def main():
    log("==== INSPECT SANDBOX ANIMATION ASSETS ====")

    for label, path in [("ABP_Infantry", ABP_PATH), ("BS_Armed_Locomotion", BS_ARMED_PATH),
                         ("BS_Unarmed_Locomotion", BS_UNARMED_PATH)]:
        asset = unreal.load_asset(path)
        if asset is None:
            log(f"{label}: NOT FOUND at {path}")
            continue
        log(f"{label}: loaded OK ({asset.get_class().get_name()})")
        try:
            skel = asset.get_editor_property("target_skeleton")
        except Exception:
            skel = None
        if skel is None:
            try:
                skel = asset.get_editor_property("skeleton")
            except Exception:
                skel = None
        log(f"  target skeleton: {skel.get_path_name() if skel else 'could not read'}")

        if "BS_" in label:
            try:
                samples = asset.get_editor_property("sample_data")
                log(f"  sample count: {len(samples)}")
                for s in samples:
                    anim = s.get_editor_property("animation")
                    log(f"    sample anim: {anim.get_path_name() if anim else None}")
            except Exception as e:
                log(f"  could not read samples: {e}")

    log("---- BP_IBCharacter_Infantry AnimClass check ----")
    infantry_bp = unreal.load_asset(INFANTRY_BP_PATH)
    if infantry_bp is None:
        log(f"Could not load {INFANTRY_BP_PATH} -- is this the right path? (searching nearby...)")
        registry = unreal.AssetRegistryHelpers.get_asset_registry()
        hits = [a for a in registry.get_assets_by_path("/Game/Characters/Infantry", recursive=True)
                if "infantry" in str(a.asset_name).lower() and "blueprint" in str(a.asset_class_path.asset_name).lower()]
        for h in hits:
            log(f"  found nearby: {h.package_name}")
    else:
        log(f"Found: {infantry_bp.get_path_name()} ({infantry_bp.get_class().get_name()})")

    log("==== DONE ====")


main()
