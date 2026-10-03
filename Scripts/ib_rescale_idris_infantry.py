"""
IBPY: ib_rescale_idris_infantry.py

Root cause of "not correctly scaled": Ms_Idris_Infantry's bounds are still
x=47.2 y=97.9 z=18.9 (before the roll=-90 fix rotated that onto the right
axes) -- the actual size was never corrected. Ms_Idris_Fixed got a 1.7x
import_uniform_scale factor earlier to fix this same ~half-height problem;
Ms_Idris_Infantry (re-imported from the wSkeleton.fbx source, explicitly
bound to the Infantry skeleton) never got that applied.

This re-imports Ms_Idris_Infantry in place (same path, replace_existing)
with import_uniform_scale = 1.7, keeping the explicit bind to
Base_Character_Mesh_Skeleton. Reports the new bounds afterward.

Since this is a mesh-level fix, the placed actors (NPC_Idris and the three
placeholders, all sharing this one mesh asset) should update automatically
-- no need to re-touch their transforms. Position (Z=384) and rotation
(roll=-90) from the last fix are untouched by this.

HOW TO RUN
----------
    py "X:/IronBreach/Scripts/ib_rescale_idris_infantry.py"
Paste back the full output, then look at them in the viewport again.
"""

import os
import unreal

SOURCE_FBX = "X:/Downloads/NPCs/MsIdris_Source/Ms_Idris_wSkeleton.fbx"
DEST_PATH = "/Game/Characters/NPCs/MsIdris"
DEST_NAME = "Ms_Idris_Infantry"
INFANTRY_SKELETON_PATH = "/Game/Characters/Infantry/Meshes/JumpSuit/Base_Character_Mesh_Skeleton"
IMPORT_SCALE = 1.7


def log(msg):
    unreal.log(f"IBPY: {msg}")


def main():
    log("==== RESCALE Ms_Idris_Infantry (import_uniform_scale=1.7) ====")

    if not os.path.isfile(SOURCE_FBX):
        log(f"ERROR: source file not found at {SOURCE_FBX}")
        return

    infantry_skeleton = unreal.load_asset(INFANTRY_SKELETON_PATH)
    if infantry_skeleton is None:
        log(f"ERROR: could not load {INFANTRY_SKELETON_PATH}")
        return

    task = unreal.AssetImportTask()
    task.filename = SOURCE_FBX
    task.destination_path = DEST_PATH
    task.destination_name = DEST_NAME
    task.automated = True
    task.save = True
    task.replace_existing = True

    options = unreal.FbxImportUI()
    options.import_mesh = True
    options.import_as_skeletal = True
    options.import_animations = False
    options.import_materials = True
    options.import_textures = True
    options.create_physics_asset = False
    options.skeleton = infantry_skeleton
    options.skeletal_mesh_import_data.set_editor_property("import_uniform_scale", IMPORT_SCALE)
    # the Tripo/Mixamo source is Y-up: bake the 90-degree turn into the mesh so it is Z-up like the Infantry skeleton
    options.skeletal_mesh_import_data.set_editor_property("import_rotation", unreal.Rotator(roll=-90, pitch=0, yaw=0))
    task.options = options

    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])

    imported = list(task.get_editor_property("imported_object_paths"))
    if not imported:
        log("ERROR: import produced no assets -- check the log above for FBX errors.")
        return
    for p in imported:
        log(f"  Imported: {p}")

    mesh_path = f"{DEST_PATH}/{DEST_NAME}"
    mesh = unreal.load_asset(mesh_path)
    if mesh is None:
        log(f"ERROR: could not load {mesh_path} after import.")
        return

    skel = mesh.get_editor_property("skeleton")
    skel_path = skel.get_path_name() if skel else None
    log(f"Skeleton after reimport: {skel_path}")
    if not (skel_path and INFANTRY_SKELETON_PATH in skel_path):
        log("  WARNING: lost the Infantry skeleton binding on this reimport -- check above for errors.")

    bounds = mesh.get_bounds()
    box = bounds.box_extent
    log(f"New bounds full size (cm): x={box.x*2:.2f} y={box.y*2:.2f} z={box.z*2:.2f}")
    log("(Remember: roll=-90 means her true 'up' axis is Y, not Z here -- check the Y value "
        "for her actual standing height, not Z.)")
    tallest_relevant = box.y * 2  # the axis that's actually "up" given the roll=-90 fix
    if 140 <= tallest_relevant <= 220:
        log(f"Y-axis dimension {tallest_relevant:.1f} cm -- human-sized, this should look right now.")
    else:
        log(f"Y-axis dimension {tallest_relevant:.1f} cm -- still NOT in expected human range. Flag it back.")

    log("==== DONE ====")


main()
