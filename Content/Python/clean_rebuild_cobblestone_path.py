"""
CLEAN REBUILD OF M_AI_COBBLESTONEPATH -- verified empty before rebuilding
================================================================
IRON BREACH / Unreal Engine 5.8

WHY
---
diagnose_texture_and_mystery_material.py found M_AI_CobblestonePath's
graph still had 6 leftover T_MossyCreekStones TextureSample nodes sitting
alongside the 3 new T_TripoCobblestone_A ones -- delete_all_material_expressions
didn't fully clear the graph before the last rebuild, leaving it in a mixed
state. That's the likely reason the path still reads wrong/flat in the
viewport even though the new texture is technically present somewhere in
the graph.

This deletes everything, explicitly VERIFIES the graph is actually empty
(logs a warning and retries once if not) before rebuilding clean with only
T_TripoCobblestone_A -- same plain triplanar basecolor-only approach as
before (no normal map, flat roughness).

HOW TO RUN IT
-------------
    py "X:/IronBreach/Content/Python/clean_rebuild_cobblestone_path.py"
"""

import unreal

MEL = unreal.MaterialEditingLibrary
AL = unreal.EditorAssetLibrary

TEXTURE_PATH = "/Game/Landscaping/IcelandEnviroment/Textures/T_TripoCobblestone/T_TripoCobblestone_A"
PATH_MATERIAL_PATH = "/Game/LevelPrototyping/AITextures/Landmass/M_AI_CobblestonePath"
TILE_WORLD_SIZE = 200.0
ROUGHNESS = 0.85


def log(msg):
    print("[CleanRebuildCobblestone] %s" % msg)


