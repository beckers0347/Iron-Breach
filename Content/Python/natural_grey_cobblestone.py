"""
GREY, IRREGULAR COBBLESTONE -- true neutral grey stones + jittered grout
so the seams read as hand-laid/natural instead of a perfect ruled grid
================================================================
IRON BREACH / Unreal Engine 5.8

WHY
---
Simply tinting the raw T_MossyCreekStones color darker (the last version)
couldn't actually turn it grey -- multiplying a warm reddish-brown texture
by another color can only scale each channel down, it can't remove the
underlying hue. This version pulls the texture's LUMINANCE only (its
light/dark detail, via a dot-product greyscale conversion) and then
recombines that with a genuinely neutral grey tint color, so the result is
actually grey regardless of what color the source photo was.

For "not a perfect grid": every cell's grout width is jittered by a cheap
per-cell hash (a hashed value derived from that cell's integer grid
coordinate, via the classic sine/frac pseudo-random trick -- deterministic,
same seed every time, no `random` module needed) so seam thickness varies
cell to cell instead of being a ruler-straight uniform grid. Each stone
also gets a small brightness variance from that same hash so no two pavers
read as identical copies. It's still a grid topologically (this is a safe,
implementable step rather than true irregular polygon flagstone, which
would need Voronoi cells and is a bigger follow-up if you want to go that
far), but the straight-ruled-grid look should be gone.

Tunables at the top: CELL_SIZE_CM, GROUT_WIDTH, GROUT_JITTER (how uneven
the seams are), STONE_TINT (the grey), BRIGHTNESS_JITTER.

HOW TO RUN IT
-------------
    py "X:/IronBreach/Content/Python/natural_grey_cobblestone.py"
"""

import unreal

MEL = unreal.MaterialEditingLibrary
AL = unreal.EditorAssetLibrary

PATH_MATERIAL_PATH = "/Game/LevelPrototyping/AITextures/Landmass/M_AI_CobblestonePath"
MOSS_ALBEDO = "/Game/Landscaping/IcelandEnviroment/Textures/T_MossyCreekStones/T_MossyCreekStones_A"
MOSS_ROUGH = "/Game/Landscaping/IcelandEnviroment/Textures/T_MossyCreekStones/T_MossyCreekStones_R"

TILE_WORLD_SIZE = 100.0
CELL_SIZE_CM = 70.0
GROUT_WIDTH = 0.14
GROUT_JITTER = 0.09          # how much each cell's seam width varies from the baseline
GROUT_SOFTNESS = 0.05
GROUT_COLOR = (0.045, 0.045, 0.05)
STONE_TINT = (0.46, 0.47, 0.49)     # genuinely neutral (very slightly cool) grey
BRIGHTNESS_JITTER = 0.28            # +/- per-stone brightness variance


def log(msg):
    print("[NaturalGreyCobblestone] %s" % msg)


