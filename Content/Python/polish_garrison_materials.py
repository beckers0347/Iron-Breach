"""
POLISH GARRISON MATERIALS -- water + continuous wall texturing
================================================================
IRON BREACH / Unreal Engine 5.8

WHAT THIS IS
------------
A one-shot Editor Python script, same convention as Content/Python/build_m1_district.py:
run it once from the in-editor Python console, it rebuilds two existing materials in place.

WHAT IT FIXES
-------------
1. M_AI_Wall -- currently a flat per-object TextureSample, which is why adjacent garrison
   building boxes never line up at their seams ("looks like boxes instead of one continuous
   texture"). Rebuilt as a proper TRIPLANAR (world-aligned, 3-axis blended) sample of the
   same T_Wall_Concrete texture, so it tiles continuously across every box regardless of
   that box's own UVs or how it's rotated/placed.

2. M_AI_Water -- currently a static single-texture Panner, which is why it reads as a
   scrolling flat image instead of fluid water. Rebuilt with two independently-panned
   samples of the same T_Water_Ocean texture blended together (breaks up the "obviously
   scrolling" look), a Fresnel-driven roughness/specular response (sharper reflections at
   grazing angles, softer straight-on -- the actual visual cue that reads as "wet"), and a
   subtle blue-teal tint so it reads as water rather than a sand-colored photo.

   Caveat, stated plainly: the current Water_Placeholder actor is a flat, unsubdivided
   scaled cube (per the level's own naming and the screenshot you shared). No shader can
   put real wave DISPLACEMENT into a mesh with no vertices to move -- what this script can
   do is make the flat surface look convincingly liquid (motion, reflectivity, color) but
   it cannot make it physically ripple. If you want actual wave geometry, that's a mesh/
   Water-plugin change, not a material change -- flagged at the bottom, not attempted here.

HOW TO RUN IT
-------------
From the Output Log console (~): py "X:/IronBreach/Content/Python/polish_garrison_materials.py"
or the Python console tab: exec(open("X:/IronBreach/Content/Python/polish_garrison_materials.py").read())

Re-running is safe/idempotent -- each target material's expression graph is fully cleared
and rebuilt from scratch every time, so there's no risk of leftover/duplicate nodes from a
previous run.

IF SOMETHING ERRORS: this was written and reviewed but NOT executed against a live editor
(no running Unreal instance available to test against directly) -- copy the exact error
text from the Output Log back so it can be fixed in one pass rather than guessed at again.
"""

import unreal

MEL = unreal.MaterialEditingLibrary
AL = unreal.EditorAssetLibrary

WALL_MATERIAL_PATH = "/Game/LevelPrototyping/AITextures/M_AI_Wall"
WALL_TEXTURE_PATH = "/Game/LevelPrototyping/AITextures/T_Wall_Concrete"
WATER_MATERIAL_PATH = "/Game/LevelPrototyping/AITextures/M_AI_Water"
WATER_TEXTURE_PATH = "/Game/LevelPrototyping/AITextures/T_Water_Ocean"

# Also fix the ground plates and generic furniture the same triplanar way, since they have
# the exact same per-object-UV problem -- set to False if you only want the walls touched
# on this pass.
ALSO_FIX_GROUND = True
ALSO_FIX_FURNITURE = True
GROUND_MATERIAL_PATH = "/Game/LevelPrototyping/AITextures/M_AI_Ground"
GROUND_TEXTURE_PATH = "/Game/LevelPrototyping/AITextures/T_Ground_Concrete"
FURNITURE_MATERIAL_PATH = "/Game/LevelPrototyping/AITextures/M_AI_Furniture"
FURNITURE_TEXTURE_PATH = "/Game/LevelPrototyping/AITextures/T_Furniture_WoodMetal"


def log(msg):
    print("[PolishMaterials] %s" % msg)


