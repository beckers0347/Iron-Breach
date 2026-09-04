"""
REBUILD M_AI_GROUND AGAIN -- clean slate, fixed 40m tile size
================================================================
IRON BREACH / Unreal Engine 5.8

The graph had 45 nodes when it should have had ~27 right after the last
rebuild, and changing the tile-scale Constant from R=100 to R=0.00025 (a
400,000x change) produced zero visible difference -- meaning something
got disconnected or duplicated since the last rebuild and Base Color
isn't actually reading our tile-scale chain anymore. Rather than keep
tracing wires that are mostly unreadable via Python anyway, this deletes
EVERYTHING in the graph again and rebuilds it clean, exactly like the
first rebuild, except the tile size is now a fixed, simple number (40m)
instead of computed from the platform's footprint -- so it's guaranteed
correctly wired and it's clear exactly what value produced what look.

HOW TO RUN IT
-------------
    py "X:/IronBreach/Content/Python/rebuild_concrete_material_v2.py"
"""

import unreal

M = 100.0
CONCRETE_MATERIAL_PATH = "/Game/LevelPrototyping/AITextures/M_AI_Ground.M_AI_Ground"
CONCRETE_TEXTURE_PATH = "/Game/LevelPrototyping/AITextures/T_Ground_Concrete.T_Ground_Concrete"
TILE_SIZE_METERS = 40.0

MEL = unreal.MaterialEditingLibrary
AL = unreal.EditorAssetLibrary


def log(msg):
    print("[RebuildConcreteMaterialV2] %s" % msg)


def build_triplanar_basecolor_only(material, basecolor_tex, tile_world_size, roughness_const=0.85):
    log("Wiping graph clean (%d node(s) currently)..." % len(MEL.get_material_expressions(material)))
    MEL.delete_all_material_expressions(material)
    log("Rebuilding %s (tile=%.0fcm / %.1fm)..." % (material.get_name(), tile_world_size, tile_world_size / M))

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

    tx = MEL.create_material_expression(material, unreal.MaterialExpressionTextureSample, 0, -200)
    tx.set_editor_property("texture", basecolor_tex)
    MEL.connect_material_expressions(mask_yz, "", tx, "Coordinates")
    ty = MEL.create_material_expression(material, unreal.MaterialExpressionTextureSample, 0, 0)
    ty.set_editor_property("texture", basecolor_tex)
    MEL.connect_material_expressions(mask_xz, "", ty, "Coordinates")
    tz = MEL.create_material_expression(material, unreal.MaterialExpressionTextureSample, 0, 200)
    tz.set_editor_property("texture", basecolor_tex)
    MEL.connect_material_expressions(mask_xy, "", tz, "Coordinates")

    mul_x = MEL.create_material_expression(material, unreal.MaterialExpressionMultiply, 260, -200)
    MEL.connect_material_expressions(tx, "RGB", mul_x, "A")
    MEL.connect_material_expressions(norm_x, "", mul_x, "B")
    mul_y = MEL.create_material_expression(material, unreal.MaterialExpressionMultiply, 260, 0)
    MEL.connect_material_expressions(ty, "RGB", mul_y, "A")
    MEL.connect_material_expressions(norm_y, "", mul_y, "B")
    mul_z = MEL.create_material_expression(material, unreal.MaterialExpressionMultiply, 260, 200)
    MEL.connect_material_expressions(tz, "RGB", mul_z, "A")
    MEL.connect_material_expressions(norm_z, "", mul_z, "B")

    add_xy = MEL.create_material_expression(material, unreal.MaterialExpressionAdd, 480, -100)
    MEL.connect_material_expressions(mul_x, "", add_xy, "A")
    MEL.connect_material_expressions(mul_y, "", add_xy, "B")
    add_xyz = MEL.create_material_expression(material, unreal.MaterialExpressionAdd, 640, 0)
    MEL.connect_material_expressions(add_xy, "", add_xyz, "A")
    MEL.connect_material_expressions(mul_z, "", add_xyz, "B")

    ok1 = MEL.connect_material_property(add_xyz, "", unreal.MaterialProperty.MP_BASE_COLOR)
    log("  connect_material_property(BaseColor) returned: %s" % ok1)

    rough_const = MEL.create_material_expression(material, unreal.MaterialExpressionConstant, 260, 1400)
    rough_const.set_editor_property("R", roughness_const)
    ok2 = MEL.connect_material_property(rough_const, "", unreal.MaterialProperty.MP_ROUGHNESS)
    log("  connect_material_property(Roughness) returned: %s" % ok2)

    MEL.recompile_material(material)
    final_count = len(MEL.get_material_expressions(material))
    log("  done -- %s recompiled. Graph now has %d node(s) (should be ~27)." % (material.get_name(), final_count))


def run():
    material = AL.load_asset(CONCRETE_MATERIAL_PATH)
    if material is None:
        log("ABORTED -- %s not found." % CONCRETE_MATERIAL_PATH)
        return

    texture = AL.load_asset(CONCRETE_TEXTURE_PATH)
    if texture is None:
        log("ABORTED -- %s not found." % CONCRETE_TEXTURE_PATH)
        return

    build_triplanar_basecolor_only(material, texture, TILE_SIZE_METERS * M, roughness_const=0.85)
    log("Done. Save, then take a fresh look.")


run()
