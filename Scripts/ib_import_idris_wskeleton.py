"""
IBPY: ib_import_idris_wskeleton.py

Shane pointed out the earlier imports used the wrong source file
(Ms_Idris.fbx from the zip). The correct one is
X:\\Downloads\\Ms_Idris_wSkeleton.fbx -- the name suggests it was already
rigged to match the Infantry bone structure on purpose.

This imports it fresh, as /Game/Characters/NPCs/MsIdris/Ms_Idris_Infantry,
explicitly binding it onto the existing
/Game/Characters/Infantry/Meshes/JumpSuit/Base_Character_Mesh_Skeleton
instead of letting a new skeleton get auto-created. Does NOT touch the
earlier Ms_Idris_Fixed (correctly-scaled, own skeleton) or the broken
Ms_Idris_wSkeleton .uasset -- this is a clean new asset so nothing existing
breaks if something's still off.

After import, reports:
  - which skeleton the new mesh actually ended up on (confirms the bind
    against Base_Character_Mesh_Skeleton actually took)
  - its bounds (sanity check on scale -- should read human-sized without
    any extra scale correction needed, since this file is supposedly the
    correct export)
  - bone-name overlap against the Infantry mesh, same check as
    ib_compare_skeletons.py, so we know for certain whether she can
    actually play the Infantry animation set now

HOW TO RUN
----------
    py "X:/IronBreach/Scripts/ib_import_idris_wskeleton.py"
Paste back the full output.
"""

import os
import unreal

SOURCE_FBX = r"X:\Downloads\Ms_Idris_wSkeleton.fbx"
DEST_PATH = "/Game/Characters/NPCs/MsIdris"
DEST_NAME = "Ms_Idris_Infantry"
INFANTRY_SKELETON_PATH = "/Game/Characters/Infantry/Meshes/JumpSuit/Base_Character_Mesh_Skeleton"
INFANTRY_MESH_PATH = "/Game/Characters/Infantry/Meshes/JumpSuit/Base_Character_Mesh"


def log(msg):
    unreal.log(f"IBPY: {msg}")


def get_bone_names(mesh, label):
    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    temp_actor = actor_subsystem.spawn_actor_from_class(
        unreal.SkeletalMeshActor, unreal.Vector(x=0.0, y=0.0, z=-50000.0),
        unreal.Rotator(roll=0.0, pitch=0.0, yaw=0.0)
    )
    names = []
    try:
        temp_actor.set_actor_label(f"TEMP_BoneCheck_{label}")
        comp = temp_actor.skeletal_mesh_component
        comp.set_skinned_asset_and_update(mesh)
        num_bones = comp.get_num_bones()
        names = [str(comp.get_bone_name(i)) for i in range(num_bones)]
    except Exception as e:
        log(f"  Could not read bone names for {label}: {e}")
    finally:
        actor_subsystem.destroy_actor(temp_actor)
    return names


def main():
    log("==== IMPORT Ms_Idris_wSkeleton.fbx onto the Infantry skeleton ====")

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
    options.skeleton = infantry_skeleton  # explicit bind, not auto-create
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
    log(f"New mesh's skeleton: {skel_path}")
    if skel_path and INFANTRY_SKELETON_PATH in skel_path:
        log("  -> confirmed bound to the Infantry skeleton.")
    else:
        log("  -> WARNING: did NOT bind to the Infantry skeleton as requested -- check above for import errors.")

    bounds = mesh.get_bounds()
    box = bounds.box_extent
    tallest = max(box.x, box.y, box.z) * 2
    log(f"Bounds full size (cm): x={box.x*2:.2f} y={box.y*2:.2f} z={box.z*2:.2f}")
    if 140 <= tallest <= 220:
        log(f"Tallest dimension {tallest:.1f} cm -- human-sized, no scale correction needed.")
    else:
        log(f"Tallest dimension {tallest:.1f} cm -- NOT in expected human range (140-220 cm). Flag this back to me.")

    log("---- Bone-name overlap check vs. the Infantry mesh ----")
    infantry_mesh = unreal.load_asset(INFANTRY_MESH_PATH)
    if infantry_mesh is None:
        log(f"Could not load {INFANTRY_MESH_PATH} to compare bones.")
    else:
        infantry_bones = set(get_bone_names(infantry_mesh, "Infantry"))
        idris_bones = set(get_bone_names(mesh, "IdrisInfantry"))
        overlap = infantry_bones & idris_bones
        log(f"Infantry: {len(infantry_bones)} bones. Idris (new import): {len(idris_bones)} bones. "
            f"Overlap: {len(overlap)}.")
        if idris_bones and len(overlap) == len(idris_bones):
            log("FULL overlap -- she can use the Infantry animation set directly.")
        elif overlap:
            log("PARTIAL overlap -- some bones match, some don't; may animate acceptably for shared bones only.")
        else:
            log("ZERO overlap -- still a real mismatch, animations will not drive her correctly.")

    log("==== DONE ====")


main()
