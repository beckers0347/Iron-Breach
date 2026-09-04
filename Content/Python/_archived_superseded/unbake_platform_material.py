"""
UNBAKE THE PLATFORM'S GROUND MATERIAL -- swap the frozen baked instance
back for the live, editable M_AI_Ground
================================================================
IRON BREACH / Unreal Engine 5.8

Confirmed via the Output Log: GarrisonPlatform_New's mesh slot is pointed
at MI_M_Body2_M_AI_Ground_24A3440C487F14453DC25D9E61BCA5C9, a baked
MaterialInstanceConstant with its own frozen BaseColor texture (produced
by the "Bake Materials" button in the Details panel at some point). That's
why editing M_AI_Ground's tile-scale node had zero visible effect --
nothing was reading that graph anymore.

This finds every material slot on GarrisonPlatform_New's mesh component
that's using that baked instance (path contains "M_Body2_M_AI_Ground")
and reassigns it to the live M_AI_Ground material directly, as a
COMPONENT-LEVEL override (doesn't touch the underlying static mesh
asset's own default slot, so other actors using the same mesh are
unaffected). After this, editing M_AI_Ground's tile-scale Constant node
and clicking Apply will show up on the platform immediately again.

HOW TO RUN IT
-------------
    py "X:/IronBreach/Content/Python/unbake_platform_material.py"
"""

import unreal

TARGET_LABEL = "GarrisonPlatform_New"
LIVE_MATERIAL_PATH = "/Game/LevelPrototyping/AITextures/M_AI_Ground.M_AI_Ground"
BAKED_PATH_MARKER = "M_Body2_M_AI_Ground"
MAX_SLOTS_TO_CHECK = 16

actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
AL = unreal.EditorAssetLibrary


def log(msg):
    print("[UnbakePlatformMaterial] %s" % msg)


def run():
    live_material = AL.load_asset(LIVE_MATERIAL_PATH)
    if live_material is None:
        log("ABORTED -- %s not found." % LIVE_MATERIAL_PATH)
        return

    target = None
    for a in actor_subsystem.get_all_level_actors():
        if a.get_actor_label() == TARGET_LABEL:
            target = a
            break
    if target is None:
        log("ABORTED -- no actor labeled '%s' found." % TARGET_LABEL)
        return

    mesh_comp = target.get_component_by_class(unreal.StaticMeshComponent)
    if mesh_comp is None:
        log("ABORTED -- %s has no StaticMeshComponent." % TARGET_LABEL)
        return

    changed = 0
    for i in range(MAX_SLOTS_TO_CHECK):
        try:
            mat = mesh_comp.get_material(i)
        except Exception:
            break
        if mat is None:
            continue
        path = mat.get_path_name()
        if BAKED_PATH_MARKER in path:
            log("Slot %d: %s -> %s" % (i, path, LIVE_MATERIAL_PATH))
            mesh_comp.set_material(i, live_material)
            changed += 1
        else:
            log("Slot %d: %s (left alone -- not the baked instance)" % (i, path))

    if changed == 0:
        log("No slots referencing the baked instance were found -- nothing changed. "
            "Tell me what the log above showed and we'll figure out the right slot.")
    else:
        log("Done -- %d slot(s) switched back to the live M_AI_Ground material. "
            "Save, then go edit the tile-scale Constant node again -- it should show up now." % changed)


run()
