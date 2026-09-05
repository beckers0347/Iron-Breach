"""
Set up IK Retargeting so Starter Armor can reuse Chaos_Armor_Skeleton's 38
InfantryTripo3D animations WITHOUT forcing a literal shared-skeleton merge
(that approach hit a hard engine-level wall: "cannot merge bone tree with
the existing skeleton" -- confirmed to be about bind-pose bone transforms,
not just names/hierarchy, and rebuilding the rig to match those transforms
exactly wasn't reliable given how the exported FBX round-trip data behaved).

WHAT THIS DOES
--------------
1. Imports the armor mesh onto its OWN independent skeleton (SK_StarterArmor
   / a new Skeleton asset) -- no forced assignment, no collision risk.
2. Builds an IK Rig for Chaos_Armor_Skeleton (the animation SOURCE).
3. Builds an IK Rig for the armor's own skeleton (the RETARGET TARGET).
4. Creates an IK Retargeter asset linking the two, with matching bone chains
   (Spine, Head, LeftArm/RightArm, LeftLeg/RightLeg) so poses transfer
   correctly between the two differently-proportioned skeletons.

This is heavily wrapped in try/except with logging at each step, since the
IK Rig Python API hasn't been used in this project before -- if any single
call has the wrong exact signature, you'll get a clear error naming which
step failed rather than a silent no-op, and I can fix just that part.

HOW TO RUN IT
-------------
    py "X:/IronBreach/Content/Python/build_ik_retargeting.py"

After it runs, open RTG_ChaosArmor_to_StarterArmor in the IK Retargeter
editor (double-click it in the Content Browser) -- it has a live preview
where you can see the armor mimicking Chaos_Armor's pose immediately. If it
looks right there, we can either drive the armor at runtime with a
"Retarget Pose From Mesh" anim node, or export baked AnimSequences for it
directly onto the armor's own skeleton.
"""

import os
import unreal

SOURCE_DIR = r"X:\IronBreach\Content\Characters\Infantry\SourceArt\StarterArmor"
SOURCE_FILENAME = "SK_StarterArmor_v8.fbx"

DEST_PATH = "/Game/Characters/Infantry/Meshes/StarterArmor"
MESH_ASSET_NAME = "SK_StarterArmor"

CHAOS_SKELETON_PATH = "/Game/Characters/Infantry/Meshes/Chaos_Armor/Chaos_Armor_Skeleton.Chaos_Armor_Skeleton"
CHAOS_MESH_PATH = "/Game/Characters/Infantry/Meshes/Chaos_Armor/Chaos_Armor.Chaos_Armor"

IKRIG_DIR = "/Game/Characters/Infantry/Animations/Retargeting"
IKRIG_SOURCE_NAME = "IK_ChaosArmor"
IKRIG_TARGET_NAME = "IK_StarterArmor"
RETARGETER_NAME = "RTG_ChaosArmor_to_StarterArmor"

asset_tools = unreal.AssetToolsHelpers.get_asset_tools()

# Chain definitions shared by both rigs -- (chain_name, start_bone, end_bone)
CHAINS = [
    ("Spine", "Spine", "Spine2"),
    ("Neck", "Neck", "Neck"),
    ("Head", "Head", "HeadTop_End"),
    ("LeftArm", "LeftShoulder", "LeftHand"),
    ("RightArm", "RightShoulder", "RightHand"),
    ("LeftLeg", "LeftUpLeg", "LeftFoot"),
    ("RightLeg", "RightUpLeg", "RightFoot"),
]
RETARGET_ROOT = "Hips"


def safe(fn, label):
    try:
        return fn()
    except Exception as e:  # noqa: BLE001
        unreal.log_error(f"[IKRetarget] FAILED at '{label}': {e}")
        return None


def import_armor_own_skeleton():
    src = os.path.join(SOURCE_DIR, SOURCE_FILENAME)
    if not os.path.exists(src):
        unreal.log_error(f"[IKRetarget] Missing source file: {src}")
        return None

    task = unreal.AssetImportTask()
    task.set_editor_property("filename", src)
    task.set_editor_property("destination_path", DEST_PATH)
    task.set_editor_property("destination_name", MESH_ASSET_NAME)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("automated", True)
    task.set_editor_property("save", True)

    options = unreal.FbxImportUI()
    options.set_editor_property("import_mesh", True)
    options.set_editor_property("import_as_skeletal", True)
    options.set_editor_property("import_materials", True)
    options.set_editor_property("import_textures", True)
    options.set_editor_property("import_animations", False)
    options.set_editor_property("create_physics_asset", False)
    # Deliberately NOT setting skeleton -- own independent skeleton this time.
    try:
        options.skeletal_mesh_import_data.set_editor_property("import_morph_targets", False)
    except Exception:
        pass
    task.set_editor_property("options", options)

    asset_tools.import_asset_tasks([task])
    mesh = unreal.EditorAssetLibrary.load_asset(f"{DEST_PATH}/{MESH_ASSET_NAME}.{MESH_ASSET_NAME}")
    if mesh is None:
        unreal.log_error("[IKRetarget] Armor import failed -- check Output Log above.")
        return None
    unreal.log(f"[IKRetarget] Imported {MESH_ASSET_NAME} onto its own new skeleton.")
    return mesh


