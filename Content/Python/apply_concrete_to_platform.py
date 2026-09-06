"""
APPLY THE CONCRETE MATERIAL TO THE GARRISON PLATFORM
================================================================
IRON BREACH / Unreal Engine 5.8

GarrisonPlatform_New is currently wearing its import's flat grey default
material (color_a0a0a0ff). This swaps it for M_AI_Ground -- the same
concrete ground material every other pad/yard surface in Carrowgate
Garrison uses (Vehicle Bay, Parade Yard, the old Ground_* segments before
they were replaced, etc.), so the new platform matches the rest of the
garrison's look instead of standing out as a bare grey placeholder.

Applies it to every material slot on the platform's mesh (in case it has
more than one element), not just slot 0.

HOW TO RUN IT
-------------
    py "X:/IronBreach/Content/Python/apply_concrete_to_platform.py"
"""

import unreal

CONCRETE_MATERIAL_PATH = "/Game/LevelPrototyping/AITextures/M_AI_Ground.M_AI_Ground"

actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
AL = unreal.EditorAssetLibrary


def log(msg):
    print("[ApplyConcreteToPlatform] %s" % msg)


def run():
    material = AL.load_asset(CONCRETE_MATERIAL_PATH)
    if material is None:
        log("ABORTED -- %s not found." % CONCRETE_MATERIAL_PATH)
        return

    platform = None
    for a in actor_subsystem.get_all_level_actors():
        if a.get_actor_label() == "GarrisonPlatform_New":
            platform = a
            break

    if platform is None:
        log("ABORTED -- GarrisonPlatform_New not found.")
        return

    mesh_comp = platform.static_mesh_component
    mesh = mesh_comp.static_mesh
    if mesh is None:
        log("ABORTED -- platform has no static mesh assigned.")
        return

    # get_material_slot_names is the more reliable way to enumerate slots across UE versions.
    slot_names = mesh_comp.get_material_slot_names() if hasattr(mesh_comp, "get_material_slot_names") else []
    num_materials = len(slot_names) if slot_names else max(mesh_comp.get_num_materials(), 1)

    for i in range(num_materials):
        mesh_comp.set_material(i, material)

    log("Applied M_AI_Ground to %d material slot(s) on GarrisonPlatform_New." % num_materials)
    log("Done. Save and take a look.")


run()
