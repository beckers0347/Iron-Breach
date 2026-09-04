"""
REBUILD M_AI_GROUND FROM SCRATCH -- clean triplanar setup, one controllable
tile size, matches the proven pattern already used for every other ground
material in this project (M_AI_MountainGround, M_AI_CobblestonePath)
================================================================
IRON BREACH / Unreal Engine 5.8

WHY A REBUILD INSTEAD OF ANOTHER IN-PLACE EDIT
------------------------------------------------
Confirmed by the last two diagnostics: M_AI_Ground's existing graph has 3
separate tile-scale-shaped Constant nodes and its expression-input pins
are flat-out unreadable from Python in this engine build ("protected and
cannot be read" on every A/B/Input/Coordinates pin) -- there's no reliable
way to trace or edit its current wiring in place. Unlike
M_AI_MountainGround, M_AI_CobblestonePath, etc. (all of which this
project's own scripts already rebuild this exact way whenever their
tiling needs fixing), M_AI_Ground was apparently hand-built directly in
the Material Editor and never went through that scripted path -- which is
also probably why it ended up with redundant/inconsistent tile-scale
nodes in the first place.

Rather than guess at a 4th unreadable structure, this deletes every node
in M_AI_Ground and rebuilds it clean: triplanar (world-position based, so
it can't stretch regardless of the actor's own scale -- same reason this
technique was used for the cobblestone/mountain materials), ONE tile-scale
constant this time, base color from T_Ground_Concrete (the only texture
this material ever used -- no normal/roughness map exists for it, so
roughness goes back to a plain 0.85 constant same as the last fix,
Metallic/Specular left at the engine's normal defaults, not shiny).

Tile size this time is set to ~2 repeats across the platform's longer
side -- Shane asked for "one solid piece," so this leans toward almost no
visible seam while still keeping SOME real texture repetition (a true
single repeat stretches the source photo enough to look soft/blurry up
close -- see the earlier note). Tell me if it should go all the way to 1
repeat instead, or back off to more repeats for sharper close-up detail.

M_AI_Ground is shared by the other pads (Vehicle Bay, Parade Yard, etc)
same as before -- this changes their tiling too, toward fewer, bigger
repeats, which won't introduce new seams there (they were already smaller
than one old tile).

HOW TO RUN IT
-------------
    py "X:/IronBreach/Content/Python/rebuild_concrete_material.py"
"""

import unreal

M = 100.0
CONCRETE_MATERIAL_PATH = "/Game/LevelPrototyping/AITextures/M_AI_Ground.M_AI_Ground"
CONCRETE_TEXTURE_PATH = "/Game/LevelPrototyping/AITextures/T_Ground_Concrete.T_Ground_Concrete"
TARGET_REPEATS_ACROSS_LONG_SIDE = 2.0
FALLBACK_TILE_WORLD_SIZE = 3000.0  # used only if the platform can't be found/measured

MEL = unreal.MaterialEditingLibrary
AL = unreal.EditorAssetLibrary
actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def log(msg):
    print("[RebuildConcreteMaterial] %s" % msg)


def build_triplanar_basecolor_only(material, basecolor_tex, tile_world_size, roughness_const=0.85):
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

    MEL.connect_material_property(add_xyz, "", unreal.MaterialProperty.MP_BASE_COLOR)

    rough_const = MEL.create_material_expression(material, unreal.MaterialExpressionConstant, 260, 1400)
    rough_const.set_editor_property("R", roughness_const)
    MEL.connect_material_property(rough_const, "", unreal.MaterialProperty.MP_ROUGHNESS)

    MEL.recompile_material(material)
    log("  done -- %s recompiled." % material.get_name())


def run():
    material = AL.load_asset(CONCRETE_MATERIAL_PATH)
    if material is None:
        log("ABORTED -- %s not found." % CONCRETE_MATERIAL_PATH)
        return

    texture = AL.load_asset(CONCRETE_TEXTURE_PATH)
    if texture is None:
        log("ABORTED -- %s not found." % CONCRETE_TEXTURE_PATH)
        return

    tile_world_size = FALLBACK_TILE_WORLD_SIZE
    for a in actor_subsystem.get_all_level_actors():
        if a.get_actor_label() == "GarrisonPlatform_New":
            origin, extent = a.get_actor_bounds(False)
            long_side_cm = max(extent.x * 2.0, extent.y * 2.0)
            tile_world_size = long_side_cm / TARGET_REPEATS_ACROSS_LONG_SIDE
            log("Platform's real footprint long side: %.0fm -> tile size %.0fcm (%.0fm) for "
                "~%.0f repeats." % (long_side_cm / M, tile_world_size, tile_world_size / M,
                                     TARGET_REPEATS_ACROSS_LONG_SIDE))
            break
    else:
        log("GarrisonPlatform_New not found -- using fallback tile size %.0fcm." % FALLBACK_TILE_WORLD_SIZE)

    build_triplanar_basecolor_only(material, texture, tile_world_size, roughness_const=0.85)
    log("Done. Save and take a look.")


run()
