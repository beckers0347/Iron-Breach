"""
DIAGNOSE WHAT MATERIAL IS ACTUALLY ON GarrisonPlatform_New -- read-only,
changes nothing
================================================================
IRON BREACH / Unreal Engine 5.8

Setting the tile-scale Constant on M_AI_Ground to 1, then to 100, produced
NO visible change on the platform -- that's only possible if the platform
isn't actually rendering M_AI_Ground itself. This prints exactly what's
assigned to every material slot on GarrisonPlatform_New's mesh: the real
class (Material vs MaterialInstanceConstant vs MaterialInstanceDynamic),
its exact asset path, and -- if it's an instance -- what its parent is.
That will show whether we're editing the material that's actually visible.

HOW TO RUN IT
-------------
    py "X:/IronBreach/Content/Python/diagnose_platform_material_assignment.py"
"""

import unreal

TARGET_LABEL = "GarrisonPlatform_New"

actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def log(msg):
    print("[DiagnosePlatformMaterialAssignment] %s" % msg)


def describe_material(mat, indent="  "):
    if mat is None:
        log(indent + "None")
        return
    cls = type(mat).__name__
    path = mat.get_path_name()
    log(indent + "class=%s  path=%s" % (cls, path))
    if isinstance(mat, unreal.MaterialInstance):
        parent = mat.get_editor_property("parent")
        if parent is not None:
            log(indent + "  parent -> class=%s path=%s" % (type(parent).__name__, parent.get_path_name()))
        else:
            log(indent + "  parent -> None")


def run():
    found = False
    for a in actor_subsystem.get_all_level_actors():
        if a.get_actor_label() != TARGET_LABEL:
            continue
        found = True
        log("Actor: %s" % a.get_actor_label())

        mesh_comp = a.get_component_by_class(unreal.StaticMeshComponent)
        if mesh_comp is None:
            log("  No StaticMeshComponent found.")
            continue

        static_mesh = mesh_comp.get_editor_property("static_mesh")
        log("  StaticMesh asset: %s" % (static_mesh.get_path_name() if static_mesh else "None"))

        num_slots = mesh_comp.get_num_material_slots()
        log("  Material slots on the COMPONENT (i.e. what's actually rendering): %d" % num_slots)
        for i in range(num_slots):
            log("  -- Element %d (component override) --" % i)
            mat = mesh_comp.get_material(i)
            describe_material(mat)

        if static_mesh is not None:
            static_mats = static_mesh.get_editor_property("static_materials") if static_mesh.get_editor_property("static_materials") else None
            try:
                mesh_materials = static_mesh.get_editor_property("static_materials")
            except Exception:
                mesh_materials = None
            if mesh_materials:
                log("  Material slots on the STATIC MESH ASSET itself (the default, before any component override):")
                for i, sm in enumerate(mesh_materials):
                    mat = sm.get_editor_property("material_interface")
                    log("  -- Slot %d (asset default) --" % i)
                    describe_material(mat)

    if not found:
        log("ABORTED -- no actor labeled '%s' found in the level." % TARGET_LABEL)
        return

    log("Done. Nothing was changed.")


run()