def build(mat, tex):
    world_pos = MEL.create_material_expression(mat, unreal.MaterialExpressionWorldPosition, -1600, 0)
    tile_scale = MEL.create_material_expression(mat, unreal.MaterialExpressionConstant, -1600, 150)
    tile_scale.set_editor_property("R", 1.0 / TILE_WORLD_SIZE)
    scaled_pos = MEL.create_material_expression(mat, unreal.MaterialExpressionMultiply, -1400, 0)
    MEL.connect_material_expressions(world_pos, "", scaled_pos, "A")
    MEL.connect_material_expressions(tile_scale, "", scaled_pos, "B")

    mask_yz = MEL.create_material_expression(mat, unreal.MaterialExpressionComponentMask, -1200, -300)
    mask_yz.set_editor_property("R", False); mask_yz.set_editor_property("G", True)
    mask_yz.set_editor_property("B", True);  mask_yz.set_editor_property("A", False)
    MEL.connect_material_expressions(scaled_pos, "", mask_yz, "")

    mask_xz = MEL.create_material_expression(mat, unreal.MaterialExpressionComponentMask, -1200, 0)
    mask_xz.set_editor_property("R", True);  mask_xz.set_editor_property("G", False)
    mask_xz.set_editor_property("B", True);  mask_xz.set_editor_property("A", False)
    MEL.connect_material_expressions(scaled_pos, "", mask_xz, "")

    mask_xy = MEL.create_material_expression(mat, unreal.MaterialExpressionComponentMask, -1200, 300)
    mask_xy.set_editor_property("R", True);  mask_xy.set_editor_property("G", True)
    mask_xy.set_editor_property("B", False); mask_xy.set_editor_property("A", False)
    MEL.connect_material_expressions(scaled_pos, "", mask_xy, "")

    world_normal = MEL.create_material_expression(mat, unreal.MaterialExpressionVertexNormalWS, -1200, 600)
    abs_normal = MEL.create_material_expression(mat, unreal.MaterialExpressionAbs, -1000, 600)
    MEL.connect_material_expressions(world_normal, "", abs_normal, "")
    sharpness_const = MEL.create_material_expression(mat, unreal.MaterialExpressionConstant, -1000, 750)
    sharpness_const.set_editor_property("R", 4.0)
    weight_pow = MEL.create_material_expression(mat, unreal.MaterialExpressionPower, -800, 600)
    MEL.connect_material_expressions(abs_normal, "", weight_pow, "Base")
    MEL.connect_material_expressions(sharpness_const, "", weight_pow, "Exp")

    w_x = MEL.create_material_expression(mat, unreal.MaterialExpressionComponentMask, -600, 520)
    w_x.set_editor_property("R", True); w_x.set_editor_property("G", False)
    w_x.set_editor_property("B", False); w_x.set_editor_property("A", False)
    MEL.connect_material_expressions(weight_pow, "", w_x, "")
    w_y = MEL.create_material_expression(mat, unreal.MaterialExpressionComponentMask, -600, 600)
    w_y.set_editor_property("R", False); w_y.set_editor_property("G", True)
    w_y.set_editor_property("B", False); w_y.set_editor_property("A", False)
    MEL.connect_material_expressions(weight_pow, "", w_y, "")
    w_z = MEL.create_material_expression(mat, unreal.MaterialExpressionComponentMask, -600, 680)
    w_z.set_editor_property("R", False); w_z.set_editor_property("G", False)
    w_z.set_editor_property("B", True); w_z.set_editor_property("A", False)
    MEL.connect_material_expressions(weight_pow, "", w_z, "")

    sum_xy = MEL.create_material_expression(mat, unreal.MaterialExpressionAdd, -420, 560)
    MEL.connect_material_expressions(w_x, "", sum_xy, "A")
    MEL.connect_material_expressions(w_y, "", sum_xy, "B")
    sum_xyz = MEL.create_material_expression(mat, unreal.MaterialExpressionAdd, -280, 600)
    MEL.connect_material_expressions(sum_xy, "", sum_xyz, "A")
    MEL.connect_material_expressions(w_z, "", sum_xyz, "B")

    norm_x = MEL.create_material_expression(mat, unreal.MaterialExpressionDivide, -120, 480)
    MEL.connect_material_expressions(w_x, "", norm_x, "A")
    MEL.connect_material_expressions(sum_xyz, "", norm_x, "B")
    norm_y = MEL.create_material_expression(mat, unreal.MaterialExpressionDivide, -120, 600)
    MEL.connect_material_expressions(w_y, "", norm_y, "A")
    MEL.connect_material_expressions(sum_xyz, "", norm_y, "B")
    norm_z = MEL.create_material_expression(mat, unreal.MaterialExpressionDivide, -120, 720)
    MEL.connect_material_expressions(w_z, "", norm_z, "A")
    MEL.connect_material_expressions(sum_xyz, "", norm_z, "B")

    def sample_and_blend(t, out_y, prop):
        tx = MEL.create_material_expression(mat, unreal.MaterialExpressionTextureSample, 0, out_y - 200)
        tx.set_editor_property("texture", t)
        MEL.connect_material_expressions(mask_yz, "", tx, "Coordinates")
        ty = MEL.create_material_expression(mat, unreal.MaterialExpressionTextureSample, 0, out_y)
        ty.set_editor_property("texture", t)
        MEL.connect_material_expressions(mask_xz, "", ty, "Coordinates")
        tz = MEL.create_material_expression(mat, unreal.MaterialExpressionTextureSample, 0, out_y + 200)
        tz.set_editor_property("texture", t)
        MEL.connect_material_expressions(mask_xy, "", tz, "Coordinates")

        mul_x = MEL.create_material_expression(mat, unreal.MaterialExpressionMultiply, 260, out_y - 200)
        MEL.connect_material_expressions(tx, "RGB", mul_x, "A")
        MEL.connect_material_expressions(norm_x, "", mul_x, "B")
        mul_y = MEL.create_material_expression(mat, unreal.MaterialExpressionMultiply, 260, out_y)
        MEL.connect_material_expressions(ty, "RGB", mul_y, "A")
        MEL.connect_material_expressions(norm_y, "", mul_y, "B")
        mul_z = MEL.create_material_expression(mat, unreal.MaterialExpressionMultiply, 260, out_y + 200)
        MEL.connect_material_expressions(tz, "RGB", mul_z, "A")
        MEL.connect_material_expressions(norm_z, "", mul_z, "B")

        add_xy = MEL.create_material_expression(mat, unreal.MaterialExpressionAdd, 480, out_y - 100)
        MEL.connect_material_expressions(mul_x, "", add_xy, "A")
        MEL.connect_material_expressions(mul_y, "", add_xy, "B")
        add_xyz = MEL.create_material_expression(mat, unreal.MaterialExpressionAdd, 640, out_y)
        MEL.connect_material_expressions(add_xy, "", add_xyz, "A")
        MEL.connect_material_expressions(mul_z, "", add_xyz, "B")
        MEL.connect_material_property(add_xyz, "", prop)

    sample_and_blend(tex, 0, unreal.MaterialProperty.MP_BASE_COLOR)
    rough_const = MEL.create_material_expression(mat, unreal.MaterialExpressionConstant, 260, 1400)
    rough_const.set_editor_property("R", ROUGHNESS)
    MEL.connect_material_property(rough_const, "", unreal.MaterialProperty.MP_ROUGHNESS)


def run():
    if not AL.does_asset_exist(TEXTURE_PATH):
        log("SKIPPED -- %s doesn't exist." % TEXTURE_PATH)
        return
    if not AL.does_asset_exist(PATH_MATERIAL_PATH):
        log("SKIPPED -- %s doesn't exist." % PATH_MATERIAL_PATH)
        return
    tex = AL.load_asset(TEXTURE_PATH)
    mat = AL.load_asset(PATH_MATERIAL_PATH)

    for attempt in range(2):
        MEL.delete_all_material_expressions(mat)
        remaining = MEL.get_material_expressions(mat)
        if not remaining:
            break
        log("Attempt %d: %d expression(s) still present after delete -- retrying." % (attempt + 1, len(remaining)))
    else:
        log("WARNING: graph still not empty after 2 delete attempts -- rebuilding on top anyway, "
            "but tell me if this keeps happening.")

    build(mat, tex)
    MEL.recompile_material(mat)
    AL.save_asset(PATH_MATERIAL_PATH)

    final_exprs = MEL.get_material_expressions(mat)
    tex_names = [e.get_editor_property("texture").get_name() for e in final_exprs
                 if isinstance(e, unreal.MaterialExpressionTextureSample) and e.get_editor_property("texture")]
    log("Rebuilt clean. Final graph has %d expression(s), textures referenced: %s" % (
        len(final_exprs), tex_names))
    log("Save and check the viewport / re-run PIE.")


run()
