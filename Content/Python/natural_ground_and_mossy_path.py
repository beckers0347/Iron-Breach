"""
NATURAL GROUND TEXTURE + MOSSY COBBLESTONE PATHS -- CG Mainland
================================================================
IRON BREACH / Unreal Engine 5.8

WHAT'S WRONG WITH THE CURRENT GROUND
--------------------------------------
M_AI_MountainGround is currently built from T_Iceland_Eroded -- a rock-strata/
erosion texture with strong linear striations. That's exactly right for a
cliff face (which is why the mountains look good with it), but tiled flat
across open ground it reads as directional streaks -- wood grain, not dirt.
Wrong texture for the surface, not a scale/tiling problem.

FIX 1 -- GROUND: rebuilds M_AI_MountainGround (same asset, already assigned
to every ground actor -- no re-swap needed) using T_Iceland_Dirt instead --
the texture actually meant for flat ground, more granular/isotropic, no
directional streaking.

FIX 2 -- MOSSY COBBLESTONE PATHS: builds a new material, M_AI_CobblestonePath,
from T_MossyCreekStones (BaseColor/Normal/Roughness -- already in the
project, just never wired to anything), tiled small (1.5m) so individual
stones read at a believable size, and force-assigns it to every actor
currently on MI_Landmass_Road -- that's the material every street/causeway/
outskirt-road actor in build_carrowgate_mainland.py uses
(PALETTE["road"], set directly with no fallback-substitution trick like the
ground material had, so matching by current material name is reliable this
time).

HOW TO RUN IT
-------------
    py "X:/IronBreach/Content/Python/natural_ground_and_mossy_path.py"

Safe to re-run.
"""

import unreal

MEL = unreal.MaterialEditingLibrary
AL = unreal.EditorAssetLibrary
actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

GROUND_MATERIAL_PATH = "/Game/LevelPrototyping/AITextures/Landmass/M_AI_MountainGround"
DIRT_BASECOLOR = "/Game/Landscaping/IcelandEnviroment/Textures/T_Iceland_Dirt/T_Iceland_Dirt_BaseColor"
DIRT_NORMAL = "/Game/Landscaping/IcelandEnviroment/Textures/T_Iceland_Dirt/T_Iceland_Dirt_Normal"

ROAD_MATERIAL_PATH = "/Game/LevelPrototyping/AITextures/Landmass/MI_Landmass_Road"
PATH_MATERIAL_PATH = "/Game/LevelPrototyping/AITextures/Landmass/M_AI_CobblestonePath"
MOSS_ALBEDO = "/Game/Landscaping/IcelandEnviroment/Textures/T_MossyCreekStones/T_MossyCreekStones_A"
MOSS_NORMAL = "/Game/Landscaping/IcelandEnviroment/Textures/T_MossyCreekStones/T_MossyCreekStones_N"
MOSS_ROUGH = "/Game/Landscaping/IcelandEnviroment/Textures/T_MossyCreekStones/T_MossyCreekStones_R"


def log(msg):
    print("[NaturalGround] %s" % msg)


