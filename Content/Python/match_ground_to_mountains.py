"""
MATCH GROUND TEXTURE TO THE MOUNTAINS
================================================================
IRON BREACH / Unreal Engine 5.8

WHAT THIS DOES
--------------
The ground (M_AI_MountainGround) is currently built from T_Iceland_Dirt --
a plain dirt texture, which is why it reads as a different material family
from the mountains now that those are on real rock textures
(T_Mountain_01 / T_Mountain_02 / T_Iceland_Eroded). This rebuilds
M_AI_MountainGround -- same asset, already assigned to every ground actor, so
nothing needs to be re-swapped -- using T_Iceland_Eroded instead: the same
texture already used on the SM_Iceland_Eroded_Mountain peaks, so the ground
now reads as a continuation of the mountain rock (like scree/talus at the
base of the slopes) instead of a separate dirt material. Tiled tighter than
the mountains themselves (600m world-size vs. the mountains' 4000m) since the
ground is seen much closer to camera and would look blurry/stretched at the
mountains' own tile scale.

Same triplanar approach as the last two fixes (world-aligned, seamless across
every ground actor regardless of its own UVs), BaseColor + Normal only, no
ORM/metallic -- matte roughness constant, same as the mountains now use.

HOW TO RUN IT
-------------
    py "X:/IronBreach/Content/Python/match_ground_to_mountains.py"

Safe to re-run.
"""

import unreal

MEL = unreal.MaterialEditingLibrary
AL = unreal.EditorAssetLibrary

GROUND_MATERIAL_PATH = "/Game/LevelPrototyping/AITextures/Landmass/M_AI_MountainGround"
ERODED_BASECOLOR = "/Game/Landscaping/IcelandEnviroment/Textures/T_Iceland_Eroded/T_Iceland_Eroded_BaseColor"
ERODED_NORMAL = "/Game/Landscaping/IcelandEnviroment/Textures/T_Iceland_Eroded/Iceland_Eroded_Normal"


def log(msg):
    print("[MatchGround] %s" % msg)


def build_triplanar_basecolor_normal(material, basecolor_tex, normal_tex, tile_world_size=600.0, blend_sharpness=4.0, roughness=0.95):
    log("Rebuilding %s from T_Iceland_Eroded (matches the mountain rock)..." % material.get_name())
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
    sharpness_const.set_editor_property("R", blend_sharpness)
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

    def sample_and_blend(tex, out_y, prop, is_normal=False):
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
        MEL.connect_material_expressions(tx, "RGB", mul_x, "A")
        MEL.connect_material_expressions(norm_x, "", mul_x, "B")
        mul_y = MEL.create_material_expression(material, unreal.MaterialExpressionMultiply, 260, out_y)
        MEL.connect_material_expressions(ty, "RGB", mul_y, "A")
        MEL.connect_material_expressions(norm_y, "", mul_y, "B")
        mul_z = MEL.create_material_expression(material, unreal.MaterialExpressionMultiply, 260, out_y + 200)
        MEL.connect_material_expressions(tz, "RGB", mul_z, "A")
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

    rough_const = MEL.create_material_expression(material, unreal.MaterialExpressionConstant, 260, 1400)
    rough_const.set_editor_property("R", roughness)
    MEL.connect_material_property(rough_const, "", unreal.MaterialProperty.MP_ROUGHNESS)
    # No metallic connection -- defaults to 0.

    MEL.recompile_material(material)
    log("  done -- %s recompiled." % material.get_name())


def run():
    if not AL.does_asset_exist(GROUND_MATERIAL_PATH):
        log("SKIPPED -- %s doesn't exist yet. Run fix_mountains_and_ground.py first." % GROUND_MATERIAL_PATH)
        return
    ground_mat = AL.load_asset(GROUND_MATERIAL_PATH)
    basecolor = AL.load_asset(ERODED_BASECOLOR)
    normal = AL.load_asset(ERODED_NORMAL)
    if not basecolor:
        log("SKIPPED -- could not load %s" % ERODED_BASECOLOR)
        return
    build_triplanar_basecolor_normal(ground_mat, basecolor, normal)
    log("Done -- ground actors already point at this material, no re-assignment needed. "
        "Save and check the viewport / re-run PIE.")


run()