def build_cobblestone(material, basecolor_tex, roughness_tex):
    log("Rebuilding %s -- grey + jittered grout (cell=%.0fcm)..." % (material.get_name(), CELL_SIZE_CM))
    MEL.delete_all_material_expressions(material)

    world_pos = MEL.create_material_expression(material, unreal.MaterialExpressionWorldPosition, -1800, 0)
    tile_scale = MEL.create_material_expression(material, unreal.MaterialExpressionConstant, -1800, 150)
    tile_scale.set_editor_property("R", 1.0 / TILE_WORLD_SIZE)
    scaled_pos = MEL.create_material_expression(material, unreal.MaterialExpressionMultiply, -1600, 0)
    MEL.connect_material_expressions(world_pos, "", scaled_pos, "A")
    MEL.connect_material_expressions(tile_scale, "", scaled_pos, "B")

    mask_yz = MEL.create_material_expression(material, unreal.MaterialExpressionComponentMask, -1400, -300)
    mask_yz.set_editor_property("R", False); mask_yz.set_editor_property("G", True)
    mask_yz.set_editor_property("B", True);  mask_yz.set_editor_property("A", False)
    MEL.connect_material_expressions(scaled_pos, "", mask_yz, "")

    mask_xz = MEL.create_material_expression(material, unreal.MaterialExpressionComponentMask, -1400, 0)
    mask_xz.set_editor_property("R", True);  mask_xz.set_editor_property("G", False)
    mask_xz.set_editor_property("B", True);  mask_xz.set_editor_property("A", False)
    MEL.connect_material_expressions(scaled_pos, "", mask_xz, "")

    mask_xy = MEL.create_material_expression(material, unreal.MaterialExpressionComponentMask, -1400, 300)
    mask_xy.set_editor_property("R", True);  mask_xy.set_editor_property("G", True)
    mask_xy.set_editor_property("B", False); mask_xy.set_editor_property("A", False)
    MEL.connect_material_expressions(scaled_pos, "", mask_xy, "")

    world_normal = MEL.create_material_expression(material, unreal.MaterialExpressionVertexNormalWS, -1400, 600)
    abs_normal = MEL.create_material_expression(material, unreal.MaterialExpressionAbs, -1200, 600)
    MEL.connect_material_expressions(world_normal, "", abs_normal, "")
    sharpness_const = MEL.create_material_expression(material, unreal.MaterialExpressionConstant, -1200, 750)
    sharpness_const.set_editor_property("R", 4.0)
    weight_pow = MEL.create_material_expression(material, unreal.MaterialExpressionPower, -1000, 600)
    MEL.connect_material_expressions(abs_normal, "", weight_pow, "Base")
    MEL.connect_material_expressions(sharpness_const, "", weight_pow, "Exp")

    w_x = MEL.create_material_expression(material, unreal.MaterialExpressionComponentMask, -800, 520)
    w_x.set_editor_property("R", True); w_x.set_editor_property("G", False)
    w_x.set_editor_property("B", False); w_x.set_editor_property("A", False)
    MEL.connect_material_expressions(weight_pow, "", w_x, "")
    w_y = MEL.create_material_expression(material, unreal.MaterialExpressionComponentMask, -800, 600)
    w_y.set_editor_property("R", False); w_y.set_editor_property("G", True)
    w_y.set_editor_property("B", False); w_y.set_editor_property("A", False)
    MEL.connect_material_expressions(weight_pow, "", w_y, "")
    w_z = MEL.create_material_expression(material, unreal.MaterialExpressionComponentMask, -800, 680)
    w_z.set_editor_property("R", False); w_z.set_editor_property("G", False)
    w_z.set_editor_property("B", True); w_z.set_editor_property("A", False)
    MEL.connect_material_expressions(weight_pow, "", w_z, "")

    sum_xy = MEL.create_material_expression(material, unreal.MaterialExpressionAdd, -620, 560)
    MEL.connect_material_expressions(w_x, "", sum_xy, "A")
    MEL.connect_material_expressions(w_y, "", sum_xy, "B")
    sum_xyz = MEL.create_material_expression(material, unreal.MaterialExpressionAdd, -480, 600)
    MEL.connect_material_expressions(sum_xy, "", sum_xyz, "A")
    MEL.connect_material_expressions(w_z, "", sum_xyz, "B")

    norm_x = MEL.create_material_expression(material, unreal.MaterialExpressionDivide, -320, 480)
    MEL.connect_material_expressions(w_x, "", norm_x, "A")
    MEL.connect_material_expressions(sum_xyz, "", norm_x, "B")
    norm_y = MEL.create_material_expression(material, unreal.MaterialExpressionDivide, -320, 600)
    MEL.connect_material_expressions(w_y, "", norm_y, "A")
    MEL.connect_material_expressions(sum_xyz, "", norm_y, "B")
    norm_z = MEL.create_material_expression(material, unreal.MaterialExpressionDivide, -320, 720)
    MEL.connect_material_expressions(w_z, "", norm_z, "A")
    MEL.connect_material_expressions(sum_xyz, "", norm_z, "B")

    def sample_and_blend(tex, out_y, channel="RGB"):
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
        return add_xyz

    raw_stone_color = sample_and_blend(basecolor_tex, 0)
    stone_rough = sample_and_blend(roughness_tex, 1500, channel="R") if roughness_tex else None

    # ---- procedural paver grid (world XY) ----
    grid_xy = MEL.create_material_expression(material, unreal.MaterialExpressionComponentMask, -1600, 1000)
    grid_xy.set_editor_property("R", True); grid_xy.set_editor_property("G", True)
    grid_xy.set_editor_property("B", False); grid_xy.set_editor_property("A", False)
    MEL.connect_material_expressions(world_pos, "", grid_xy, "")

    cell_scale = MEL.create_material_expression(material, unreal.MaterialExpressionConstant, -1600, 1150)
    cell_scale.set_editor_property("R", 1.0 / CELL_SIZE_CM)
    grid_pos = MEL.create_material_expression(material, unreal.MaterialExpressionMultiply, -1400, 1000)
    MEL.connect_material_expressions(grid_xy, "", grid_pos, "A")
    MEL.connect_material_expressions(cell_scale, "", grid_pos, "B")

    frac_grid = MEL.create_material_expression(material, unreal.MaterialExpressionFrac, -1200, 1000)
    MEL.connect_material_expressions(grid_pos, "", frac_grid, "")
    one_minus = MEL.create_material_expression(material, unreal.MaterialExpressionOneMinus, -1200, 1120)
    MEL.connect_material_expressions(frac_grid, "", one_minus, "")
    edge_vec = MEL.create_material_expression(material, unreal.MaterialExpressionMin, -1000, 1060)
    MEL.connect_material_expressions(frac_grid, "", edge_vec, "A")
    MEL.connect_material_expressions(one_minus, "", edge_vec, "B")

    edge_r = MEL.create_material_expression(material, unreal.MaterialExpressionComponentMask, -800, 1000)
    edge_r.set_editor_property("R", True); edge_r.set_editor_property("G", False)
    edge_r.set_editor_property("B", False); edge_r.set_editor_property("A", False)
    MEL.connect_material_expressions(edge_vec, "", edge_r, "")
    edge_g = MEL.create_material_expression(material, unreal.MaterialExpressionComponentMask, -800, 1120)
    edge_g.set_editor_property("R", False); edge_g.set_editor_property("G", True)
    edge_g.set_editor_property("B", False); edge_g.set_editor_property("A", False)
    MEL.connect_material_expressions(edge_vec, "", edge_g, "")
    edge_dist = MEL.create_material_expression(material, unreal.MaterialExpressionMin, -600, 1060)
    MEL.connect_material_expressions(edge_r, "", edge_dist, "A")
    MEL.connect_material_expressions(edge_g, "", edge_dist, "B")

    # ---- per-cell hash (deterministic pseudo-random, classic sin/frac trick) ----
    floor_grid = MEL.create_material_expression(material, unreal.MaterialExpressionFloor, -1000, 1400)
    MEL.connect_material_expressions(grid_pos, "", floor_grid, "")
    hash_dot_const = MEL.create_material_expression(material, unreal.MaterialExpressionConstant2Vector, -1000, 1520)
    hash_dot_const.set_editor_property("R", 12.9898)
    hash_dot_const.set_editor_property("G", 78.233)
    hash_dot = MEL.create_material_expression(material, unreal.MaterialExpressionDotProduct, -800, 1440)
    MEL.connect_material_expressions(floor_grid, "", hash_dot, "A")
    MEL.connect_material_expressions(hash_dot_const, "", hash_dot, "B")
    hash_sin = MEL.create_material_expression(material, unreal.MaterialExpressionSine, -600, 1440)
    MEL.connect_material_expressions(hash_dot, "", hash_sin, "")
    hash_big_const = MEL.create_material_expression(material, unreal.MaterialExpressionConstant, -600, 1560)
    hash_big_const.set_editor_property("R", 43758.5453)
    hash_mul = MEL.create_material_expression(material, unreal.MaterialExpressionMultiply, -400, 1440)
    MEL.connect_material_expressions(hash_sin, "", hash_mul, "A")
    MEL.connect_material_expressions(hash_big_const, "", hash_mul, "B")
    cell_hash = MEL.create_material_expression(material, unreal.MaterialExpressionFrac, -200, 1440)
    MEL.connect_material_expressions(hash_mul, "", cell_hash, "")

    half_const = MEL.create_material_expression(material, unreal.MaterialExpressionConstant, -200, 1560)
    half_const.set_editor_property("R", 0.5)
    hash_centered = MEL.create_material_expression(material, unreal.MaterialExpressionSubtract, 0, 1440)
    MEL.connect_material_expressions(cell_hash, "", hash_centered, "A")
    MEL.connect_material_expressions(half_const, "", hash_centered, "B")

    jitter_const = MEL.create_material_expression(material, unreal.MaterialExpressionConstant, 0, 1560)
    jitter_const.set_editor_property("R", GROUT_JITTER)
    jitter_offset = MEL.create_material_expression(material, unreal.MaterialExpressionMultiply, 200, 1440)
    MEL.connect_material_expressions(hash_centered, "", jitter_offset, "A")
    MEL.connect_material_expressions(jitter_const, "", jitter_offset, "B")

    grout_width_const = MEL.create_material_expression(material, unreal.MaterialExpressionConstant, 200, 1560)
    grout_width_const.set_editor_property("R", GROUT_WIDTH)
    effective_grout_width = MEL.create_material_expression(material, unreal.MaterialExpressionAdd, 400, 1440)
    MEL.connect_material_expressions(grout_width_const, "", effective_grout_width, "A")
    MEL.connect_material_expressions(jitter_offset, "", effective_grout_width, "B")

    sub = MEL.create_material_expression(material, unreal.MaterialExpressionSubtract, -400, 1060)
    MEL.connect_material_expressions(edge_dist, "", sub, "A")
    MEL.connect_material_expressions(effective_grout_width, "", sub, "B")

    softness_const = MEL.create_material_expression(material, unreal.MaterialExpressionConstant, -400, 1200)
    softness_const.set_editor_property("R", GROUT_SOFTNESS)
    div = MEL.create_material_expression(material, unreal.MaterialExpressionDivide, -200, 1060)
    MEL.connect_material_expressions(sub, "", div, "A")
    MEL.connect_material_expressions(softness_const, "", div, "B")

    grout_mask = MEL.create_material_expression(material, unreal.MaterialExpressionClamp, 0, 1060)
    grout_mask.set_editor_property("min_default", 0.0)
    grout_mask.set_editor_property("max_default", 1.0)
    MEL.connect_material_expressions(div, "", grout_mask, "")

    # ---- true grey stone color: luminance-only, recombined with a neutral tint ----
    lum_const = MEL.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, 780, -220)
    lum_const.set_editor_property("constant", unreal.LinearColor(0.299, 0.587, 0.114, 1.0))
    luminance = MEL.create_material_expression(material, unreal.MaterialExpressionDotProduct, 900, -100)
    MEL.connect_material_expressions(raw_stone_color, "", luminance, "A")
    MEL.connect_material_expressions(lum_const, "", luminance, "B")

    bright_jitter_const = MEL.create_material_expression(material, unreal.MaterialExpressionConstant, 900, 20)
    bright_jitter_const.set_editor_property("R", BRIGHTNESS_JITTER)
    bright_offset = MEL.create_material_expression(material, unreal.MaterialExpressionMultiply, 1080, -20)
    MEL.connect_material_expressions(hash_centered, "", bright_offset, "A")
    MEL.connect_material_expressions(bright_jitter_const, "", bright_offset, "B")
    one_const = MEL.create_material_expression(material, unreal.MaterialExpressionConstant, 1080, 100)
    one_const.set_editor_property("R", 1.0)
    bright_mult = MEL.create_material_expression(material, unreal.MaterialExpressionAdd, 1260, -20)
    MEL.connect_material_expressions(one_const, "", bright_mult, "A")
    MEL.connect_material_expressions(bright_offset, "", bright_mult, "B")

    lum_varied = MEL.create_material_expression(material, unreal.MaterialExpressionMultiply, 1440, -100)
    MEL.connect_material_expressions(luminance, "", lum_varied, "A")
    MEL.connect_material_expressions(bright_mult, "", lum_varied, "B")

    tint_const = MEL.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, 1440, 80)
    tint_const.set_editor_property("constant", unreal.LinearColor(STONE_TINT[0], STONE_TINT[1], STONE_TINT[2], 1.0))
    stone_color = MEL.create_material_expression(material, unreal.MaterialExpressionMultiply, 1620, 0)
    MEL.connect_material_expressions(lum_varied, "", stone_color, "A")
    MEL.connect_material_expressions(tint_const, "", stone_color, "B")

    grout_color_const = MEL.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, 1620, 1200)
    grout_color_const.set_editor_property("constant", unreal.LinearColor(GROUT_COLOR[0], GROUT_COLOR[1], GROUT_COLOR[2], 1.0))

    final_color = MEL.create_material_expression(material, unreal.MaterialExpressionLinearInterpolate, 1800, 0)
    MEL.connect_material_expressions(grout_color_const, "", final_color, "A")
    MEL.connect_material_expressions(stone_color, "", final_color, "B")
    MEL.connect_material_expressions(grout_mask, "", final_color, "Alpha")
    MEL.connect_material_property(final_color, "", unreal.MaterialProperty.MP_BASE_COLOR)

    grout_rough_const = MEL.create_material_expression(material, unreal.MaterialExpressionConstant, 1800, 1350)
    grout_rough_const.set_editor_property("R", 1.0)
    if stone_rough is not None:
        final_rough = MEL.create_material_expression(material, unreal.MaterialExpressionLinearInterpolate, 1800, 1500)
        MEL.connect_material_expressions(grout_rough_const, "", final_rough, "A")
        MEL.connect_material_expressions(stone_rough, "", final_rough, "B")
        MEL.connect_material_expressions(grout_mask, "", final_rough, "Alpha")
        MEL.connect_material_property(final_rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    else:
        MEL.connect_material_property(grout_rough_const, "", unreal.MaterialProperty.MP_ROUGHNESS)

    MEL.recompile_material(material)
    log("  done -- %s recompiled." % material.get_name())


def run():
    if not AL.does_asset_exist(PATH_MATERIAL_PATH):
        log("SKIPPED -- %s doesn't exist." % PATH_MATERIAL_PATH)
        return
    path_mat = AL.load_asset(PATH_MATERIAL_PATH)
    albedo = AL.load_asset(MOSS_ALBEDO)
    rough = AL.load_asset(MOSS_ROUGH)
    if not albedo:
        log("SKIPPED -- could not load %s" % MOSS_ALBEDO)
        return
    build_cobblestone(path_mat, albedo, rough)
    log("Path actors already point at this material -- no re-assignment needed. "
        "Save and check the viewport / re-run PIE.")


run()