def build_triplanar(material, basecolor_tex, normal_tex, roughness_tex, tile_world_size, roughness_const=0.9):
    """basecolor + normal + (optional) real roughness map, triplanar (world-aligned,
    seamless regardless of actor UVs). No metallic connection -- ever (lesson learned
    from the ground-turned-water bug)."""
    log("Rebuilding %s (tile=%.0fcm)..." % (material.get_name(), tile_world_size))
    MEL.delete_all_material_expressions(material)

    world_pos = MEL.create_material_expression(material, unreal.MaterialExpressionWorldPosition, -1600, 0)
    tile_scale = MEL.create_material_expression(material, unreal.MaterialExpressionConstant, -1600, 150)
    tile_scale.set_editor_property("R", 1.0 / tile_world_size)
    scaled_pos = MEL.create_material_expression(material, unreal.MaterialExpressionMultiply, -1400, 0)
    MEL.connect_material_expressions(world_pos, "", scaled_pos, "A")
    MEL.connect_material_expressions(tile_scale, "", scaled_pos, "B")

    mask_yz = MEL.create_material_expression(material, unreal.MaterialExpressionComponentMask, -1200, -300)
    mask_yz.set_editor_property("R", False); mask_yz.set_editor_property("G", True)
    mask_yz.set_editor_property("B", True);  mask_yz.set_editor_property("A", False)
    MEL.connect_material_expressions(scaled_pos, "", mask_yz, "")

    mask_xz = MEL.create_material_expression(material, unreal.MaterialExpressionComponentMask, -1200, 0)
    mask_xz.set_editor_property("R", True);  mask_xz.set_editor_property("G", False)
    mask_xz.set_editor_property("B", True);  mask_xz.set_editor_property("A", False)
    MEL.connect_material_expressions(scaled_pos, "", mask_xz, "")

    mask_xy = MEL.create_material_expression(material, unreal.MaterialExpressionComponentMask, -1200, 300)
    mask_xy.set_editor_property("R", True);  mask_xy.set_editor_property("G", True)
    mask_xy.set_editor_property("B", False); mask_xy.set_editor_property("A", False)
    MEL.connect_material_expressions(scaled_pos, "", mask_xy, "")

    world_normal = MEL.create_material_expression(material, unreal.MaterialExpressionVertexNormalWS, -1200, 600)
    abs_normal = MEL.create_material_expression(material, unreal.MaterialExpressionAbs, -1000, 600)
    MEL.connect_material_expressions(world_normal, "", abs_normal, "")
    sharpness_const = MEL.create_material_expression(material, unreal.MaterialExpressionConstant, -1000, 750)
    sharpness_const.set_editor_property("R", 4.0)
    weight_pow = MEL.create_material_expression(material, unreal.MaterialExpressionPower, -800, 600)
    MEL.connect_material_expressions(abs_normal, "", weight_pow, "Base")
    MEL.connect_material_expressions(sharpness_const, "", weight_pow, "Exp")

    w_x = MEL.create_material_expression(material, unreal.MaterialExpressionComponentMask, -600, 520)
    w_x.set_editor_property("R", True); w_x.set_editor_property("G", False)
    w_x.set_editor_property("B", False); w_x.set_editor_property("A", False)
    MEL.connect_material_expressions(weight_pow, "", w_x, "")
    w_y = MEL.create_material_expression(material, unreal.MaterialExpressionComponentMask, -600, 600)
    w_y.set_editor_property("R", False); w_y.set_editor_property("G", True)
    w_y.set_editor_property("B", False); w_y.set_editor_property("A", False)
    MEL.connect_material_expressions(weight_pow, "", w_y, "")
    w_z = MEL.create_material_expression(material, unreal.MaterialExpressionComponentMask, -600, 680)
    w_z.set_editor_property("R", False); w_z.set_editor_property("G", False)
    w_z.set_editor_property("B", True); w_z.set_editor_property("A", False)
    MEL.connect_material_expressions(weight_pow, "", w_z, "")

    sum_xy = MEL.create_material_expression(material, unreal.MaterialExpressionAdd, -420, 560)
    MEL.connect_material_expressions(w_x, "", sum_xy, "A")
    MEL.connect_material_expressions(w_y, "", sum_xy, "B")
    sum_xyz = MEL.create_material_expression(material, unreal.MaterialExpressionAdd, -280, 600)
    MEL.connect_material_expressions(sum_xy, "", sum_xyz, "A")
    MEL.connect_material_expressions(w_z, "", sum_xyz, "B")

    norm_x = MEL.create_material_expression(material, unreal.MaterialExpressionDivide, -120, 480)
    MEL.connect_material_expressions(w_x, "", norm_x, "A")
    MEL.connect_material_expressions(sum_xyz, "", norm_x, "B")
    norm_y = MEL.create_material_expression(material, unreal.MaterialExpressionDivide, -120, 600)
    MEL.connect_material_expressions(w_y, "", norm_y, "A")
    MEL.connect_material_expressions(sum_xyz, "", norm_y, "B")
    norm_z = MEL.create_material_expression(material, unreal.MaterialExpressionDivide, -120, 720)
    MEL.connect_material_expressions(w_z, "", norm_z, "A")
    MEL.connect_material_expressions(sum_xyz, "", norm_z, "B")

    def sample_and_blend(tex, out_y, prop, is_normal=False, channel="RGB"):
        tx = MEL.create_material_expression(material, unreal.MaterialExpressionTextureSample, 0, out_y - 200)
        tx.set_editor_property("texture", tex)
        if is_normal:
            tx.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
        MEL.connect_material_expressions(mask_yz, "", tx, "Coordinates")

        ty = MEL.create_material_expression(material, unreal.MaterialExpressionTextureSample, 0, out_y)
        ty.set_editor_property("texture", tex)
        if is_normal:
            ty.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
        MEL.connect_material_expressions(mask_xz, "", ty, "Coordinates")

        tz = MEL.create_material_expression(material, unreal.MaterialExpressionTextureSample, 0, out_y + 200)
        tz.set_editor_property("texture", tex)
        if is_normal:
            tz.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
        MEL.connect_material_expressions(mask_xy, "", tz, "Coordinates")

        mul_x = MEL.create_material_expression(material, unreal.MaterialExpressionMultiply, 260, out_y - 200)
        MEL.connect_material_expressions(tx, channel, mul_x, "A")
        MEL.connect_material_expressions(norm_x, "", mul_x, "B")
        mul_y = MEL.create_material_expression(material, unreal.MaterialExpressionMultiply, 260, out_y)
        MEL.connect_material_expressions(ty, channel, mul_y, "A")
        MEL.connect_material_expressions(norm_y, "", mul_y, "B")
        mul_z = MEL.create_material_expression(material, unreal.MaterialExpressionMultiply, 260, out_y + 200)
        MEL.connect_material_expressions(tz, channel, mul_z, "A")
        MEL.connect_material_expressions(norm_z, "", mul_z, "B")

        add_xy = MEL.create_material_expression(material, unreal.MaterialExpressionAdd, 480, out_y - 100)
        MEL.connect_material_expressions(mul_x, "", add_xy, "A")
        MEL.connect_material_expressions(mul_y, "", add_xy, "B")
        add_xyz = MEL.create_material_expression(material, unreal.MaterialExpressionAdd, 640, out_y)
        MEL.connect_material_expressions(add_xy, "", add_xyz, "A")
        MEL.connect_material_expressions(mul_z, "", add_xyz, "B")

        MEL.connect_material_property(add_xyz, "", prop)

    sample_and_blend(basecolor_tex, 0, unreal.MaterialProperty.MP_BASE_COLOR)
    if normal_tex:
        sample_and_blend(normal_tex, 900, unreal.MaterialProperty.MP_NORMAL, is_normal=True)

    if roughness_tex:
        sample_and_blend(roughness_tex, 1500, unreal.MaterialProperty.MP_ROUGHNESS, channel="R")
    else:
        rough_const = MEL.create_material_expression(material, unreal.MaterialExpressionConstant, 260, 1400)
        rough_const.set_editor_property("R", roughness_const)
        MEL.connect_material_property(rough_const, "", unreal.MaterialProperty.MP_ROUGHNESS)

    MEL.recompile_material(material)
    log("  done -- %s recompiled." % material.get_name())


