"""
Starter Armor -- skeletal mesh import, direct-assign onto Chaos_Armor_Skeleton
================================================================================
IRON BREACH / Unreal Engine 5.8

WHY THIS VERSION IS DIFFERENT (again)
--------------------------------------
Two earlier attempts at this:
1. Force-assigning the shared skeleton at import time -- failed because
   Blender's FBX exporter always emits the Armature object itself as an
   extra node, which Unreal promotes into a real bone using the object's
   name. Since that object was named "Chaos_Armor_Skeleton" (same as the
   shared skeleton asset), Interchange auto-renamed it to
   "Chaos_Armor_Skeleton1" to avoid a collision -- which then made the mesh
   genuinely incompatible.
2. Importing onto its own independent skeleton, then using Unreal's
   "Assign Skeleton" merge tool as a second step -- even after getting a
   PERFECT bone-for-bone match confirmed via an exact automated diff (every
   single bone name and parent matching), the merge still failed generically
   with "Failed to merge bones to Skeleton", with no further detail logged.

This version fixes the actual root cause of #1: the FBX is now exported with
Blender's `armature_nodetype='ROOT'` option, which tells the FBX file to mark
the armature's own node as a root pivot rather than a deforming bone -- and
confirmed via a fresh Skeleton Tree screenshot that this eliminates the extra
promoted bone entirely (Hips is now the true top-level bone, matching the
real Chaos_Armor_Skeleton exactly, with nothing above it). With that
collision gone, going back to direct force-assignment at import time (like
attempt #1) should no longer collide, and altogether avoids the flaky
"Assign Skeleton" merge dialog from attempt #2.

HOW TO RUN IT
-------------
1. Confirm the FBX is at:
       X:\\IronBreach\\Content\\Characters\\Infantry\\SourceArt\\StarterArmor\\SK_StarterArmor_v3.fbx
2. Run from the Output Log console:
       py "X:/IronBreach/Content/Python/import_starter_armor.py"
   This creates SK_StarterArmor_Test4 at /Game/Characters/Infantry/Meshes/StarterArmor,
   bound DIRECTLY to the existing Chaos_Armor_Skeleton in one step.
3. Check the Output Log: it should say "Confirmed bound directly to shared
   skeleton" with no incompatible-skeleton AssetLog error at all this time.
4. Open SK_StarterArmor_Test4 and preview an existing InfantryTripo3D
   animation to confirm it deforms correctly.

KNOWN LIMITATION -- READ BEFORE TESTING ANIMATIONS ON THIS
-------------------------------------------------------------
The source mesh's own pose has the arms resting down against the hips/belt
(a presentation render pose, not a clean T/A bind pose) -- confirmed via
render. Chaos_Armor_Skeleton's own rigging pipeline (Tripo3D Auto-Rig, same
tool used for the Landfall evacuee) normally expects a T-pose. I attempted to
reshape this mesh into a T-pose bind (rotating the arms up to horizontal and
baking that as the new rest pose) so it would visually match, but the source
mesh has multiple places where body parts are only millimeters apart or
touching in its native pose -- the fist resting against the hip/holster, and
the shoulder pauldron against the collar -- and automatic weight computation
could not cleanly separate "arm" from "torso" influence at those contact
points. Every attempt produced visible tearing/stretching once the arms
moved, so rather than ship a mesh with that damage permanently baked into
its geometry, this import uses the mesh in its ORIGINAL native standing pose
(verified clean at rest).

Practical effect: because this mesh's own bind pose differs from whatever
pose Chaos_Armor_Skeleton was actually authored in, playing the shared
animations on this armor may show the arms sitting slightly differently than
on Chaos_Armor itself, and there may be some residual weight bleed right at
the underarm/hip and shoulder-pad/collar seams if an animation swings the
arms a lot (a rifle-raise or wide arm swing is the most likely place to see
it -- check those first). If it shows up, the fix is either: (a) manual
weight paint touch-up on those two seams in Blender, or (b) regenerating
Starting_Armor through Tripo3D's own Auto-Rig tool in a proper T-pose like
Chaos_Armor was, which sidesteps the whole problem at the source.

Safe to re-run: existing asset gets re-imported in place, not duplicated.
"""

