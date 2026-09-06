"""
SWAP GROUND TO T_Iceland_Grass -- test whether the base texture's own grain
is what's reading as "streaking", now that the normal-map bug is fixed
================================================================
IRON BREACH / Unreal Engine 5.8

WHY
---
fix_broken_normal_streaking.py removed the broken triplanar normal-map
blend (confirmed: "a little better"). But the two newest screenshots still
show hard, directional dark lines across the ground, converging toward a
point in the distance the way parallel lines always do under perspective
from a low/oblique camera angle. That's the signature of a texture that has
real linear grain baked into its own diffuse map (cracked/eroded dirt photo-
scan textures almost always do), not a shader bug -- and every ground
texture tried so far (Iceland_Eroded, Iceland_Dirt, T_ForestGround) is
exactly that kind of texture: rock/dirt/mud with visible fissures and grain.

T_Iceland_Grass is the one ground-type texture in the project that hasn't
been tried and is a fundamentally different look -- grass/turf textures are
close to isotropic (no single dominant crack direction), so if the
streaking disappears with this swap, that confirms it was always texture
grain, not geometry or shader math. It's also just a better fit for a town
green/garrison yard than eroded mountain dirt.

Keeps everything else identical to the last (working, "a little better")
setup: no normal map, same triplanar blend, same code path -- only the base
texture and its roughness source change, so this is a clean one-variable
test.

HOW TO RUN IT
-------------
    py "X:/IronBreach/Content/Python/try_grass_ground.py"

Safe to re-run.
"""

import unreal

MEL = unreal.MaterialEditingLibrary
AL = unreal.EditorAssetLibrary

GROUND_MATERIAL_PATH = "/Game/LevelPrototyping/AITextures/Landmass/M_AI_MountainGround"
GRASS_BASECOLOR = "/Game/Landscaping/IcelandEnviroment/Textures/T_Iceland_Grass/T_Iceland_Grass_BaseColor"
GRASS_ORM = "/Game/Landscaping/IcelandEnviroment/Textures/T_Iceland_Grass/T_Iceland_Grass_ORM"


def log(msg):
    print("[TryGrassGround] %s" % msg)


def build_triplanar_no_normal(material, basecolor_tex, roughness_tex, roughness_channel,
                               tile_world_size, blend_sharpness=4.0):
    log("Rebuilding %s from T_Iceland_Grass (tile=%.0fcm, NO normal map)..." % (
        material.get_name(), tile_world_size))
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
    # Still no normal map -- isolating the one variable being tested (base texture).

    if roughness_tex:
        sample_and_blend(roughness_tex, 1500, unreal.MaterialProperty.MP_ROUGHNESS, channel=roughness_channel)
    else:
        rough_const = MEL.create_material_expression(material, unreal.MaterialExpressionConstant, 260, 1400)
        rough_const.set_editor_property("R", 0.9)
        MEL.connect_material_property(rough_const, "", unreal.MaterialProperty.MP_ROUGHNESS)

    MEL.recompile_material(material)
    log("  done -- %s recompiled." % material.get_name())


def run():
    if not AL.does_asset_exist(GROUND_MATERIAL_PATH):
        log("SKIPPED -- %s doesn't exist." % GROUND_MATERIAL_PATH)
        return
    ground_mat = AL.load_asset(GROUND_MATERIAL_PATH)
    basecolor = AL.load_asset(GRASS_BASECOLOR)
    orm = AL.load_asset(GRASS_ORM)
    if not basecolor:
        log("SKIPPED -- could not load %s" % GRASS_BASECOLOR)
        return
    # ORM packs roughness in G -- use it directly if present, else fall back to a constant.
    build_triplanar_no_normal(ground_mat, basecolor, orm, "G", tile_world_size=1000.0)
    log("Ground actors already point at this material -- no re-assignment needed. "
        "Save and check the viewport / re-run PIE.")


run()
