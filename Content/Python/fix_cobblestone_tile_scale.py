"""
FIX STRETCHED PATH TEXTURE -- shrink the cobblestone tile size
================================================================
IRON BREACH / Unreal Engine 5.8

WHY
---
M_AI_CobblestonePath is triplanar (world-position based), so it can't
stretch from an actor's own scale the way a UV-mapped material would --
but TILE_WORLD_SIZE=200cm means each repeat of the generated stone image
spans a full 2m of world space. Roads are only 6-8m wide (ROAD_WIDTH=6m,
STREET_WIDTH=8m), so at that tile size only 3-4 repeats ever show across
the width of a road -- each paver in the source image gets blown up to a
huge, blurry, "stretched" size instead of reading as a normal hand-sized
paving stone.

THE FIX
-------
Rebuild M_AI_CobblestonePath with a much smaller tile -- 200cm -> 90cm --
so the stone pattern repeats at a scale that actually looks like
individual pavers on a road this wide, not one giant smear. Same clean
delete-and-verify-empty approach as clean_rebuild_cobblestone_path.py, no
normal map, flat roughness.

HOW TO RUN IT
-------------
    py "X:/IronBreach/Content/Python/fix_cobblestone_tile_scale.py"
"""

import unreal

MEL = unreal.MaterialEditingLibrary
AL = unreal.EditorAssetLibrary

TEXTURE_PATH = "/Game/Landscaping/IcelandEnviroment/Textures/T_TripoCobblestone/T_TripoCobblestone_A"
PATH_MATERIAL_PATH = "/Game/LevelPrototyping/AITextures/Landmass/M_AI_CobblestonePath"
TILE_WORLD_SIZE = 90.0   # cm -- was 200cm
ROUGHNESS = 0.85


def log(msg):
    print("[FixCobblestoneTileScale] %s" % msg)


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
    if not AL.does_asset_exist(TEXTURE_PATH) or not AL.does_asset_exist(PATH_MATERIAL_PATH):
        log("ABORTED -- material or texture asset missing.")
        return
    tex = AL.load_asset(TEXTURE_PATH)
    mat = AL.load_asset(PATH_MATERIAL_PATH)

    for attempt in range(2):
        MEL.delete_all_material_expressions(mat)
        remaining = MEL.get_material_expressions(mat)
        if not remaining:
            break
        log("Attempt %d: %d expression(s) still present after delete -- retrying." % (attempt + 1, len(remaining)))

    build(mat, tex)
    MEL.recompile_material(mat)
    AL.save_asset(PATH_MATERIAL_PATH)
    log("Rebuilt %s at tile=%.0fcm (was 200cm). Save and check the viewport / re-run PIE." % (
        mat.get_name(), TILE_WORLD_SIZE))


run()