import os
import unreal

SOURCE_DIR = r"X:\IronBreach\Content\Characters\Infantry\SourceArt\StarterArmor"
SOURCE_FILENAME = "SK_StarterArmor_v3.fbx"

DEST_PATH = "/Game/Characters/Infantry/Meshes/StarterArmor"
MESH_ASSET_NAME = "SK_StarterArmor_Test4"

EXISTING_SKELETON_PATH = "/Game/Characters/Infantry/Meshes/Chaos_Armor/Chaos_Armor_Skeleton.Chaos_Armor_Skeleton"

asset_tools = unreal.AssetToolsHelpers.get_asset_tools()


def safe(fn, label):
    try:
        return fn()
    except Exception as e:  # noqa: BLE001
        unreal.log_warning(f"[StarterArmor] Skipped '{label}': {e}")
        return None


def import_skeletal_mesh():
    src = os.path.join(SOURCE_DIR, SOURCE_FILENAME)
    if not os.path.exists(src):
        unreal.log_error(f"[StarterArmor] Missing source file: {src}")
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
    # Back to force-assigning the shared skeleton directly at import time.
    # The earlier "Chaos_Armor_Skeleton1" collision was caused by Blender
    # exporting the armature object itself as an extra promoted bone with
    # the same name -- that's now suppressed via armature_nodetype='ROOT'
    # at export, so this direct assignment should no longer collide.
    skeleton = unreal.EditorAssetLibrary.load_asset(EXISTING_SKELETON_PATH)
    if skeleton is not None:
        options.set_editor_property("skeleton", skeleton)
    try:
        options.skeletal_mesh_import_data.set_editor_property("import_morph_targets", False)
    except Exception:
        pass
    task.set_editor_property("options", options)

    asset_tools.import_asset_tasks([task])

    mesh = unreal.EditorAssetLibrary.load_asset(f"{DEST_PATH}/{MESH_ASSET_NAME}.{MESH_ASSET_NAME}")
    if mesh is None:
        unreal.log_error("[StarterArmor] Skeletal mesh import failed -- check the Output Log above.")
        return None

    mesh_skeleton = mesh.get_editor_property("skeleton")
    if mesh_skeleton and mesh_skeleton.get_path_name() == skeleton.get_path_name():
        unreal.log(f"[StarterArmor] Confirmed bound directly to shared skeleton: {EXISTING_SKELETON_PATH}")
    else:
        unreal.log_warning("[StarterArmor] Imported, but skeleton assignment doesn't look right -- check in the mesh editor.")
    return mesh


def check_height(mesh, target_height_cm=180.0):
    if mesh is None:
        return
    bounds = mesh.get_editor_property("bounds")  # BoxSphereBounds -- SkeletalMesh has no get_bounding_box()
    actual_height_cm = bounds.box_extent.z * 2.0
    if actual_height_cm <= 0.01:
        unreal.log_warning("[StarterArmor] Could not read a sane bounding height.")
        return
    ratio = target_height_cm / actual_height_cm
    if abs(ratio - 1.0) > 0.15:
        unreal.log_warning(
            f"[StarterArmor] Imported at {actual_height_cm:.0f}cm tall, expected roughly "
            f"{target_height_cm:.0f}cm for an armored adult male (ratio {ratio:.2f}x)."
        )
    else:
        unreal.log(f"[StarterArmor] {actual_height_cm:.0f}cm tall, close enough to the {target_height_cm:.0f}cm target.")


def run():
    mesh = safe(import_skeletal_mesh, "import starter armor skeletal mesh onto its own skeleton")
    if mesh is None:
        unreal.log(f"[StarterArmor] Import failed, 0 asset(s) built at {DEST_PATH}.")
        return
    safe(lambda m=mesh: check_height(m), "check starter armor height")
    unreal.EditorAssetLibrary.save_loaded_asset(mesh)
    unreal.log(f"[StarterArmor] Imported {MESH_ASSET_NAME} at {DEST_PATH}. "
               f"NEXT: right-click it in the Content Browser -> Skeleton -> Assign Skeleton -> "
               f"pick Chaos_Armor_Skeleton.")


run()
