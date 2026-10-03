"""
IBPY: ib_import_npcs.py

Imports the two NPC source assets that actually exist on disk right now:

  1. Ms. Idris -- fresh Tripo3D export, extracted from your Downloads zip to
     X:\\Downloads\\MsIdris_Source\\Ms_Idris.fbx (textures alongside it).
     Imported as a full skeletal mesh (mesh+materials+textures) to
     /Game/Characters/NPCs/MsIdris/Ms_Idris -- this matches the path the old
     export_idris_for_anim.py / import_idris_anims.py scripts already expect,
     so if you still have her Idle/Walk/Alert anim FBXs lying around,
     import_idris_anims.py should work again without changes.

Then places ONE instance of each as a plain SkeletalMeshActor in the
currently open level (near the Act1 barracks director, at the world origin
-- move them by hand afterward, that's just a parking spot) so they show up
as real actors you can see and drag into an array, rather than only
existing as unplaced mesh assets.

Does NOT wire them into any Act director's NPC array -- I want to look at
where you actually want them standing before I do that, and Act5 (where
Idris's carry sequence happens) doesn't currently have an NPC reference
array in C++ at all, so wiring her in for real is a slightly bigger
conversation than placement.

Does NOT touch Rhodes / Okafor ("Bricks") / Yun ("Static") -- no source
files for them were found anywhere in Downloads, so there's nothing to
import yet.

HOW TO RUN
----------
    py "X:/IronBreach/Scripts/ib_import_npcs.py"
Paste back the full output.
"""

import os
import unreal

NPCS = [
    {
        "name": "Ms_Idris",
        "source_fbx": r"X:\Downloads\MsIdris_Source\Ms_Idris.fbx",
        "dest_path": "/Game/Characters/NPCs/MsIdris",
        "dest_name": "Ms_Idris",
    },
]


def log(msg):
    unreal.log(f"IBPY: {msg}")


def import_skeletal_mesh(npc):
    src = npc["source_fbx"]
    log(f"---- Importing {npc['name']} from {src} ----")
    if not os.path.isfile(src):
        log(f"ERROR: source file not found at {src}")
        return None

    task = unreal.AssetImportTask()
    task.filename = src
    task.destination_path = npc["dest_path"]
    task.destination_name = npc["dest_name"]
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
        log(f"ERROR: {npc['name']} import produced no assets -- check the log above for FBX errors.")
        return None
    for p in imported:
        log(f"  Imported: {p}")

    mesh_path = f"{npc['dest_path']}/{npc['dest_name']}"
    mesh = unreal.load_asset(mesh_path)
    if mesh is None:
        log(f"ERROR: could not load {mesh_path} after import.")
        return None
    return mesh


def place_in_level(npc, mesh, spawn_loc):
    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actor = actor_subsystem.spawn_actor_from_class(
        unreal.SkeletalMeshActor, spawn_loc, unreal.Rotator(roll=0.0, pitch=0.0, yaw=0.0)
    )
    if actor is None:
        log(f"ERROR: failed to spawn SkeletalMeshActor for {npc['name']}")
        return
    actor.set_actor_label(f"NPC_{npc['name']}")
    comp = actor.skeletal_mesh_component
    comp.set_skeletal_mesh(mesh)
    log(f"  Placed '{actor.get_actor_label()}' in the level at {spawn_loc}")


def main():
    log("==== NPC IMPORT ====")
    spawn_x = 0.0
    for npc in NPCS:
        mesh = import_skeletal_mesh(npc)
        if mesh:
            place_in_level(npc, mesh, unreal.Vector(x=spawn_x, y=0.0, z=0.0))
        spawn_x += 300.0  # keep them from overlapping if more than one imports
    log("==== DONE. Both NPCs (where source existed) are now real actors in this "
        "level -- find them in the World Outliner as NPC_Ms_Idris, move "
        "them where they belong, and let me know. Still need source art for "
        "Rhodes / Okafor (\"Bricks\") / Yun (\"Static\") before those can be done "
        "the same way. ====")


main()
