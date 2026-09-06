"""
FIX GARRISON GROUND -- stop the platform reading as "random square tiles"
================================================================
IRON BREACH / Unreal Engine 5.8

WHY
---
Checked M_AI_Ground's material graph (it's built by polish_garrison_materials.py's
build_triplanar_basecolor() helper): it's ALREADY correctly triplanar/world-aligned,
same proven pattern as the grass ground and cobblestone path -- so this is not a
broken-UV bug like the earlier streaking issues.

The garrison platform is enormous (built from many overlapping Ground_* slabs,
see build_carrowgate_garrison.py), and T_Ground_Concrete was tiled at 768cm.
On a surface that large, a 768cm repeat means the texture's own panel/joint
lines repeat MANY times across the platform -- which is very likely exactly
what's reading as "a bunch of random square texture tiles" instead of one
continuous slab: each repeat looks like its own separate physical tile.

THE FIX (what I can do without a new texture)
-----------------------------------------------
Rebuild M_AI_Ground with a much larger tile size (768cm -> 2400cm, ~3x), so
the same texture repeats far less often across the platform's footprint and
reads more like one continuous surface with subtle grain rather than an
obvious tile grid. Same no-normal-map triplanar approach already proven not
to streak. Roughness unchanged.

HONEST LIMIT: if T_Ground_Concrete's own imagery is a very literal
slab/joint pattern (not just fine surface grain), a bigger tile size
reduces how often that pattern repeats but can't fully remove the "distinct
panels" look -- the real fix there would be swapping in a texture with
finer, less-panelled grain (e.g. a proper worn-concrete or steel-platform
image generated the same way the cobblestone was). I couldn't generate one
this pass because the Chrome connection to Tripo3D dropped -- flagging that
rather than silently skipping it.

HOW TO RUN IT
-------------
    py "X:/IronBreach/Content/Python/fix_garrison_ground_scale.py"
"""

import unreal

MEL = unreal.MaterialEditingLibrary
AL = unreal.EditorAssetLibrary

GROUND_MATERIAL_PATH = "/Game/LevelPrototyping/AITextures/M_AI_Ground"
GROUND_TEXTURE_PATH = "/Game/LevelPrototyping/AITextures/T_Ground_Concrete"
TILE_WORLD_SIZE = 2400.0   # cm -- was 768cm, ~3x larger repeat spacing
ROUGHNESS = 0.8


def log(msg):
    print("[FixGarrisonGroundScale] %s" % msg)


def build(material, tex):
    MEL.delete_all_material_expressions(material)

    world_pos = MEL.create_material_expression(material, unreal.MaterialExpressionWorldPosition, -1600, 0)
    tile_scale = MEL.create_material_expression(material, unreal.MaterialExpressionConstant, -1600, 150)
    tile_scale.set_editor_property("R", 1.0 / TILE_WORLD_SIZE)
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

    def sample_and_blend(t, out_y, prop):
        tx = MEL.create_material_expression(material, unreal.MaterialExpressionTextureSample, 0, out_y - 200)
        tx.set_editor_property("texture", t)
        MEL.connect_material_expressions(mask_yz, "", tx, "Coordinates")
        ty = MEL.create_material_expression(material, unreal.MaterialExpressionTextureSample, 0, out_y)
        ty.set_editor_property("texture", t)
        MEL.connect_material_expressions(mask_xz, "", ty, "Coordinates")
        tz = MEL.create_material_expression(material, unreal.MaterialExpressionTextureSample, 0, out_y + 200)
        tz.set_editor_property("texture", t)
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

    sample_and_blend(tex, 0, unreal.MaterialProperty.MP_BASE_COLOR)
    rough_const = MEL.create_material_expression(material, unreal.MaterialExpressionConstant, 260, 1400)
    rough_const.set_editor_property("R", ROUGHNESS)
    MEL.connect_material_property(rough_const, "", unreal.MaterialProperty.MP_ROUGHNESS)


def run():
    if not AL.does_asset_exist(GROUND_MATERIAL_PATH) or not AL.does_asset_exist(GROUND_TEXTURE_PATH):
        log("ABORTED -- material or texture asset missing.")
        return
    mat = AL.load_asset(GROUND_MATERIAL_PATH)
    tex = AL.load_asset(GROUND_TEXTURE_PATH)

    build(mat, tex)
    MEL.recompile_material(mat)
    AL.save_asset(GROUND_MATERIAL_PATH)
    log("Rebuilt %s at tile=%.0fcm (was 768cm). Save and check the viewport / re-run PIE." % (
        mat.get_name(), TILE_WORLD_SIZE))


run()
