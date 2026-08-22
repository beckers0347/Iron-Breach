"""
M1 LANDFALL -- Evacuee civilian skeletal mesh + walk animation import (Tripo3D)
================================================================================
IRON BREACH / Unreal Engine 5.8

WHAT THIS IS
------------
Sibling to import_m1_district_ai_models.py, same job, different asset shape.
Every prop on the M1_District Tripo3D shopping list (Docs/M1_DISTRICT_TRIPO3D_
PROMPTS.md) is a static mesh; the carry mechanic's civilian (Docs/
M1_LANDFALL_Mission_Design.md, AIBCarryablePawn) needs an actual rig + a walk
cycle so she reads as a person being carried rather than a stiff prop, so this
is a SKELETAL mesh import with one baked AnimSequence, not a static one.

Generated via Tripo3D's "3D Rigging & Animation" tool: Text to 3D (generic
civilian, T-pose) -> Auto Rig (v2.5 - Good for Animals model, Humanoid result)
-> searched animation presets for "walk", applied the single "walk" retarget
result -> Export panel, FBX, 3dsmax orientation preset, Export Skeleton ON.

IMPORTANT: Tripo3D's Export dialog defaults "Number of Animations" to 0 even
with a retargeted animation applied and showing a checkmark on its thumbnail --
the walk clip is NOT included in the export until you open "Choose Animations"
(click the "Number of Animations" row) and explicitly check it. Confirmed by
hand this session: unchecked, "Number of Animations" reads 0; after checking
the "walk" thumbnail it reads 1. If you re-generate this asset, don't trust an
unexamined Export dialog to have grabbed the animation -- open Choose
Animations and check.

HOW TO RUN IT
-------------
1. Move/rename the downloaded file into:
       X:\\IronBreach\\Content\\LevelPrototyping\\AIModels_Landfall\\SK_Evacuee_Male_Walk.fbx
   (create the AIModels_Landfall folder if it isn't there yet -- kept separate
   from AIModels_District since this is a skeletal asset with a very different
   import path, not a district prop.)
2. Run from the Output Log console:
       py "X:/IronBreach/Content/Python/import_m1_landfall_evacuee.py"
   or the Python console tab:
       exec(open("X:/IronBreach/Content/Python/import_m1_landfall_evacuee.py").read())
3. This creates SK_Evacuee_Male, a Skeleton asset, and an AnimSequence
   (A_Evacuee_Male_Walk) under /Game/M1_Landfall/AIModels/. Assign the
   skeletal mesh to AIBCarryablePawn's Mesh component (swap the placeholder
   UStaticMeshComponent for a USkeletalMeshComponent first -- see the
   "swap for a skeletal mesh once her model exists" comment in
   IBCarryablePawn.h) and drive the walk anim off her carried/idle state.

Safe to re-run: existing assets get re-imported in place, not duplicated.

WHY THIS IS THE ONLY LANDFALL CHARACTER ON A TRIPO3D LIST
-----------------------------------------------------------
Ms. Idris (the specific, named civilian actually being carried) and PALAWAN
are both deliberately excluded from AI generation, same reasoning as the
Caryatid frame in the M1_District import script: both recur as specific,
emotionally load-bearing individuals across the mission (Idris is "the
mission's entire emotional payload" per the design doc) rather than
background dressing, and a single Tripo3D pass is very likely to produce
something the game is stuck looking at for its first act. This evacuee is
deliberately generic background-civilian scope -- background muster-point
NPCs, not Idris herself -- which is exactly the kind of asset text-to-3D
handles well. Worth generating a couple of palette/build variants of this
same generic evacuee later if the muster point ends up needing more than one
body on screen at once (avoid a visible "clone army"), but that's a follow-up
generation pass, not a blocker on this import.
"""

import os
import unreal

SOURCE_DIR = r"X:\IronBreach\Content\LevelPrototyping\AIModels_Landfall"
DEST_PATH = "/Game/M1_Landfall/AIModels"

SOURCE_FILENAME = "SK_Evacuee_Male_Walk.fbx"
MESH_ASSET_NAME = "SK_Evacuee_Male"
ANIM_ASSET_NAME = "A_Evacuee_Male_Walk"

asset_tools = unreal.AssetToolsHelpers.get_asset_tools()


def safe(fn, label):
    try:
        return fn()
    except Exception as e:  # noqa: BLE001
        unreal.log_warning(f"[Landfall Evacuee] Skipped '{label}': {e}")
        return None


