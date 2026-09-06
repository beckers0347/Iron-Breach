"""
Export the Chaos_Armor SkeletalMesh (the one already using Chaos_Armor_Skeleton)
back out to FBX, so its exact bone hierarchy can be inspected directly rather
than guessed at from a screenshot or a Python bone-listing API that may not
be available in this project (unreal.SkeletalMeshLibrary isn't registered
here -- likely the Editor Scripting Utilities plugin isn't enabled).

HOW TO RUN IT
-------------
    py "X:/IronBreach/Content/Python/dump_chaos_skeleton.py"

Writes X:\\Downloads\\Chaos_Armor_SkeletonDump.fbx. Nothing needs pasting
back from the Output Log this time -- just run it and let me know it
finished (or paste any error).
"""

import unreal

MESH_PATH = "/Game/Characters/Infantry/Meshes/Chaos_Armor/Chaos_Armor.Chaos_Armor"
OUT_PATH = r"X:\Downloads\Chaos_Armor_SkeletonDump.fbx"

mesh = unreal.EditorAssetLibrary.load_asset(MESH_PATH)
if mesh is None:
    unreal.log_error(f"[DumpSkeleton] Could not load {MESH_PATH}")
else:
    task = unreal.AssetExportTask()
    task.set_editor_property("object", mesh)
    task.set_editor_property("filename", OUT_PATH)
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_identical", True)
    task.set_editor_property("prompt", False)
    task.set_editor_property("selected", False)

    exporter = None
    for class_name in ("SkeletalMeshExporterFBX", "AnimSequenceExporterFBX"):
        cls = getattr(unreal, class_name, None)
        if cls is not None:
            exporter = cls()
            unreal.log(f"[DumpSkeleton] Using exporter class: {class_name}")
            break

    if exporter is None:
        unreal.log_error("[DumpSkeleton] No FBX exporter class found (tried SkeletalMeshExporterFBX). Can't export via this route.")
    else:
        task.set_editor_property("exporter", exporter)
        success = unreal.Exporter.run_asset_export_task(task)
        unreal.log(f"[DumpSkeleton] export success={success} -> {OUT_PATH}")
