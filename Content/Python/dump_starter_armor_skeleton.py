"""
Export SK_StarterArmor itself (whatever Unreal actually created from the
import, even though it errored) back out to FBX, so I can see EXACTLY what
Interchange parsed as its bone hierarchy -- rather than assuming it matches
the source FBX I built. This checks whether the newer Interchange import
pipeline mangled/renamed/reordered anything during import, which would
explain why Unreal's compatibility check rejected it even though the source
FBX's hierarchy matches Chaos_Armor_Skeleton bone-for-bone.

HOW TO RUN IT
-------------
    py "X:/IronBreach/Content/Python/dump_starter_armor_skeleton.py"

Writes X:\\Downloads\\StarterArmor_SkeletonDump.fbx -- I'll pull it myself,
no need to paste anything back unless it errors.
"""

import unreal

MESH_PATH = "/Game/Characters/Infantry/Meshes/StarterArmor/SK_StarterArmor.SK_StarterArmor"
OUT_PATH = r"X:\Downloads\StarterArmor_SkeletonDump.fbx"

mesh = unreal.EditorAssetLibrary.load_asset(MESH_PATH)
if mesh is None:
    unreal.log_error(f"[DumpArmor] Could not load {MESH_PATH} -- does the asset exist at all? Check the Content Browser path.")
else:
    # Also report what skeleton this mesh currently thinks it has.
    try:
        sk = mesh.get_editor_property("skeleton")
        unreal.log(f"[DumpArmor] SK_StarterArmor.skeleton = {sk.get_path_name() if sk else None}")
    except Exception as e:
        unreal.log_warning(f"[DumpArmor] could not read skeleton property: {e}")

    task = unreal.AssetExportTask()
    task.set_editor_property("object", mesh)
    task.set_editor_property("filename", OUT_PATH)
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_identical", True)
    task.set_editor_property("prompt", False)
    task.set_editor_property("selected", False)

    exporter = getattr(unreal, "SkeletalMeshExporterFBX", None)
    if exporter is None:
        unreal.log_error("[DumpArmor] SkeletalMeshExporterFBX not found.")
    else:
        task.set_editor_property("exporter", exporter())
        success = unreal.Exporter.run_asset_export_task(task)
        unreal.log(f"[DumpArmor] export success={success} -> {OUT_PATH}")