def import_skeletal_mesh_and_anim():
    src = os.path.join(SOURCE_DIR, SOURCE_FILENAME)
    if not os.path.exists(src):
        unreal.log_error(
            f"[Landfall Evacuee] Missing source file: {src} -- move/rename the "
            f"Tripo3D export into that folder first. See this script's docstring."
        )
        return None, None

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
    options.set_editor_property("import_animations", True)
    options.set_editor_property("create_physics_asset", True)
    try:
        options.skeletal_mesh_import_data.set_editor_property("import_morph_targets", False)
    except Exception:
        pass
    task.set_editor_property("options", options)

    asset_tools.import_asset_tasks([task])

    mesh = unreal.EditorAssetLibrary.load_asset(f"{DEST_PATH}/{MESH_ASSET_NAME}.{MESH_ASSET_NAME}")
    if mesh is None:
        unreal.log_error(f"[Landfall Evacuee] Skeletal mesh import failed -- check the Output Log above.")
        return None, None

    # Tripo3D's FBX bundles the walk clip inside the same file as the mesh
    # (per "Export Skeleton" + "Number of Animations: 1"), so the importer
    # drops an AnimSequence next to the mesh named after the source file
    # rather than ANIM_ASSET_NAME -- find and rename it so the rest of the
    # project's naming convention (A_ prefix) holds.
    anim = unreal.EditorAssetLibrary.load_asset(f"{DEST_PATH}/{MESH_ASSET_NAME}_{SOURCE_FILENAME.rsplit('.', 1)[0]}")
    if anim is None:
        # Fall back to scanning the destination folder for any AnimSequence
        # that isn't the mesh itself -- importer-assigned names for bundled
        # clips vary by FBX exporter.
        asset_paths = unreal.EditorAssetLibrary.list_assets(DEST_PATH, recursive=False)
        for path in asset_paths:
            candidate = unreal.EditorAssetLibrary.load_asset(path)
            if isinstance(candidate, unreal.AnimSequence):
                anim = candidate
                break

    if anim is None:
        unreal.log_warning(
            f"[Landfall Evacuee] Skeletal mesh imported, but no AnimSequence was found next to it in "
            f"{DEST_PATH} -- re-check the source FBX actually has the walk clip baked in (this session's "
            f"Tripo3D export needed 'Number of Animations' explicitly bumped from 0 to 1 in the Choose "
            f"Animations panel before exporting; a re-export skipping that step will produce a mesh-only FBX)."
        )
        return mesh, None

    if unreal.EditorAssetLibrary.does_asset_exist(f"{DEST_PATH}/{ANIM_ASSET_NAME}"):
        unreal.EditorAssetLibrary.delete_asset(f"{DEST_PATH}/{ANIM_ASSET_NAME}")
    renamed = unreal.EditorAssetLibrary.rename_asset(anim.get_path_name(), f"{DEST_PATH}/{ANIM_ASSET_NAME}")
    if not renamed:
        unreal.log_warning(f"[Landfall Evacuee] Could not rename animation to {ANIM_ASSET_NAME}; left as imported.")
    else:
        anim = unreal.EditorAssetLibrary.load_asset(f"{DEST_PATH}/{ANIM_ASSET_NAME}")

    return mesh, anim


def check_height(mesh, target_height_cm=175.0):
    """Same reasoning as the district import script's check_height -- Tripo3D
    doesn't guarantee the generated character comes out at a specific
    real-world height. An adult evacuee should read at roughly average human
    height next to AIBCharacter_Infantry; flag it if it's wildly off so it
    gets rescaled before anyone tries to carry her at the wrong proportions."""
    if mesh is None:
        return
    bounds = mesh.get_bounding_box()
    actual_height_cm = bounds.max.z - bounds.min.z
    if actual_height_cm <= 0.01:
        unreal.log_warning("[Landfall Evacuee] Could not read a sane bounding height.")
        return
    ratio = target_height_cm / actual_height_cm
    if abs(ratio - 1.0) > 0.15:
        unreal.log_warning(
            f"[Landfall Evacuee] Imported at {actual_height_cm:.0f}cm tall, expected roughly "
            f"{target_height_cm:.0f}cm for an adult human (ratio {ratio:.2f}x). Rescale in the "
            f"Skeletal Mesh Editor, or on the SkeletalMeshComponent when assigning her to "
            f"AIBCarryablePawn, before placing her next to the player capsule."
        )
    else:
        unreal.log(f"[Landfall Evacuee] {actual_height_cm:.0f}cm tall, close enough to the {target_height_cm:.0f}cm human-scale target.")


def run():
    mesh, anim = safe(import_skeletal_mesh_and_anim, "import evacuee skeletal mesh + walk anim")
    if mesh is None:
        unreal.log(f"[Landfall Evacuee] Import failed, 0 asset(s) built at {DEST_PATH}.")
        return
    safe(lambda m=mesh: check_height(m), "check evacuee height")
    unreal.EditorAssetLibrary.save_loaded_asset(mesh)
    built = 1
    if anim is not None:
        unreal.EditorAssetLibrary.save_loaded_asset(anim)
        built += 1
        unreal.log(f"[Landfall Evacuee] Imported {MESH_ASSET_NAME} + {ANIM_ASSET_NAME} at {DEST_PATH}.")
    else:
        unreal.log(f"[Landfall Evacuee] Imported {MESH_ASSET_NAME} only (no walk animation found) at {DEST_PATH} -- see warning above.")


run()
