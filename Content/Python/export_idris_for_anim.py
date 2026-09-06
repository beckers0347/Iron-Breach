"""
Export the existing Ms_Idris skeletal mesh back out to FBX so I can pull the
real mesh + bone rest pose into Blender and build new animations against her
ACTUAL proportions instead of guessing at a generic Mixamo rig (that guessing
game is exactly what burned so much time on the StarterArmor orientation
work -- not repeating it here).

This does NOT touch/modify the existing Ms_Idris asset in the project. It
only writes a copy out as FBX for reference.

HOW TO RUN
----------
    py "X:/IronBreach/Content/Python/export_idris_for_anim.py"

Output lands at:
    X:/IronBreach/Content/Characters/NPCs/MsIdris/Export/Ms_Idris_export.fbx

After it runs, just let me know it's done -- I'll pick the file up from
there.
"""

import os
import unreal

MESH_PATH = "/Game/Characters/NPCs/MsIdris/Ms_Idris.Ms_Idris"
OUT_DIR = r"X:\IronBreach\Content\Characters\NPCs\MsIdris\Export"
OUT_FILE = os.path.join(OUT_DIR, "Ms_Idris_export.fbx")


def run():
    os.makedirs(OUT_DIR, exist_ok=True)

    mesh = unreal.EditorAssetLibrary.load_asset(MESH_PATH)
    if mesh is None:
        unreal.log_error(f"[IdrisExport] Could not load {MESH_PATH} -- check the path.")
        return

    task = unreal.AssetExportTask()
    task.set_editor_property("object", mesh)
    task.set_editor_property("filename", OUT_FILE)
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_identical", True)
    task.set_editor_property("prompt", False)
    task.set_editor_property("exporter", unreal.SkeletalMeshExporterFBX())

    success = unreal.Exporter.run_asset_export_task(task)
    if success:
        unreal.log(f"[IdrisExport] DONE. Wrote {OUT_FILE}")
    else:
        unreal.log_error("[IdrisExport] Export failed -- see Output Log above for details.")


run()
