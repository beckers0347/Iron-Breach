"""
Import the 3 new Ms. Idris animation clips (Idle / Walk / Alert) as
AnimSequences onto her EXISTING Skeleton asset -- does not touch her mesh
or her original single animation.

HOW TO RUN
----------
    py "X:/IronBreach/Content/Python/import_idris_anims.py"
"""

import os
import unreal

SOURCE_DIR = r"X:\IronBreach\Content\Characters\NPCs\MsIdris\SourceArt"
DEST_PATH = "/Game/Characters/NPCs/MsIdris/Animations"
SKELETON_PATH = "/Game/Characters/NPCs/MsIdris/Ms_Idris_Skeleton.Ms_Idris_Skeleton"

CLIPS = [
    ("SK_Idris_Idle.fbx", "A_Idris_Idle"),
    ("SK_Idris_Walk.fbx", "A_Idris_Walk"),
    ("SK_Idris_Alert.fbx", "A_Idris_Alert"),
]

asset_tools = unreal.AssetToolsHelpers.get_asset_tools()


def safe(fn, label):
    try:
        return fn()
    except Exception as e:  # noqa: BLE001
        unreal.log_error(f"[IdrisAnims] FAILED at '{label}': {e}")
        return None


def find_skeleton():
    skel = unreal.EditorAssetLibrary.load_asset(SKELETON_PATH)
    if skel is not None:
        return skel
    # Fall back to scanning the mesh's own Skeleton reference in case the
    # asset name doesn't match the guess above.
    mesh = unreal.EditorAssetLibrary.load_asset("/Game/Characters/NPCs/MsIdris/Ms_Idris.Ms_Idris")
    if mesh is not None:
        skel = mesh.get_editor_property("skeleton")
        if skel is not None:
            unreal.log(f"[IdrisAnims] Resolved skeleton via mesh reference: {skel.get_path_name()}")
            return skel
    return None


def import_clip(filename, asset_name, skeleton):
    src = os.path.join(SOURCE_DIR, filename)
    if not os.path.exists(src):
        unreal.log_error(f"[IdrisAnims] Missing source file: {src}")
        return None

    task = unreal.AssetImportTask()
    task.set_editor_property("filename", src)
    task.set_editor_property("destination_path", DEST_PATH)
    task.set_editor_property("destination_name", asset_name)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("automated", True)
    task.set_editor_property("save", True)

    options = unreal.FbxImportUI()
    options.set_editor_property("import_mesh", False)
    options.set_editor_property("import_as_skeletal", True)
    options.set_editor_property("import_animations", True)
    options.set_editor_property("import_materials", False)
    options.set_editor_property("import_textures", False)
    options.set_editor_property("create_physics_asset", False)
    options.set_editor_property("skeleton", skeleton)

    task.set_editor_property("options", options)
    asset_tools.import_asset_tasks([task])

    anim = unreal.EditorAssetLibrary.load_asset(f"{DEST_PATH}/{asset_name}.{asset_name}")
    if anim is None:
        unreal.log_error(f"[IdrisAnims] Import of {asset_name} failed -- check Output Log above.")
    else:
        unreal.log(f"[IdrisAnims] Imported {asset_name}.")
    return anim


def run():
    skeleton = safe(find_skeleton, "resolve Ms_Idris skeleton")
    if skeleton is None:
        unreal.log_error("[IdrisAnims] Could not resolve Ms_Idris's Skeleton asset -- "
                          "open Ms_Idris_Anim in the editor, check its Skeleton in the "
                          "Asset Details panel, and tell me the exact path if it's not "
                          "at /Game/Characters/NPCs/MsIdris/Ms_Idris_Skeleton.")
        return

    for filename, asset_name in CLIPS:
        safe(lambda f=filename, a=asset_name: import_clip(f, a, skeleton), f"import {asset_name}")

    unreal.log("[IdrisAnims] DONE. Check /Game/Characters/NPCs/MsIdris/Animations for "
               "A_Idris_Idle / A_Idris_Walk / A_Idris_Alert.")


run()