def build_ik_rig(rig_name, skeletal_mesh):
    package_path = f"{IKRIG_DIR}/{rig_name}"
    existing = unreal.EditorAssetLibrary.load_asset(f"{package_path}.{rig_name}")
    if existing is not None:
        unreal.log(f"[IKRetarget] {rig_name} already exists, reusing it.")
        ik_rig = existing
    else:
        factory = unreal.IKRigDefinitionFactory()
        ik_rig = asset_tools.create_asset(rig_name, IKRIG_DIR, unreal.IKRigDefinition, factory)
        if ik_rig is None:
            unreal.log_error(f"[IKRetarget] Could not create IK Rig asset {rig_name}")
            return None

    controller = unreal.IKRigController.get_controller(ik_rig)
    if controller is None:
        unreal.log_error(f"[IKRetarget] Could not get IKRigController for {rig_name}")
        return None

    safe(lambda: controller.set_skeletal_mesh(skeletal_mesh), f"{rig_name}: set_skeletal_mesh")
    safe(lambda: controller.set_retarget_root(RETARGET_ROOT), f"{rig_name}: set_retarget_root")

    # Clear any existing chains first so re-running this script is idempotent
    # instead of erroring out on duplicates.
    for chain_info in list(controller.get_retarget_chains()):
        try:
            controller.remove_retarget_chain(chain_info.get_editor_property("chain_name"))
        except Exception as e:  # noqa: BLE001
            unreal.log_warning(f"[IKRetarget] {rig_name}: could not remove old chain: {e}")

    for chain_name, start_bone, end_bone in CHAINS:
        def add_chain(c=chain_name, s=start_bone, e=end_bone):
            controller.add_retarget_chain(
                unreal.Name(c), unreal.Name(s), unreal.Name(e), unreal.Name("")
            )
        safe(add_chain, f"{rig_name}: add_retarget_chain({chain_name})")

    unreal.EditorAssetLibrary.save_loaded_asset(ik_rig)
    unreal.log(f"[IKRetarget] Built/updated {rig_name} with {len(CHAINS)} chains + root '{RETARGET_ROOT}'.")
    return ik_rig


def build_retargeter(source_rig, target_rig):
    existing = unreal.EditorAssetLibrary.load_asset(f"{IKRIG_DIR}/{RETARGETER_NAME}.{RETARGETER_NAME}")
    if existing is not None:
        unreal.log(f"[IKRetarget] {RETARGETER_NAME} already exists, reusing it.")
        retargeter = existing
    else:
        factory = unreal.IKRetargetFactory()
        retargeter = asset_tools.create_asset(RETARGETER_NAME, IKRIG_DIR, unreal.IKRetargeter, factory)
        if retargeter is None:
            unreal.log_error(f"[IKRetarget] Could not create IK Retargeter asset {RETARGETER_NAME}")
            return None

    controller = unreal.IKRetargeterController.get_controller(retargeter)
    if controller is None:
        unreal.log_error("[IKRetarget] Could not get IKRetargeterController")
        return None

    safe(lambda: controller.set_ik_rig(unreal.RetargetSourceOrTarget.SOURCE, source_rig), "retargeter: set source IK rig")
    safe(lambda: controller.set_ik_rig(unreal.RetargetSourceOrTarget.TARGET, target_rig), "retargeter: set target IK rig")

    unreal.EditorAssetLibrary.save_loaded_asset(retargeter)
    unreal.log(f"[IKRetarget] Built/updated {RETARGETER_NAME}.")
    return retargeter


def run():
    armor_mesh = safe(import_armor_own_skeleton, "import armor mesh")
    if armor_mesh is None:
        return
    armor_skeleton = armor_mesh.get_editor_property("skeleton")
    if armor_skeleton is None:
        unreal.log_error("[IKRetarget] Armor mesh has no skeleton assigned -- aborting.")
        return

    chaos_skeleton = unreal.EditorAssetLibrary.load_asset(CHAOS_SKELETON_PATH)
    chaos_mesh = unreal.EditorAssetLibrary.load_asset(CHAOS_MESH_PATH)
    if chaos_skeleton is None or chaos_mesh is None:
        unreal.log_error("[IKRetarget] Could not load Chaos_Armor_Skeleton or its mesh -- check paths.")
        return

    source_rig = safe(lambda: build_ik_rig(IKRIG_SOURCE_NAME, chaos_mesh), "build source IK rig")
    target_rig = safe(lambda: build_ik_rig(IKRIG_TARGET_NAME, armor_mesh), "build target IK rig")
    if source_rig is None or target_rig is None:
        unreal.log_error("[IKRetarget] One or both IK Rigs failed to build -- see errors above. Stopping before retargeter.")
        return

    retargeter = safe(lambda: build_retargeter(source_rig, target_rig), "build IK retargeter")
    if retargeter is None:
        unreal.log_error("[IKRetarget] Retargeter failed to build -- see errors above.")
        return

    unreal.log("[IKRetarget] DONE. Open RTG_ChaosArmor_to_StarterArmor in the Content Browser "
               "(under Characters/Infantry/Animations/Retargeting) and double-click to preview.")


run()
