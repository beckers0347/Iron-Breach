"""
IBPY: ib_geoscript_probe3.py

READ-ONLY, final follow-up probe. Gets exact call signatures for the
static-mesh <-> DynamicMesh copy functions (GeometryScript_AssetUtils) and
the doc/field info for the options structs they take, plus confirms the
GeometryScriptBooleanOperation enum's value names (need SUBTRACT). Touches
nothing.

HOW TO RUN:
  py "X:/IronBreach/Scripts/ib_geoscript_probe3.py"
"""

import unreal


def log(msg):
    unreal.log(f"IBPY: {msg}")


def main():
    log("---- GeometryScript_AssetUtils copy function doc strings ----")
    for name in ["copy_mesh_from_static_mesh", "copy_mesh_from_static_mesh_v2", "copy_mesh_to_static_mesh"]:
        func = getattr(unreal.GeometryScript_AssetUtils, name, None)
        doc = getattr(func, "__doc__", None) if func else None
        log(f"GeometryScript_AssetUtils.{name} doc:\n{doc}")

    log("---- Options struct doc strings ----")
    for name in [
        "GeometryScriptCopyMeshFromAssetOptions",
        "GeometryScriptCopyMeshToAssetOptions",
        "GeometryScriptMeshReadLOD",
        "GeometryScriptMeshWriteLOD",
        "GeometryScriptMeshBooleanOptions",
        "GeometryScriptPrimitiveOptions",
        "GeometryScriptCalculateNormalsOptions",
    ]:
        cls = getattr(unreal, name, None)
        doc = getattr(cls, "__doc__", None) if cls else None
        log(f"{name} doc:\n{doc}")

    log("---- GeometryScriptBooleanOperation enum values ----")
    enum_cls = getattr(unreal, "GeometryScriptBooleanOperation", None)
    if enum_cls:
        log([e for e in dir(enum_cls) if not e.startswith("_")])

    log("Done.")


main()
