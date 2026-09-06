"""
DECISIVE TEST -- swap GarrisonPlatform_New to a plain, unmistakable bright
red material to find out if the visible diamond pattern is even coming
from the material at all
================================================================
IRON BREACH / Unreal Engine 5.8

Six completely different material states (real triplanar concrete at
various tile sizes, R=1, R=100, a full from-scratch rebuild with verified
successful Base Color/Roughness connections) have all produced the exact
same, unchanged diamond/argyle-looking pattern on the platform. That's
only possible if the platform isn't actually rendering M_AI_Ground's
output the way we think -- so before spending more time on that material,
this creates a brand new, dead-simple bright red material (no textures,
no triplanar, nothing that could tile) and assigns it directly to
GarrisonPlatform_New.

If the platform turns solid red -- material swaps DO work, and something
about M_AI_Ground specifically is still not right (we'll go back to it
with fresh eyes). If the platform STILL shows the diamond pattern even
with a solid red material assigned -- the pattern isn't a material at
all; it's baked into the mesh's own geometry/normal detail or a lighting
effect, and we need a completely different approach (e.g. a different
mesh, or fixing the mesh's own data instead of the material).

This does NOT touch M_AI_Ground itself -- fully reversible by re-running
unbake_platform_material.py-style logic or just re-assigning M_AI_Ground
back once we know the answer.

HOW TO RUN IT
-------------
    py "X:/IronBreach/Content/Python/test_swap_bright_material.py"
"""

import unreal

TARGET_LABEL = "GarrisonPlatform_New"
TEST_MATERIAL_PATH = "/Game/LevelPrototyping/AITextures/TEST_BrightRed"

actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
AL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()


def log(msg):
    print("[TestSwapBrightMaterial] %s" % msg)


def run():
    if AL.does_asset_exist(TEST_MATERIAL_PATH):
        test_mat = AL.load_asset(TEST_MATERIAL_PATH)
        log("Reusing existing test material.")
    else:
        package_path, asset_name = TEST_MATERIAL_PATH.rsplit("/", 1)
        factory = unreal.MaterialFactoryNew()
        test_mat = asset_tools.create_asset(asset_name, package_path, unreal.Material, factory)
        log("Created new test material: %s" % TEST_MATERIAL_PATH)

        red_const = MEL.create_material_expression(test_mat, unreal.MaterialExpressionConstant3Vector, -300, 0)
        red_const.set_editor_property("constant", unreal.LinearColor(1.0, 0.0, 0.0, 1.0))
        MEL.connect_material_property(red_const, "", unreal.MaterialProperty.MP_BASE_COLOR)

        rough_const = MEL.create_material_expression(test_mat, unreal.MaterialExpressionConstant, -300, 200)
        rough_const.set_editor_property("R", 0.9)
        MEL.connect_material_property(rough_const, "", unreal.MaterialProperty.MP_ROUGHNESS)

        MEL.recompile_material(test_mat)
        AL.save_asset(TEST_MATERIAL_PATH)

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

    mesh_comp.set_material(0, test_mat)
    log("Assigned TEST_BrightRed to slot 0 of %s." % TARGET_LABEL)
    log("Done. Save is optional (this is just a test) -- look at the platform now. Tell me: "
        "solid red, or still the same diamond pattern?")


run()
