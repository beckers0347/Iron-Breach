"""
IBPY: ib_geoscript_probe2.py

READ-ONLY, follow-up to ib_geoscript_probe.py. That probe showed this
engine build's mesh-editing functions live as methods directly on
unreal.DynamicMesh (e.g. DynamicMesh.apply_mesh_boolean,
DynamicMesh.append_box), not on separate GeometryScriptLibrary_* classes.
This probe:
  1. Lists members of the asset-utility classes that likely hold the
     "static mesh asset <-> DynamicMesh" copy functions
     (GeometryScript_AssetUtils, GeometryScript_NewAssetUtils,
     GeometryScript_SceneUtils, GeometryScript_EditorDynamicMeshUtil).
  2. Prints full doc strings (signatures) for the specific DynamicMesh
     methods we'll need: apply_mesh_boolean, append_box, recompute_normals.
  3. Properly checks for StaticMesh's alternate "complex collision mesh"
     property via get_editor_property() with try/except, since a plain
     dir() check (what the first probe used) can miss valid UE properties
     that aren't surfaced as direct Python attributes.

Touches nothing -- no assets or actors are modified.

HOW TO RUN:
  py "X:/IronBreach/Scripts/ib_geoscript_probe2.py"
"""

import unreal


def log(msg):
    unreal.log(f"IBPY: {msg}")


def main():
    asset_util_classes = [
        "GeometryScript_AssetUtils",
        "GeometryScript_NewAssetUtils",
        "GeometryScript_SceneUtils",
        "GeometryScript_EditorDynamicMeshUtil",
    ]
    for cls_name in asset_util_classes:
        cls = getattr(unreal, cls_name, None)
        log(f"---- {cls_name}: {'FOUND' if cls else 'NOT FOUND'} ----")
        if not cls:
            continue
        members = [m for m in dir(cls) if not m.startswith("_")]
        for m in members:
            log(f"  {cls_name}.{m}")

    log("---- DynamicMesh method doc strings ----")
    for method_name in ["apply_mesh_boolean", "append_box", "recompute_normals", "translate_mesh", "transform_mesh"]:
        method = getattr(unreal.DynamicMesh, method_name, None)
        doc = getattr(method, "__doc__", None) if method else None
        log(f"DynamicMesh.{method_name} doc:\n{doc}")

    log("---- StaticMesh alternate/complex collision mesh property check (via get_editor_property) ----")
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
                for prop_name in ["complex_collision_mesh", "ComplexCollisionMesh", "body_setup"]:
                    try:
                        val = static_mesh.get_editor_property(prop_name)
                        log(f"  static_mesh.get_editor_property('{prop_name}') = {val}")
                    except Exception as e:
                        log(f"  static_mesh.get_editor_property('{prop_name}') FAILED: {e}")
                body_setup = static_mesh.get_editor_property("body_setup")
                if body_setup:
                    bs_props = [p for p in dir(body_setup) if not p.startswith("_")]
                    log(f"  body_setup members: {bs_props}")
            else:
                log("Could not resolve SM_Armory_Tripo's StaticMesh asset.")
        else:
            log("Could not find SM_Armory_Tripo actor.")
    except Exception as e:
        log(f"complex_collision_mesh probe failed: {e}")

    log("Done.")


main()
