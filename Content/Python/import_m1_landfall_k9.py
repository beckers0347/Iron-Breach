"""
M1 LANDFALL -- K9 skeletal mesh + Act II animation set import (custom rig)
================================================================================
IRON BREACH / Unreal Engine 5.8

WHAT THIS IS
------------
Sibling to import_m1_landfall_evacuee.py, same job, different asset shape.
Docs/M1_LANDFALL_Mission_Design_v2.md, Act II ("An Eerie Escalation"), has a
working K9 that senses the coming kaiju threat and refuses to work -- one
beat in an escalation ladder, not a companion or combat unit. The source mesh
(Downloads/Dog/Dog.fbx, Tripo3D-generated) came with no rig at all, so unlike
the evacuee (which arrived pre-rigged and pre-animated out of Tripo3D's Auto
Rig tool), this dog was rigged and animated from scratch in Blender this
session: a 28-bone quadruped armature, automatic-weight skinning, and six
hand-keyed clips.

Because of that, the export shape is different from the evacuee's single
bundled FBX: this is ONE skeletal-mesh FBX (mesh + armature, rest pose, no
baked animation) plus SIX animation-only FBX files (armature only, one clip
each), the standard multi-clip Unreal workflow -- import the mesh first to
create the Skeleton asset, then import each animation FBX targeting that same
Skeleton so they land as separate AnimSequences on it rather than as their
own unrelated skeletons.

The four Act II clips (Idle, Walk, AlertSniff, RefuseBalk -- RefuseBalk is
the key beat, the dog planting and resisting the leash) are the actual
mission requirement. Sit and Bark are bonus/reusable extras, nearly free
once the rig existed.

KNOWN ISSUE -- Dog_Sit: the hind-leg fold in this clip is still not right
(the back legs hyperextend up and back instead of folding under the body
into a proper sit) -- it imports fine as an AnimSequence like the others,
but will look broken if played. It needs manual hand-tuning of the
back_L/R_upper and back_L/R_lower pose keys in Blender's viewport before
it's usable; don't wire it up to anything until that's fixed. The other
five clips (including RefuseBalk, the one that actually matters for Act II)
looked correct in render checks this session.

HOW TO RUN IT
-------------
1. The FBX files should already be in place at:
       X:\\IronBreach\\Content\\LevelPrototyping\\AIModels_Landfall\\
   (SK_Dog.fbx, Dog_Idle.fbx, Dog_Walk.fbx, Dog_AlertSniff.fbx,
   Dog_RefuseBalk.fbx, Dog_Sit.fbx, Dog_Bark.fbx -- delivered and committed
   there directly this session.)
2. Run from the Output Log console:
       py "X:/IronBreach/Content/Python/import_m1_landfall_k9.py"
   or the Python console tab:
       exec(open("X:/IronBreach/Content/Python/import_m1_landfall_k9.py").read())
3. This creates SK_Dog, a Skeleton asset (Dog_Skeleton_Skeleton or similar,
   auto-named by the importer off the mesh), and six AnimSequences
   (A_Dog_Idle, A_Dog_Walk, A_Dog_AlertSniff, A_Dog_RefuseBalk, A_Dog_Sit,
   A_Dog_Bark) all under /Game/M1_Landfall/AIModels/. Assign the skeletal
   mesh to the K9 NPC's USkeletalMeshComponent and drive A_Dog_RefuseBalk
   off whatever triggers the Act II escalation beat.

Safe to re-run: existing assets get re-imported in place, not duplicated.
"""

import os
import unreal

SOURCE_DIR = r"X:\IronBreach\Content\LevelPrototyping\AIModels_Landfall"
DEST_PATH = "/Game/M1_Landfall/AIModels"

MESH_SOURCE_FILENAME = "SK_Dog.fbx"
MESH_ASSET_NAME = "SK_Dog"

# (source fbx filename, destination AnimSequence name)
ANIM_CLIPS = [
    ("Dog_Idle.fbx", "A_Dog_Idle"),
    ("Dog_Walk.fbx", "A_Dog_Walk"),
    ("Dog_AlertSniff.fbx", "A_Dog_AlertSniff"),
    ("Dog_RefuseBalk.fbx", "A_Dog_RefuseBalk"),
    ("Dog_Sit.fbx", "A_Dog_Sit"),  # known-broken pose, see docstring
    ("Dog_Bark.fbx", "A_Dog_Bark"),
]

asset_tools = unreal.AssetToolsHelpers.get_asset_tools()


def safe(fn, label):
    try:
        return fn()
    except Exception as e:  # noqa: BLE001
        unreal.log_warning(f"[Landfall K9] Skipped '{label}': {e}")
        return None


