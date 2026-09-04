"""
FIX THE STREAKING -- drop the broken triplanar normal-map blend
================================================================
IRON BREACH / Unreal Engine 5.8

THE ACTUAL BUG
----------------
Every triplanar material script in this session's ground/mountain/path work
shared the same normal-map blending code: sample the normal map from 3 axis
projections, then combine them with the same weighted-sum math used for the
color channels. That's fine for color, but it's not valid for normal
vectors -- summing raw tangent-space normal RGB values from 3 different
projections doesn't produce a correct combined normal, it can produce
distorted/exploded values, which reads as exactly the kind of hard
directional banding/streaking seen in the screenshots (bright streaks in the
specular highlights, present in the SAME shape and place no matter which
base color texture was underneath -- dirt, eroded rock, forest ground all
looked identical, which was the tell that it was never the color texture at
fault).

THE FIX
-------
Rebuilds M_AI_MountainGround (T_ForestGround) and M_AI_CobblestonePath
(T_MossyCreekStones) WITHOUT the normal map step at all -- base color +
(for the path) a real roughness map, flat vertex-normal shading otherwise.
Less fine surface detail than a correctly-blended normal map would give, but
correct and streak-free, which matters more right now. If it looks good
flat, a proper whiteout-blended normal map (reorienting each per-axis sample
into world space before combining, which is the correct way to triplanar-
blend normals) can be added back later as a real enhancement rather than
patched again under time pressure.

HOW TO RUN IT
-------------
    py "X:/IronBreach/Content/Python/fix_broken_normal_streaking.py"

Safe to re-run.
"""

import unreal

MEL = unreal.MaterialEditingLibrary
AL = unreal.EditorAssetLibrary

GROUND_MATERIAL_PATH = "/Game/LevelPrototyping/AITextures/Landmass/M_AI_MountainGround"
FOREST_BASECOLOR = "/Game/Landscaping/IcelandEnviroment/Textures/T_ForestGround/T_ForestGround_A"

PATH_MATERIAL_PATH = "/Game/LevelPrototyping/AITextures/Landmass/M_AI_CobblestonePath"
MOSS_ALBEDO = "/Game/Landscaping/IcelandEnviroment/Textures/T_MossyCreekStones/T_MossyCreekStones_A"
MOSS_ROUGH = "/Game/Landscaping/IcelandEnviroment/Textures/T_MossyCreekStones/T_MossyCreekStones_R"


def log(msg):
    print("[FixStreaking] %s" % msg)


def build_triplanar_no_normal(material, basecolor_tex, roughness_tex, tile_world_size, roughness_const=0.9, blend_sharpness=4.0):
    log("Rebuilding %s (basecolor%s only -- NO normal map, that's what was streaking)..." % (
        material.get_name(), " + roughness map" if roughness_tex else ""))
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

    def sample_and_blend(tex, out_y, prop, channel="RGB"):
        tx = MEL.create_material_expression(material, unreal.MaterialExpressionTextureSample, 0, out_y - 200)
        tx.set_editor_property("texture", tex)
        MEL.connect_material_expressions(mask_yz, "", tx, "Coordinates")

        ty = MEL.create_material_expression(material, unreal.MaterialExpressionTextureSample, 0, out_y)
        ty.set_editor_property("texture", tex)
        MEL.connect_material_expressions(mask_xz, "", ty, "Coordinates")

        tz = MEL.create_material_expression(material, unreal.MaterialExpressionTextureSample, 0, out_y + 200)
        tz.set_editor_property("texture", tex)
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
    # NO normal map sampling at all this time -- that's the fix.

    if roughness_tex:
        sample_and_blend(roughness_tex, 1500, unreal.MaterialProperty.MP_ROUGHNESS, channel="R")
    else:
        rough_const = MEL.create_material_expression(material, unreal.MaterialExpressionConstant, 260, 1400)
        rough_const.set_editor_property("R", roughness_const)
        MEL.connect_material_property(rough_const, "", unreal.MaterialProperty.MP_ROUGHNESS)

    MEL.recompile_material(material)
    log("  done -- %s recompiled." % material.get_name())


def run():
    if AL.does_asset_exist(GROUND_MATERIAL_PATH):
        ground_mat = AL.load_asset(GROUND_MATERIAL_PATH)
        basecolor = AL.load_asset(FOREST_BASECOLOR)
        if basecolor:
            build_triplanar_no_normal(ground_mat, basecolor, None, tile_world_size=800.0, roughness_const=0.9)
        else:
            log("SKIPPED ground -- could not load %s" % FOREST_BASECOLOR)
    else:
        log("SKIPPED ground -- %s doesn't exist." % GROUND_MATERIAL_PATH)

    if AL.does_asset_exist(PATH_MATERIAL_PATH):
        path_mat = AL.load_asset(PATH_MATERIAL_PATH)
        albedo = AL.load_asset(MOSS_ALBEDO)
        rough = AL.load_asset(MOSS_ROUGH)
        if albedo:
            build_triplanar_no_normal(path_mat, albedo, rough, tile_world_size=150.0)
        else:
            log("SKIPPED path -- could not load %s" % MOSS_ALBEDO)
    else:
        log("SKIPPED path -- %s doesn't exist." % PATH_MATERIAL_PATH)

    log("Both materials already assigned to their actors -- no re-assignment needed. "
        "Save and check the viewport / re-run PIE.")


run()
