"""
Carrowgate Garrison -- realistic water material rebuild
==========================================================
IRON BREACH / Unreal Engine 5.8

WHAT THIS IS
------------
Rebuilds M_AI_Water (currently a flat, static tiled texture -- reads as a
painted plane, not water) into an actual animated water shader:

  - Two copies of the existing T_Water_Ocean texture, panned at different
    speeds/directions/scales and multiplied together, so the surface visibly
    moves instead of sitting frozen, and the moire between the two layers
    reads as shimmer/sparkle instead of one obvious repeating tile.
  - A cheap fake normal map built from those same two panned samples (no
    real normal texture was ever generated) -- small per-pixel tilts that
    catch the sun and break up the flat look. Pure pixel-shader trick, needs
    no extra mesh subdivision (the water plane is still a single flat quad).
  - Fresnel-driven rim brightening: water gets a lighter, more reflective
    "sky" tint at grazing viewing angles and stays a darker tinted color
    looking straight down -- the single biggest visual cue that reads as
    "water" instead of "flat blue plane."
  - Low, fixed Roughness + boosted Specular for a sharp sun glint.

Does NOT use UE5's Water plugin/WaterBodyOcean (not enabled on this
project) -- this is a pixel-shader-only upgrade to the existing flat plane:
no new mesh, no plugin, no editor restart. True Gerstner-wave displacement
would need the Water plugin -- ask if that's wanted later.

HOW TO RUN IT
-------------
Run AFTER import_ai_textures.py has created T_Water_Ocean at least once
(reuses that texture, no re-import needed here). From the Output Log
console:
    py "X:/IronBreach/Content/Python/build_water_material.py"
or the dedicated Python console tab:
    exec(open("X:/IronBreach/Content/Python/build_water_material.py").read())

Then re-run build_carrowgate_garrison.py so the water plane picks up the
rebuilt material (it loads M_AI_Water by path, same as always -- no code
change needed there).

Safe to re-run: wipes and rebuilds M_AI_Water's graph in place.
"""

import unreal

TEXTURE_PATH = "/Game/LevelPrototyping/AITextures/T_Water_Ocean.T_Water_Ocean"
MATERIAL_PATH_DIR = "/Game/LevelPrototyping/AITextures"
MATERIAL_NAME = "M_AI_Water"

asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary


def run():
    texture = unreal.EditorAssetLibrary.load_asset(TEXTURE_PATH)
    if texture is None:
        unreal.log_error(f"[Water Material] {TEXTURE_PATH} not found -- run import_ai_textures.py first.")
        return

    full_path = f"{MATERIAL_PATH_DIR}/{MATERIAL_NAME}.{MATERIAL_NAME}"
    if unreal.EditorAssetLibrary.does_asset_exist(full_path):
        material = unreal.EditorAssetLibrary.load_asset(full_path)
        mel.delete_all_material_expressions(material)
    else:
        factory = unreal.MaterialFactoryNew()
        material = asset_tools.create_asset(MATERIAL_NAME, MATERIAL_PATH_DIR, unreal.Material, factory)

    if material is None:
        unreal.log_error("[Water Material] Could not create/load M_AI_Water.")
        return

    # ---- UVs: two independently panned, differently-scaled copies ----
    texcoord = mel.create_material_expression(material, unreal.MaterialExpressionTextureCoordinate, -1400, -350)

    tile_a = mel.create_material_expression(material, unreal.MaterialExpressionMultiply, -1200, -500)
    tile_a.set_editor_property("const_b", 250.0)
    mel.connect_material_expressions(texcoord, "", tile_a, "A")

    tile_b = mel.create_material_expression(material, unreal.MaterialExpressionMultiply, -1200, -250)
    tile_b.set_editor_property("const_b", 180.0)
    mel.connect_material_expressions(texcoord, "", tile_b, "A")

    time_node = mel.create_material_expression(material, unreal.MaterialExpressionTime, -1200, 0)

    panner_a = mel.create_material_expression(material, unreal.MaterialExpressionPanner, -1000, -500)
    panner_a.set_editor_property("speed_x", 0.02)
    panner_a.set_editor_property("speed_y", 0.012)
    mel.connect_material_expressions(tile_a, "", panner_a, "Coordinate")
    mel.connect_material_expressions(time_node, "", panner_a, "Time")

    panner_b = mel.create_material_expression(material, unreal.MaterialExpressionPanner, -1000, -250)
    panner_b.set_editor_property("speed_x", -0.017)
    panner_b.set_editor_property("speed_y", 0.024)
    mel.connect_material_expressions(tile_b, "", panner_b, "Coordinate")
    mel.connect_material_expressions(time_node, "", panner_b, "Time")

    sample_a = mel.create_material_expression(material, unreal.MaterialExpressionTextureSample, -800, -500)
    sample_a.set_editor_property("texture", texture)
    mel.connect_material_expressions(panner_a, "", sample_a, "UVs")

    sample_b = mel.create_material_expression(material, unreal.MaterialExpressionTextureSample, -800, -250)
    sample_b.set_editor_property("texture", texture)
    mel.connect_material_expressions(panner_b, "", sample_b, "UVs")

    # ---- Base Color: multiply the two panned samples (moire/shimmer), tint
    # dark teal, then brighten toward a light "sky" tint at grazing angles ----
    combine = mel.create_material_expression(material, unreal.MaterialExpressionMultiply, -600, -400)
    mel.connect_material_expressions(sample_a, "RGB", combine, "A")
    mel.connect_material_expressions(sample_b, "RGB", combine, "B")

    combine_boost = mel.create_material_expression(material, unreal.MaterialExpressionMultiply, -450, -400)
    combine_boost.set_editor_property("const_b", 2.5)
    mel.connect_material_expressions(combine, "", combine_boost, "A")

    deep_color = mel.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, -450, -150)
    deep_color.set_editor_property("constant", unreal.LinearColor(0.02, 0.09, 0.14, 1.0))

    tinted = mel.create_material_expression(material, unreal.MaterialExpressionMultiply, -250, -300)
    mel.connect_material_expressions(combine_boost, "", tinted, "A")
    mel.connect_material_expressions(deep_color, "", tinted, "B")

    fresnel = mel.create_material_expression(material, unreal.MaterialExpressionFresnel, -450, 100)
    fresnel.set_editor_property("exponent", 3.5)
    fresnel.set_editor_property("base_reflect_fraction", 0.04)

    rim_color = mel.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, -450, 300)
    rim_color.set_editor_property("constant", unreal.LinearColor(0.55, 0.65, 0.7, 1.0))

    final_color = mel.create_material_expression(material, unreal.MaterialExpressionLinearInterpolate, 0, 0)
    mel.connect_material_expressions(tinted, "", final_color, "A")
    mel.connect_material_expressions(rim_color, "", final_color, "B")
    mel.connect_material_expressions(fresnel, "", final_color, "Alpha")
    mel.connect_material_property(final_color, "", unreal.MaterialProperty.MP_BASE_COLOR)

    # ---- Roughness / Specular: low + boosted for a sharp sun glint ----
    roughness = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -450, 500)
    roughness.set_editor_property("r", 0.06)
    mel.connect_material_property(roughness, "", unreal.MaterialProperty.MP_ROUGHNESS)

    specular = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -450, 620)
    specular.set_editor_property("r", 0.9)
    mel.connect_material_property(specular, "", unreal.MaterialProperty.MP_SPECULAR)

    # ---- Fake normal: no real normal map was generated, so build a subtle
    # per-pixel tilt from the same two panned samples (different channels so
    # it doesn't just mirror the color pattern) instead of a flat (0,0,1). ----
    center_a = mel.create_material_expression(material, unreal.MaterialExpressionAdd, -800, 750)
    center_a.set_editor_property("const_b", -0.5)
    mel.connect_material_expressions(sample_a, "R", center_a, "A")

    strength_a = mel.create_material_expression(material, unreal.MaterialExpressionMultiply, -650, 750)
    strength_a.set_editor_property("const_b", 0.15)
    mel.connect_material_expressions(center_a, "", strength_a, "A")

    center_b = mel.create_material_expression(material, unreal.MaterialExpressionAdd, -800, 880)
    center_b.set_editor_property("const_b", -0.5)
    mel.connect_material_expressions(sample_b, "G", center_b, "A")

    strength_b = mel.create_material_expression(material, unreal.MaterialExpressionMultiply, -650, 880)
    strength_b.set_editor_property("const_b", 0.15)
    mel.connect_material_expressions(center_b, "", strength_b, "A")

    normal_xy = mel.create_material_expression(material, unreal.MaterialExpressionAppendVector, -450, 800)
    mel.connect_material_expressions(strength_a, "", normal_xy, "A")
    mel.connect_material_expressions(strength_b, "", normal_xy, "B")

    normal_z = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -450, 950)
    normal_z.set_editor_property("r", 1.0)

    normal_full = mel.create_material_expression(material, unreal.MaterialExpressionAppendVector, -250, 850)
    mel.connect_material_expressions(normal_xy, "", normal_full, "A")
    mel.connect_material_expressions(normal_z, "", normal_full, "B")
    mel.connect_material_property(normal_full, "", unreal.MaterialProperty.MP_NORMAL)

    mel.layout_material_expressions(material)
    mel.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material)
    unreal.log(f"[Water Material] Rebuilt {MATERIAL_NAME} with animated ripple + Fresnel rim shading.")


run()