def import_skeletal_mesh():
    src = os.path.join(SOURCE_DIR, MESH_SOURCE_FILENAME)
    if not os.path.exists(src):
        unreal.log_error(
            f"[Landfall K9] Missing source file: {src} -- see this script's docstring "
            f"for where the FBX exports should live."
        )
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
    options.set_editor_property("import_animations", False)  # rest-pose-only FBX, no clip baked in
    options.set_editor_property("create_physics_asset", True)
    try:
        options.skeletal_mesh_import_data.set_editor_property("import_morph_targets", False)
    except Exception:
        pass
    task.set_editor_property("options", options)

    asset_tools.import_asset_tasks([task])

    mesh = unreal.EditorAssetLibrary.load_asset(f"{DEST_PATH}/{MESH_ASSET_NAME}.{MESH_ASSET_NAME}")
    if mesh is None:
        unreal.log_error("[Landfall K9] Skeletal mesh import failed -- check the Output Log above.")
    return mesh


def import_anim_clip(skeleton, source_filename, anim_asset_name):
    src = os.path.join(SOURCE_DIR, source_filename)
    if not os.path.exists(src):
        unreal.log_warning(f"[Landfall K9] Missing anim source file: {src}, skipping {anim_asset_name}.")
        return None

    task = unreal.AssetImportTask()
    task.set_editor_property("filename", src)
    task.set_editor_property("destination_path", DEST_PATH)
    task.set_editor_property("destination_name", anim_asset_name)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("automated", True)
    task.set_editor_property("save", True)

    options = unreal.FbxImportUI()
    options.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_ANIMATION)
    options.set_editor_property("import_mesh", False)
    options.set_editor_property("import_as_skeletal", True)
    options.set_editor_property("import_animations", True)
    options.set_editor_property("import_materials", False)
    options.set_editor_property("import_textures", False)
    options.set_editor_property("create_physics_asset", False)
    options.set_editor_property("skeleton", skeleton)
    task.set_editor_property("options", options)

    asset_tools.import_asset_tasks([task])

    anim = unreal.EditorAssetLibrary.load_asset(f"{DEST_PATH}/{anim_asset_name}.{anim_asset_name}")
    if anim is None:
        unreal.log_warning(f"[Landfall K9] AnimSequence import failed for {anim_asset_name} -- check the Output Log above.")
    return anim


def check_height(mesh, target_height_cm=60.0):
    """Sanity-check the imported scale against a rough working-dog withers
    height (a German Shepherd-sized K9 is roughly 55-65cm at the shoulder;
    this checks total bounding height which will read taller once ears/head
    are included, so the tolerance here is loose -- it's just a tripwire for
    a wildly wrong import scale, not a precise measurement)."""
    if mesh is None:
        return
    bounds = mesh.get_editor_property("bounds")  # BoxSphereBounds -- SkeletalMesh has no get_bounding_box()
    actual_height_cm = bounds.box_extent.z * 2.0
    if actual_height_cm <= 0.01:
        unreal.log_warning("[Landfall K9] Could not read a sane bounding height.")
        return
    ratio = target_height_cm / actual_height_cm
    if abs(ratio - 1.0) > 0.5:
        unreal.log_warning(
            f"[Landfall K9] Imported at {actual_height_cm:.0f}cm tall, expected roughly "
            f"{target_height_cm:.0f}cm for a working dog (ratio {ratio:.2f}x). Rescale on the "
            f"SkeletalMeshComponent when placing it before relying on this number for gameplay."
        )
    else:
        unreal.log(f"[Landfall K9] {actual_height_cm:.0f}cm tall, close enough to the {target_height_cm:.0f}cm target.")


def run():
    mesh = safe(import_skeletal_mesh, "import K9 skeletal mesh")
    if mesh is None:
        unreal.log(f"[Landfall K9] Import failed, 0 asset(s) built at {DEST_PATH}.")
        return
    safe(lambda m=mesh: check_height(m), "check K9 height")
    unreal.EditorAssetLibrary.save_loaded_asset(mesh)

    skeleton = mesh.get_editor_property("skeleton")
    if skeleton is None:
        unreal.log_error("[Landfall K9] Skeletal mesh has no Skeleton asset attached -- cannot import animations.")
        unreal.log(f"[Landfall K9] Imported {MESH_ASSET_NAME} only (no animations) at {DEST_PATH}.")
        return

    built = 1
    for source_filename, anim_asset_name in ANIM_CLIPS:
        anim = safe(
            lambda sf=source_filename, an=anim_asset_name: import_anim_clip(skeleton, sf, an),
            f"import {anim_asset_name}",
        )
        if anim is not None:
            unreal.EditorAssetLibrary.save_loaded_asset(anim)
            built += 1

    unreal.log(f"[Landfall K9] Built {built} asset(s) at {DEST_PATH} ({MESH_ASSET_NAME} + up to {len(ANIM_CLIPS)} anim clip(s)).")
    unreal.log("[Landfall K9] NOTE: A_Dog_Sit has a known-broken hind-leg pose, see this script's docstring -- don't wire it up yet.")


run()
