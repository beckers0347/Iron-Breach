"""
IBPY: ib_geoscript_probe.py

READ-ONLY. Doesn't touch any asset or actor. Before writing the real
mesh-boolean "carve a doorway hole" script for option B, this dumps the
exact Geometry Script Python API available in THIS engine build -- class
names, function names, and (where UE exposes them) full call signatures
with parameter names/types/defaults -- so the real script is written
against what's actually here instead of guessed from memory of other UE5.x
versions, which have moved these functions around and renamed parameters
release to release.

HOW TO RUN:
  py "X:/IronBreach/Scripts/ib_geoscript_probe.py"
Then send me the IBPY: log output (Output Log, or search "IBPY:" in
Saved/Logs/IronBreach.log).
"""

import unreal


def log(msg):
    unreal.log(f"IBPY: {msg}")


def main():
    log("---- GeometryScript-related classes in this build ----")
    gs_classes = sorted(name for name in dir(unreal) if "GeometryScript" in name)
    for name in gs_classes:
        log(name)

    targets = [
        "GeometryScriptLibrary_StaticMeshFunctions",
        "GeometryScriptLibrary_MeshBooleanFunctions",
        "GeometryScriptLibrary_PrimitiveFunctions",
        "GeometryScriptLibrary_MeshNormalsFunctions",
        "GeometryScriptLibrary_MeshTransformFunctions",
        "DynamicMesh",
    ]

    for cls_name in targets:
        cls = getattr(unreal, cls_name, None)
        log(f"---- {cls_name}: {'FOUND' if cls else 'NOT FOUND'} ----")
        if not cls:
            continue
        members = [m for m in dir(cls) if not m.startswith("_")]
        for m in members:
            log(f"  {cls_name}.{m}")

    log("---- Function signatures (doc strings) ----")
    interesting_funcs = [
        ("GeometryScriptLibrary_StaticMeshFunctions", "copy_mesh_from_static_mesh"),
        ("GeometryScriptLibrary_StaticMeshFunctions", "copy_mesh_to_static_mesh"),
        ("GeometryScriptLibrary_MeshBooleanFunctions", "apply_mesh_boolean"),
        ("GeometryScriptLibrary_PrimitiveFunctions", "append_box"),
        ("GeometryScriptLibrary_MeshNormalsFunctions", "recompute_normals"),
    ]
    for cls_name, func_name in interesting_funcs:
        cls = getattr(unreal, cls_name, None)
        func = getattr(cls, func_name, None) if cls else None
        if func is None:
            log(f"{cls_name}.{func_name}: NOT FOUND")
            continue
        doc = getattr(func, "__doc__", None)
        log(f"{cls_name}.{func_name} doc:\n{doc}")

    # Also check the StaticMesh asset property we'd need for the
    # non-destructive "alternate complex collision mesh" approach, so the
    # original visual mesh asset is never modified.
    log("---- StaticMesh 'complex_collision_mesh' property check ----")
    try:
        subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        armory = None
        for a in subsystem.get_all_level_actors():
            if a.get_actor_label() == "SM_Armory_Tripo":
                armory = a
                break
        if armory:
            mesh_comp = getattr(armory, "static_mesh_component", None) or armory.get_component_by_class(unreal.StaticMeshComponent)
            static_mesh = mesh_comp.get_editor_property("static_mesh") if mesh_comp else None
            if static_mesh:
                has_prop = "complex_collision_mesh" in dir(static_mesh)
                log(f"StaticMesh 'complex_collision_mesh' attribute present: {has_prop}")
                if has_prop:
                    log(f"Current value: {static_mesh.get_editor_property('complex_collision_mesh')}")
            else:
                log("Could not resolve SM_Armory_Tripo's StaticMesh asset.")
        else:
            log("Could not find SM_Armory_Tripo actor.")
    except Exception as e:
        log(f"complex_collision_mesh probe failed: {e}")

    log("Done.")


main()