def get_or_create_material(path):
    if AL.does_asset_exist(path):
        return AL.load_asset(path)
    package_path, name = path.rsplit("/", 1)
    factory = unreal.MaterialFactoryNew()
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    return asset_tools.create_asset(name, package_path, unreal.Material, factory)


def fix_ground():
    if not AL.does_asset_exist(GROUND_MATERIAL_PATH):
        log("SKIPPED ground -- %s doesn't exist." % GROUND_MATERIAL_PATH)
        return
    ground_mat = AL.load_asset(GROUND_MATERIAL_PATH)
    basecolor = AL.load_asset(DIRT_BASECOLOR)
    normal = AL.load_asset(DIRT_NORMAL)
    if not basecolor:
        log("SKIPPED ground -- could not load %s" % DIRT_BASECOLOR)
        return
    build_triplanar(ground_mat, basecolor, normal, None, tile_world_size=1200.0, roughness_const=0.92)
    log("Ground actors already point at this material -- no re-assignment needed.")


def fix_paths():
    albedo = AL.load_asset(MOSS_ALBEDO)
    normal = AL.load_asset(MOSS_NORMAL)
    rough = AL.load_asset(MOSS_ROUGH)
    if not albedo:
        log("SKIPPED paths -- could not load %s" % MOSS_ALBEDO)
        return

    path_mat = get_or_create_material(PATH_MATERIAL_PATH)
    build_triplanar(path_mat, albedo, normal, rough, tile_world_size=150.0)

    road_mat = AL.load_asset(ROAD_MATERIAL_PATH) if AL.does_asset_exist(ROAD_MATERIAL_PATH) else None
    if road_mat is None:
        log("Note: %s doesn't exist in this checkout -- nothing to swap away from. "
            "The new material is built and ready at %s if you want to hand-assign it." % (
                ROAD_MATERIAL_PATH, PATH_MATERIAL_PATH))
        return

    swapped = 0
    for a in actor_subsystem.get_all_level_actors():
        if not isinstance(a, unreal.StaticMeshActor):
            continue
        comp = a.static_mesh_component
        if comp and comp.get_material(0) == road_mat:
            comp.set_material(0, path_mat)
            swapped += 1
    log("Swapped %d street/road/path actor(s) to the mossy cobblestone material." % swapped)


def run():
    fix_ground()
    fix_paths()
    log("All done. Save the level and modified materials (Ctrl+Shift+S / File > Save All), "
        "then check the viewport or a fresh PIE run.")


run()