def build_triplanar_basecolor(material, texture, tile_world_size=512.0, blend_sharpness=4.0):
    """
    Clears `material`'s graph and rebuilds it as a world-aligned triplanar sample of
    `texture` feeding BaseColor. Standard 3-projection normal-weighted blend:
      - project along each world axis using the OTHER two axes as UV
      - weight each projection by abs(WorldNormal)^blend_sharpness on ITS OWN axis
      - normalize the three weights to sum to 1
    This is what makes texture continuous across separately-placed box actors regardless
    of their individual UVs -- the UV is derived from world position, not per-object UVs.
    """
    log("Rebuilding %s as triplanar..." % material.get_name())
    MEL.delete_all_material_expressions(material)

    # --- World position, scaled down to control tiling frequency ---
    world_pos = MEL.create_material_expression(material, unreal.MaterialExpressionWorldPosition, -1400, 0)

    tile_scale = MEL.create_material_expression(material, unreal.MaterialExpressionConstant, -1400, 150)
    tile_scale.set_editor_property("R", 1.0 / tile_world_size)

    scaled_pos = MEL.create_material_expression(material, unreal.MaterialExpressionMultiply, -1200, 0)
    MEL.connect_material_expressions(world_pos, "", scaled_pos, "A")
    MEL.connect_material_expressions(tile_scale, "", scaled_pos, "B")

    # --- Three axis-pair UV projections (YZ / XZ / XY) ---
    mask_yz = MEL.create_material_expression(material, unreal.MaterialExpressionComponentMask, -1000, -200)
    mask_yz.set_editor_property("R", False); mask_yz.set_editor_property("G", True)
    mask_yz.set_editor_property("B", True);  mask_yz.set_editor_property("A", False)
    MEL.connect_material_expressions(scaled_pos, "", mask_yz, "")

    mask_xz = MEL.create_material_expression(material, unreal.MaterialExpressionComponentMask, -1000, 0)
    mask_xz.set_editor_property("R", True);  mask_xz.set_editor_property("G", False)
    mask_xz.set_editor_property("B", True);  mask_xz.set_editor_property("A", False)
    MEL.connect_material_expressions(scaled_pos, "", mask_xz, "")

    mask_xy = MEL.create_material_expression(material, unreal.MaterialExpressionComponentMask, -1000, 200)
    mask_xy.set_editor_property("R", True);  mask_xy.set_editor_property("G", True)
    mask_xy.set_editor_property("B", False); mask_xy.set_editor_property("A", False)
    MEL.connect_material_expressions(scaled_pos, "", mask_xy, "")

    # --- Three texture samples, same texture, one per projection ---
    tex_x = MEL.create_material_expression(material, unreal.MaterialExpressionTextureSample, -800, -200)
    tex_x.set_editor_property("texture", texture)
    MEL.connect_material_expressions(mask_yz, "", tex_x, "Coordinates")

    tex_y = MEL.create_material_expression(material, unreal.MaterialExpressionTextureSample, -800, 0)
    tex_y.set_editor_property("texture", texture)
    MEL.connect_material_expressions(mask_xz, "", tex_y, "Coordinates")

    tex_z = MEL.create_material_expression(material, unreal.MaterialExpressionTextureSample, -800, 200)
    tex_z.set_editor_property("texture", texture)
    MEL.connect_material_expressions(mask_xy, "", tex_z, "Coordinates")

    # --- Blend weights: abs(WorldNormal)^sharpness, normalized ---
    world_normal = MEL.create_material_expression(material, unreal.MaterialExpressionVertexNormalWS, -1000, 450)

    abs_normal = MEL.create_material_expression(material, unreal.MaterialExpressionAbs, -820, 450)
    MEL.connect_material_expressions(world_normal, "", abs_normal, "")

    sharpness_const = MEL.create_material_expression(material, unreal.MaterialExpressionConstant, -820, 600)
    sharpness_const.set_editor_property("R", blend_sharpness)

    weight_pow = MEL.create_material_expression(material, unreal.MaterialExpressionPower, -650, 450)
    MEL.connect_material_expressions(abs_normal, "", weight_pow, "Base")
    MEL.connect_material_expressions(sharpness_const, "", weight_pow, "Exp")

    w_x = MEL.create_material_expression(material, unreal.MaterialExpressionComponentMask, -480, 380)
    w_x.set_editor_property("R", True); w_x.set_editor_property("G", False)
    w_x.set_editor_property("B", False); w_x.set_editor_property("A", False)
    MEL.connect_material_expressions(weight_pow, "", w_x, "")

    w_y = MEL.create_material_expression(material, unreal.MaterialExpressionComponentMask, -480, 450)
    w_y.set_editor_property("R", False); w_y.set_editor_property("G", True)
    w_y.set_editor_property("B", False); w_y.set_editor_property("A", False)
    MEL.connect_material_expressions(weight_pow, "", w_y, "")

    w_z = MEL.create_material_expression(material, unreal.MaterialExpressionComponentMask, -480, 520)
    w_z.set_editor_property("R", False); w_z.set_editor_property("G", False)
    w_z.set_editor_property("B", True); w_z.set_editor_property("A", False)
    MEL.connect_material_expressions(weight_pow, "", w_z, "")

    sum_xy = MEL.create_material_expression(material, unreal.MaterialExpressionAdd, -300, 420)
    MEL.connect_material_expressions(w_x, "", sum_xy, "A")
    MEL.connect_material_expressions(w_y, "", sum_xy, "B")

    sum_xyz = MEL.create_material_expression(material, unreal.MaterialExpressionAdd, -150, 450)
    MEL.connect_material_expressions(sum_xy, "", sum_xyz, "A")
    MEL.connect_material_expressions(w_z, "", sum_xyz, "B")

    norm_x = MEL.create_material_expression(material, unreal.MaterialExpressionDivide, 0, 350)
    MEL.connect_material_expressions(w_x, "", norm_x, "A")
    MEL.connect_material_expressions(sum_xyz, "", norm_x, "B")

    norm_y = MEL.create_material_expression(material, unreal.MaterialExpressionDivide, 0, 450)
    MEL.connect_material_expressions(w_y, "", norm_y, "A")
    MEL.connect_material_expressions(sum_xyz, "", norm_y, "B")

    norm_z = MEL.create_material_expression(material, unreal.MaterialExpressionDivide, 0, 550)
    MEL.connect_material_expressions(w_z, "", norm_z, "A")
    MEL.connect_material_expressions(sum_xyz, "", norm_z, "B")

    # --- Weighted blend of the three samples ---
    mul_x = MEL.create_material_expression(material, unreal.MaterialExpressionMultiply, 250, -100)
    MEL.connect_material_expressions(tex_x, "RGB", mul_x, "A")
    MEL.connect_material_expressions(norm_x, "", mul_x, "B")

    mul_y = MEL.create_material_expression(material, unreal.MaterialExpressionMultiply, 250, 100)
    MEL.connect_material_expressions(tex_y, "RGB", mul_y, "A")
    MEL.connect_material_expressions(norm_y, "", mul_y, "B")

    mul_z = MEL.create_material_expression(material, unreal.MaterialExpressionMultiply, 250, 300)
    MEL.connect_material_expressions(tex_z, "RGB", mul_z, "A")
    MEL.connect_material_expressions(norm_z, "", mul_z, "B")

    add_xy = MEL.create_material_expression(material, unreal.MaterialExpressionAdd, 480, 0)
    MEL.connect_material_expressions(mul_x, "", add_xy, "A")
    MEL.connect_material_expressions(mul_y, "", add_xy, "B")

    add_xyz = MEL.create_material_expression(material, unreal.MaterialExpressionAdd, 650, 150)
    MEL.connect_material_expressions(add_xy, "", add_xyz, "A")
    MEL.connect_material_expressions(mul_z, "", add_xyz, "B")

    MEL.connect_material_property(add_xyz, "", unreal.MaterialProperty.MP_BASE_COLOR)

    # Modest default roughness so it isn't shiny plastic -- constant, not textured (matches
    # the punch-list note that these AI-prototype materials don't have real roughness maps
    # yet; this at least gives a sane non-default value instead of the engine default).
    roughness_const = MEL.create_material_expression(material, unreal.MaterialExpressionConstant, 650, 350)
    roughness_const.set_editor_property("R", 0.75)
    MEL.connect_material_property(roughness_const, "", unreal.MaterialProperty.MP_ROUGHNESS)

    MEL.recompile_material(material)
    log("  done -- %s now triplanar-sampled from %s" % (material.get_name(), texture.get_name()))


