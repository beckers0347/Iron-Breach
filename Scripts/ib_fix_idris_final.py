"""
IBPY: ib_fix_idris_final.py

Two things, in order:

1. RESCALE: Ms_Idris_Fixed is correctly proportioned now (own skeleton,
   stands upright) but reads ~97.9 cm tall -- about half a typical adult,
   confirmed visually next to the player mannequin. Re-imports the SAME
   asset in place (same path, replace_existing) with import_uniform_scale
   = 1.7, which should land her around ~166 cm. If that's still off once
   you look at her, tell me the direction (bigger/smaller) and I'll adjust
   the factor -- this is a one-line change, not a redo.

2. CLEAN UP THE BROKEN GIANTS: removes every actor in the current level
   that's using the old broken /Game/Characters/NPCs/MsIdris/Ms_Idris_wSkeleton
   mesh (the Mixamo-rig-bound one that renders as a 979-meter sideways
   giant). That's your three placeholders -- NPC_Rhodes_PLACEHOLDER,
   NPC_Okafor_Bricks_PLACEHOLDER, NPC_Yun_Static_PLACEHOLDER -- plus
   anything else unexpectedly using it. This is removing placed actors
   from the level (an ordinary, undoable editor action, Ctrl+Z gets them
   back), not deleting any file.

Then RE-SPAWNS the three placeholders fresh, this time using the fixed,
correctly-scaled Ms_Idris_Fixed mesh, and re-wires them into
Act1BarracksDirector.SquadNPCs / Act2EscalationDirector.DistrictNPCs same
as before. Leaves NPC_Idris_FIXED_PREVIEW alone (it'll just look right now
that the asset itself is rescaled) and does NOT touch the
Ms_Idris_wSkeleton ASSET itself -- only removes placed actors using it.

HOW TO RUN
----------
    py "X:/IronBreach/Scripts/ib_fix_idris_final.py"
Paste back the full output, then look at her again in the viewport.
"""

import os
import unreal

SOURCE_FBX = r"X:\Downloads\MsIdris_Source\Ms_Idris.fbx"
FIXED_MESH_PATH = "/Game/Characters/NPCs/MsIdris/Ms_Idris_Fixed"
BROKEN_MESH_PATH = "/Game/Characters/NPCs/MsIdris/Ms_Idris_wSkeleton"
IMPORT_SCALE = 1.7

PLACEHOLDERS = [
    {"label": "NPC_Rhodes_PLACEHOLDER", "offset_x": 300.0},
    {"label": "NPC_Okafor_Bricks_PLACEHOLDER", "offset_x": 600.0},
    {"label": "NPC_Yun_Static_PLACEHOLDER", "offset_x": 900.0},
]

DIRECTOR_WIRING = [
    ("Act1BarracksDirector", "SquadNPCs"),
    ("Act2EscalationDirector", "DistrictNPCs"),
]


def log(msg):
    unreal.log(f"IBPY: {msg}")


def rescale_idris():
    log(f"---- Re-importing {FIXED_MESH_PATH} at uniform scale {IMPORT_SCALE} ----")
    task = unreal.AssetImportTask()
    task.filename = SOURCE_FBX
    task.destination_path = "/Game/Characters/NPCs/MsIdris"
    task.destination_name = "Ms_Idris_Fixed"
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
    # import_uniform_scale lives on the nested mesh-import-data object, not
    # directly on FbxImportUI -- that's what the previous attempt got wrong.
    options.skeletal_mesh_import_data.set_editor_property("import_uniform_scale", IMPORT_SCALE)
    task.options = options

    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])

    mesh = unreal.load_asset(FIXED_MESH_PATH)
    if mesh is None:
        log("ERROR: reimport failed, could not reload the mesh.")
        return None
    bounds = mesh.get_bounds()
    box = bounds.box_extent
    log(f"New bounds full size (cm): x={box.x*2:.2f} y={box.y*2:.2f} z={box.z*2:.2f}")
    return mesh


def remove_broken_giants():
    log(f"---- Removing placed actors using {BROKEN_MESH_PATH} ----")
    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    all_actors = actor_subsystem.get_all_level_actors()
    removed = []
    for a in all_actors:
        if not isinstance(a, unreal.SkeletalMeshActor):
            continue
        comp = a.skeletal_mesh_component
        used_mesh = comp.get_skeletal_mesh_asset() if hasattr(comp, "get_skeletal_mesh_asset") else comp.skeletal_mesh
        if used_mesh and used_mesh.get_path_name() == f"{BROKEN_MESH_PATH}.{BROKEN_MESH_PATH.split('/')[-1]}":
            removed.append(a.get_actor_label())
            actor_subsystem.destroy_actor(a)
    if removed:
        log(f"Removed {len(removed)} actor(s): {removed}")
    else:
        log("No placed actors found using the broken mesh (nothing to remove).")
    return removed


def respawn_placeholders(fixed_mesh):
    log("---- Re-spawning placeholders on the fixed mesh ----")
    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    spawned = {}
    for p in PLACEHOLDERS:
        spawn_loc = unreal.Vector(x=p["offset_x"], y=0.0, z=0.0)
        actor = actor_subsystem.spawn_actor_from_class(
            unreal.SkeletalMeshActor, spawn_loc, unreal.Rotator(roll=0.0, pitch=0.0, yaw=0.0)
        )
        if actor is None:
            log(f"ERROR: failed to spawn {p['label']}")
            continue
        actor.set_actor_label(p["label"])
        actor.skeletal_mesh_component.set_skinned_asset_and_update(fixed_mesh)
        spawned[p["label"]] = actor
        log(f"  Placed '{p['label']}' at {spawn_loc}")

    if len(spawned) < len(PLACEHOLDERS):
        log("WARNING: not all placeholders respawned -- skipping director rewiring.")
        return

    npc_list = [spawned[p["label"]] for p in PLACEHOLDERS]
    log("---- Rewiring into Act directors ----")
    all_actors = actor_subsystem.get_all_level_actors()
    for cls_name, prop_name in DIRECTOR_WIRING:
        matches = [a for a in all_actors if a.get_class().get_name() == cls_name]
        if not matches:
            log(f"  {cls_name} not found in this level -- skipped.")
            continue
        director = matches[0]
        try:
            director.set_editor_property(prop_name, npc_list)
            confirm = director.get_editor_property(prop_name)
            log(f"  {cls_name}.{prop_name} set to {len(confirm)} entr(y/ies): "
                f"{[a.get_actor_label() for a in confirm]}")
        except Exception as e:
            log(f"  ERROR setting {cls_name}.{prop_name}: {e}")


def main():
    log("==== FIX IDRIS SCALE + CLEAN UP BROKEN GIANTS ====")
    if not os.path.isfile(SOURCE_FBX):
        log(f"ERROR: source file not found at {SOURCE_FBX}")
        return

    fixed_mesh = rescale_idris()
    if fixed_mesh is None:
        log("Aborting -- rescale failed, not touching placed actors.")
        return

    remove_broken_giants()
    respawn_placeholders(fixed_mesh)

    log("==== DONE. Check NPC_Idris_FIXED_PREVIEW and the three placeholders "
        "in the viewport -- they should all be using the corrected, "
        "human-scale mesh now. Save the level once it looks right. ====")


main()
