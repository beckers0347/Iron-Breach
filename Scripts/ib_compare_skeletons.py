"""
IBPY: ib_compare_skeletons.py

Read-only. Before rebinding Ms. Idris (and every future NPC) onto
/Game/Characters/Infantry/Meshes/JumpSuit/Base_Character_Mesh_Skeleton so
they can share the Infantry animation set, I need to know whether the two
rigs actually use matching bone names. If they don't, a plain "reassign
skeleton" won't let her play those animations -- the bones just won't line
up -- and this needs an IK Retargeter instead (same issue that was flagged
earlier for the Jump+Suit Mixamo animations vs. the UE5 Mannequin).

What this does:
  1. Finds a SkeletalMesh that actually uses Base_Character_Mesh_Skeleton
     (searches the asset registry for any SkeletalMesh under
     /Game/Characters/Infantry/ whose Skeleton property points at it) and
     lists its bone names.
  2. Lists Ms_Idris_Fixed's current bone names.
  3. Reports: bone count for each, how many names match exactly, and a
     sample of names unique to each side -- so we can tell at a glance if
     this is "same rig, just reassign" or "different rig, needs retargeting."

Changes nothing.

HOW TO RUN
----------
    py "X:/IronBreach/Scripts/ib_compare_skeletons.py"
Paste back the full output.
"""

import unreal

INFANTRY_SKELETON_PATH = "/Game/Characters/Infantry/Meshes/JumpSuit/Base_Character_Mesh_Skeleton"
IDRIS_MESH_PATH = "/Game/Characters/NPCs/MsIdris/Ms_Idris_Fixed"

registry = unreal.AssetRegistryHelpers.get_asset_registry()


def log(msg):
    unreal.log(f"IBPY: {msg}")


def get_bone_names(mesh, label):
    # SkeletalMeshLibrary isn't available in this engine's Python API, so
    # read bone names the way a runtime component would: spawn a throwaway
    # SkeletalMeshActor, ask its component for each bone by index, then
    # clean it up. This is a temporary, undoable editor action, not a
    # permanent change to anything.
    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    temp_actor = actor_subsystem.spawn_actor_from_class(
        unreal.SkeletalMeshActor, unreal.Vector(x=0.0, y=0.0, z=-50000.0),  # tucked out of the way
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


def find_mesh_using_skeleton(skeleton_path):
    all_assets = registry.get_assets_by_path("/Game/Characters/Infantry", recursive=True)
    for a in all_assets:
        if str(a.asset_class_path.asset_name) != "SkeletalMesh":
            continue
        obj = a.get_asset()
        if obj is None:
            continue
        skel = obj.get_editor_property("skeleton")
        if skel and skeleton_path in skel.get_path_name():
            return obj
    return None


def main():
    log("==== COMPARE SKELETONS (Infantry vs. Idris) ====")

    infantry_mesh = find_mesh_using_skeleton(INFANTRY_SKELETON_PATH)
    if infantry_mesh is None:
        log(f"Could not find any SkeletalMesh under /Game/Characters/Infantry/ using {INFANTRY_SKELETON_PATH}.")
        log("Trying to load the Skeleton asset directly instead, just to confirm it exists.")
        skel = unreal.load_asset(INFANTRY_SKELETON_PATH)
        log(f"Skeleton asset itself: {'found' if skel else 'NOT FOUND -- check the path'}")
        return
    log(f"Found Infantry mesh using that skeleton: {infantry_mesh.get_path_name()}")

    idris_mesh = unreal.load_asset(IDRIS_MESH_PATH)
    if idris_mesh is None:
        log(f"ERROR: could not load {IDRIS_MESH_PATH}")
        return

    infantry_bones = get_bone_names(infantry_mesh, "Infantry")
    idris_bones = get_bone_names(idris_mesh, "Idris")

    log(f"Infantry rig: {len(infantry_bones)} bones. First 10: {infantry_bones[:10]}")
    log(f"Idris rig:    {len(idris_bones)} bones. First 10: {idris_bones[:10]}")

    infantry_set = set(infantry_bones)
    idris_set = set(idris_bones)
    overlap = infantry_set & idris_set
    only_infantry = sorted(infantry_set - idris_set)
    only_idris = sorted(idris_set - infantry_set)

    log(f"---- Overlap: {len(overlap)} / {len(idris_set)} of Idris's bone names also exist in the Infantry rig ----")
    if len(overlap) == 0:
        log("ZERO overlap -- completely different naming conventions. A plain skeleton "
            "reassignment will not work; this needs an IK Rig + IK Retargeter.")
    elif len(overlap) == len(idris_set):
        log("FULL overlap -- every one of Idris's bones exists under the same name in the "
            "Infantry rig. A direct skeleton reassignment + reimport should work cleanly.")
    else:
        log("PARTIAL overlap -- some bones match, some don't. Reassignment would partially "
            "work at best; likely still needs a retargeter for full animation compatibility.")

    if only_infantry:
        log(f"Bones only in Infantry rig (sample): {only_infantry[:15]}")
    if only_idris:
        log(f"Bones only in Idris rig (sample): {only_idris[:15]}")

    log("==== DONE ====")


main()