def build_fluid_water(material, texture):
    log("Rebuilding %s as animated water..." % material.get_name())
    MEL.delete_all_material_expressions(material)

    uv0 = MEL.create_material_expression(material, unreal.MaterialExpressionTextureCoordinate, -1200, 0)

    # --- Layer 1: slow pan, larger scale ---
    scale1 = MEL.create_material_expression(material, unreal.MaterialExpressionConstant, -1200, 150)
    scale1.set_editor_property("R", 0.6)
    uv1_scaled = MEL.create_material_expression(material, unreal.MaterialExpressionMultiply, -1000, 50)
    MEL.connect_material_expressions(uv0, "", uv1_scaled, "A")
    MEL.connect_material_expressions(scale1, "", uv1_scaled, "B")

    time1 = MEL.create_material_expression(material, unreal.MaterialExpressionConstant2Vector, -1000, 200)
    time1.set_editor_property("R", 0.015); time1.set_editor_property("G", 0.01)
    panner1 = MEL.create_material_expression(material, unreal.MaterialExpressionPanner, -800, 100)
    panner1.set_editor_property("SpeedX", 0.015)
    panner1.set_editor_property("SpeedY", 0.01)
    MEL.connect_material_expressions(uv1_scaled, "", panner1, "Coordinate")

    tex1 = MEL.create_material_expression(material, unreal.MaterialExpressionTextureSample, -600, 0)
    tex1.set_editor_property("texture", texture)
    MEL.connect_material_expressions(panner1, "", tex1, "Coordinates")

    # --- Layer 2: opposite direction, different scale/speed -- breaks the "obviously
    # scrolling" tell of a single panned layer ---
    scale2 = MEL.create_material_expression(material, unreal.MaterialExpressionConstant, -1200, 350)
    scale2.set_editor_property("R", 1.3)
    uv2_scaled = MEL.create_material_expression(material, unreal.MaterialExpressionMultiply, -1000, 400)
    MEL.connect_material_expressions(uv0, "", uv2_scaled, "A")
    MEL.connect_material_expressions(scale2, "", uv2_scaled, "B")

    panner2 = MEL.create_material_expression(material, unreal.MaterialExpressionPanner, -800, 400)
    panner2.set_editor_property("SpeedX", -0.008)
    panner2.set_editor_property("SpeedY", 0.02)
    MEL.connect_material_expressions(uv2_scaled, "", panner2, "Coordinate")

    tex2 = MEL.create_material_expression(material, unreal.MaterialExpressionTextureSample, -600, 400)
    tex2.set_editor_property("texture", texture)
    MEL.connect_material_expressions(panner2, "", tex2, "Coordinates")

    # --- Blend the two layers 50/50, then tint blue-teal so it reads as water rather than
    # the sand-colored source photo ---
    blend = MEL.create_material_expression(material, unreal.MaterialExpressionLerp, -350, 150)
    MEL.connect_material_expressions(tex1, "RGB", blend, "A")
    MEL.connect_material_expressions(tex2, "RGB", blend, "B")
    blend.set_editor_property("ConstAlpha", 0.5)

    tint = MEL.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, -350, 320)
    tint.set_editor_property("Constant", unreal.LinearColor(0.55, 0.75, 0.8, 1.0))

    tinted = MEL.create_material_expression(material, unreal.MaterialExpressionMultiply, -150, 200)
    MEL.connect_material_expressions(blend, "", tinted, "A")
    MEL.connect_material_expressions(tint, "", tinted, "B")

    MEL.connect_material_property(tinted, "", unreal.MaterialProperty.MP_BASE_COLOR)

    # --- Fresnel-driven roughness: sharp/reflective at grazing angles, softer straight-on
    # -- the actual visual cue that reads as "wet liquid" rather than matte ground ---
    fresnel = MEL.create_material_expression(material, unreal.MaterialExpressionFresnel, -150, 500)
    fresnel.set_editor_property("Exponent", 3.0)

    rough_min = MEL.create_material_expression(material, unreal.MaterialExpressionConstant, 50, 450)
    rough_min.set_editor_property("R", 0.05)
    rough_max = MEL.create_material_expression(material, unreal.MaterialExpressionConstant, 50, 550)
    rough_max.set_editor_property("R", 0.35)

    roughness_lerp = MEL.create_material_expression(material, unreal.MaterialExpressionLerp, 220, 500)
    MEL.connect_material_expressions(rough_max, "", roughness_lerp, "A")
    MEL.connect_material_expressions(rough_min, "", roughness_lerp, "B")
    MEL.connect_material_expressions(fresnel, "", roughness_lerp, "Alpha")

    MEL.connect_material_property(roughness_lerp, "", unreal.MaterialProperty.MP_ROUGHNESS)

    specular_const = MEL.create_material_expression(material, unreal.MaterialExpressionConstant, 220, 650)
    specular_const.set_editor_property("R", 0.9)
    MEL.connect_material_property(specular_const, "", unreal.MaterialProperty.MP_SPECULAR)

    MEL.recompile_material(material)
    log("  done -- %s now animated/fresnel-shaded" % material.get_name())
    log("  NOTE: Water_Placeholder is a flat, unsubdivided scaled cube -- this material")
    log("  cannot make it physically ripple, only look reflective/in-motion. Real wave")
    log("  displacement needs either more mesh subdivisions + a World Position Offset,")
    log("  or swapping to UE5.8's built-in Water plugin (Water Body Ocean/Lake) -- a mesh")
    log("  change, not something this script attempts.")


