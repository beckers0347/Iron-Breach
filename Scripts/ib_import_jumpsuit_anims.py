"""
IBPY: ib_import_jumpsuit_anims.py

Imports the organized Jump+Suit animation set (Mixamo-rig FBX files) into
the project as its own new skeleton, per your call: "Import as their own
Mixamo skeleton first." These are NOT retargeted onto SK_Mannequin by this
script -- that's a separate follow-up step (IK Rig + IK Retargeter) once
you've looked at what actually came in.

What this does:
  1. Imports X:\\Downloads\\Jump+Suit\\Source_Character\\Base_Character_Mesh.fbx
     as a new Skeletal Mesh at /Game/Characters/JumpSuit/Mesh/SK_JumpSuit_Base
     -- this auto-creates the Skeleton asset everything else imports against.
  2. Walks every subfolder under X:\\Downloads\\Jump+Suit\\Animations\\ and
     imports every .fbx in it as an animation-only import (skeleton set to
     the one from step 1, no mesh/geometry pulled in even from
     Combat_Punching_FullMeshBundle.fbx, which has a mesh baked in) into a
     matching /Game/Characters/JumpSuit/Animations/<PackName>/ folder.
  3. Logs every file: imported OK, or the specific error if not, so you can
     see exactly what needs attention rather than a silent partial import.

Doesn't touch the existing Characters/Mannequins content at all -- this is
purely additive under a new /Game/Characters/JumpSuit/ folder.

HOW TO RUN:
  py "X:/IronBreach/Scripts/ib_import_jumpsuit_anims.py"
Paste back the full output.
"""

import os
import unreal

SOURCE_MESH_FBX = r"X:\Downloads\Jump+Suit\Source_Character\Base_Character_Mesh.fbx"
SOURCE_ANIM_ROOT = r"X:\Downloads\Jump+Suit\Animations"

MESH_DEST_PATH = "/Game/Characters/JumpSuit/Mesh"
MESH_DEST_NAME = "SK_JumpSuit_Base"
ANIM_DEST_ROOT = "/Game/Characters/JumpSuit/Animations"


def log(msg):
    unreal.log(f"IBPY: {msg}")


def import_skeletal_mesh():
    log(f"---- Importing base skeletal mesh from {SOURCE_MESH_FBX} ----")
    if not os.path.isfile(SOURCE_MESH_FBX):
        log(f"ERROR: source mesh file not found at {SOURCE_MESH_FBX}")
        return None

    task = unreal.AssetImportTask()
    task.filename = SOURCE_MESH_FBX
    task.destination_path = MESH_DEST_PATH
    task.destination_name = MESH_DEST_NAME
    task.automated = True
    task.save = True
    task.replace_existing = True

    options = unreal.FbxImportUI()
    options.import_mesh = True
    options.import_as_skeletal = True
    options.import_animations = False
    options.import_materials = True
    options.import_textures = True
    task.options = options

    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])

    imported = list(task.get_editor_property("imported_object_paths"))
    if not imported:
        log("ERROR: skeletal mesh import produced no assets -- check the log above for FBX import errors.")
        return None
    for p in imported:
        log(f"  Imported: {p}")

    skeleton_path = f"{MESH_DEST_PATH}/{MESH_DEST_NAME}_Skeleton"
    if unreal.EditorAssetLibrary.does_asset_exist(skeleton_path):
        skeleton = unreal.load_asset(skeleton_path)
        log(f"  Skeleton asset ready: {skeleton_path}")
        return skeleton

    # Fallback: sometimes the skeleton gets a slightly different auto name --
    # search the imported paths for anything of class Skeleton.
    for p in imported:
        asset = unreal.load_asset(p)
        if isinstance(asset, unreal.Skeleton):
            log(f"  Skeleton asset ready (fallback lookup): {p}")
            return asset

    log("ERROR: could not locate the Skeleton asset after import.")
    return None


def import_animations(skeleton):
    log(f"---- Importing animations from {SOURCE_ANIM_ROOT} ----")
    if not os.path.isdir(SOURCE_ANIM_ROOT):
        log(f"ERROR: animations root not found at {SOURCE_ANIM_ROOT}")
        return

    total_ok = 0
    total_fail = 0

    for pack_name in sorted(os.listdir(SOURCE_ANIM_ROOT)):
        pack_dir = os.path.join(SOURCE_ANIM_ROOT, pack_name)
        if not os.path.isdir(pack_dir):
            continue
        dest_path = f"{ANIM_DEST_ROOT}/{pack_name}"
        fbx_files = sorted(f for f in os.listdir(pack_dir) if f.lower().endswith(".fbx"))
        log(f"  [{pack_name}] {len(fbx_files)} file(s) -> {dest_path}")

        for fname in fbx_files:
            full_path = os.path.join(pack_dir, fname)
            dest_name = os.path.splitext(fname)[0]

            task = unreal.AssetImportTask()
            task.filename = full_path
            task.destination_path = dest_path
            task.destination_name = dest_name
            task.automated = True
            task.save = True
            task.replace_existing = True

            options = unreal.FbxImportUI()
            options.skeleton = skeleton
            options.import_mesh = False
            options.import_as_skeletal = False
            options.import_animations = True
            options.import_materials = False
            options.import_textures = False
            task.options = options

            try:
                unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
                imported = list(task.get_editor_property("imported_object_paths"))
                if imported:
                    log(f"    OK   {fname} -> {imported[0]}")
                    total_ok += 1
                else:
                    log(f"    FAIL {fname} -- no asset produced (see FBX import errors above)")
                    total_fail += 1
            except Exception as e:
                log(f"    FAIL {fname} -- exception: {e}")
                total_fail += 1

    log(f"---- Done. {total_ok} animation(s) imported OK, {total_fail} failed. ----")


def main():
    skeleton = import_skeletal_mesh()
    if not skeleton:
        log("Aborting animation import -- no skeleton to import against.")
        return
    import_animations(skeleton)
    log("All done. Everything is under /Game/Characters/JumpSuit/. "
        "Existing Characters/Mannequins content was not touched. "
        "Next step (not done by this script) would be setting up an IK Rig + "
        "IK Retargeter if you want these retargeted onto SK_Mannequin.")


main()
