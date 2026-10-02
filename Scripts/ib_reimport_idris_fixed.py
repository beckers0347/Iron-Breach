"""
IBPY: ib_reimport_idris_fixed.py

Root cause found: /Game/Characters/NPCs/MsIdris/Ms_Idris_wSkeleton is bound
to /Game/Characters/Infantry/Meshes/JumpSuit/Base_Character_Mesh_Skeleton --
the Mixamo rig from the Jump+Suit animation import work, NOT her own
skeleton. Different bone scale entirely, which is why she renders as a
~979-meter sideways giant. Not a transform/orientation problem -- a wrong-
skeleton binding.

This imports her FRESH from the same source FBX as a brand-new asset,
deliberately NOT specifying a skeleton on the import options, so Unreal
creates a dedicated new Skeleton asset for her instead of reusing anything
existing:

    /Game/Characters/NPCs/MsIdris/Ms_Idris_Fixed            (SkeletalMesh)
    /Game/Characters/NPCs/MsIdris/Ms_Idris_Fixed_Skeleton    (auto-created)

Does NOT touch or delete Ms_Idris_wSkeleton (the broken one) -- leaving it
alone so nothing currently referencing it breaks unexpectedly. Reports the
new mesh's bounds afterward so we can confirm it's human-sized before
anything gets placed or wired up using it.

HOW TO RUN
----------
    py "X:/IronBreach/Scripts/ib_reimport_idris_fixed.py"
Paste back the full output.
"""

import os
import unreal

SOURCE_FBX = r"X:\Downloads\MsIdris_Source\Ms_Idris.fbx"
DEST_PATH = "/Game/Characters/NPCs/MsIdris"
DEST_NAME = "Ms_Idris_Fixed"


def log(msg):
    unreal.log(f"IBPY: {msg}")


def main():
    log("==== REIMPORT IDRIS (own skeleton, not the JumpSuit one) ====")

    if not os.path.isfile(SOURCE_FBX):
        log(f"ERROR: source file not found at {SOURCE_FBX} -- did the MsIdris_Source folder move?")
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
    # Deliberately NOT setting options.skeleton -- leave unset so Unreal
    # creates a brand-new Skeleton asset matched to this mesh's own rig,
    # instead of trying to bind onto an incompatible existing one.
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
    log(f"New mesh's skeleton: {skel.get_path_name() if skel else 'NONE -- something went wrong'}")

    bounds = mesh.get_bounds()
    box = bounds.box_extent
    log(f"New bounds full size (cm): x={box.x*2:.2f} y={box.y*2:.2f} z={box.z*2:.2f}")
    tallest = max(box.x, box.y, box.z) * 2
    if 140 <= tallest <= 220:
        log(f"Tallest dimension {tallest:.1f} cm -- looks human-sized. This should be good to use.")
    else:
        log(f"Tallest dimension {tallest:.1f} cm -- still NOT in human range (140-220 cm expected). "
            "Something else is going on with this source file -- don't place her yet, flag this back to me.")

    log("==== DONE ====")


main()