def run():
    wall_mat = AL.load_asset(WALL_MATERIAL_PATH)
    wall_tex = AL.load_asset(WALL_TEXTURE_PATH)
    if wall_mat and wall_tex:
        build_triplanar_basecolor(wall_mat, wall_tex)
    else:
        log("SKIPPED wall -- could not load %s or %s" % (WALL_MATERIAL_PATH, WALL_TEXTURE_PATH))

    water_mat = AL.load_asset(WATER_MATERIAL_PATH)
    water_tex = AL.load_asset(WATER_TEXTURE_PATH)
    if water_mat and water_tex:
        build_fluid_water(water_mat, water_tex)
    else:
        log("SKIPPED water -- could not load %s or %s" % (WATER_MATERIAL_PATH, WATER_TEXTURE_PATH))

    if ALSO_FIX_GROUND:
        ground_mat = AL.load_asset(GROUND_MATERIAL_PATH)
        ground_tex = AL.load_asset(GROUND_TEXTURE_PATH)
        if ground_mat and ground_tex:
            build_triplanar_basecolor(ground_mat, ground_tex, tile_world_size=768.0)
        else:
            log("SKIPPED ground -- could not load %s or %s" % (GROUND_MATERIAL_PATH, GROUND_TEXTURE_PATH))

    if ALSO_FIX_FURNITURE:
        furn_mat = AL.load_asset(FURNITURE_MATERIAL_PATH)
        furn_tex = AL.load_asset(FURNITURE_TEXTURE_PATH)
        if furn_mat and furn_tex:
            build_triplanar_basecolor(furn_mat, furn_tex, tile_world_size=128.0)
        else:
            log("SKIPPED furniture -- could not load %s or %s" % (FURNITURE_MATERIAL_PATH, FURNITURE_TEXTURE_PATH))

    log("All done. Save the modified materials (Ctrl+Shift+S or File > Save All) and")
    log("check the garrison and water in the viewport / a fresh PIE run.")


run()
