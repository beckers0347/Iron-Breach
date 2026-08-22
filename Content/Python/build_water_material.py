"""
Carrowgate Garrison -- realistic water material rebuild (deep + shallow bands)
================================================================================
IRON BREACH / Unreal Engine 5.8

WHAT THIS IS
------------
Rebuilds M_AI_Water (and now also builds a second, lighter M_AI_Water_Shallow)
into an actual animated water shader, and adds a second, coarser "swell" layer
on top of the original fine ripple so the surface reads less like a single
repeating tile and more like real chop with two overlapping wave scales:

  - FINE layer (as before): two panned copies of T_Water_Ocean, multiplied
    together for shimmer, and used to build a cheap fake normal map.
  - SWELL layer (new): a second pair of panned copies, tiled much coarser and
    panned slower, blended into both the color (subtle brightness variation --
    "wave faces" catching more or less light) and the fake normal (bigger,
    slower undulation under the fine ripple detail).
  - Fresnel-driven rim brightening, same as before -- water gets a lighter,
    more reflective "sky" tint at grazing angles.
  - Low, fixed Roughness + boosted Specular for a sharp sun glint.

build_carrowgate_mainland.py's build_shoreline() now lays down a SHALLOW band
right along the beach and a DEEP band further out (real oceans read lighter/
more turquoise close to shore where light bounces off the sand below, and
darker further out) -- this file builds both materials from one shared graph-
building function, just with a different deep-tint constant, so build_shoreline
can put a visibly different color close to the surf line than out past it.
Same graph shape for both -- no plugin, no new mesh, pure pixel shader.

Does NOT use UE5's Water plugin/WaterBodyOcean (not enabled on this
project). True Gerstner-wave displacement would need the Water plugin -- ask
if that's wanted later. Actual breaking waves/foam are handled separately by
build_foam_material.py + build_carrowgate_mainland.py's surf-strip placement.

HOW TO RUN IT
-------------
Run AFTER import_ai_textures.py has created T_Water_Ocean at least once
(reuses that texture, no re-import needed here). From the Output Log
console:
    py "X:/IronBreach/Content/Python/build_water_material.py"

Then re-run build_carrowgate_mainland.py so the shoreline picks up the
rebuilt materials (loads them by path, same as always -- no code change
needed there).

Safe to re-run: wipes and rebuilds both materials' graphs in place.
"""

import unreal

TEXTURE_PATH = "/Game/LevelPrototyping/AITextures/T_Water_Ocean.T_Water_Ocean"
MATERIAL_PATH_DIR = "/Game/LevelPrototyping/AITextures"

asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary


def build_water_material(material_name, deep_rgb, rim_rgb=(0.55, 0.65, 0.7)):
    texture = unreal.EditorAssetLibrary.load_asset(TEXTURE_PATH)
    if texture is None:
        unreal.log_error(f"[Water Material] {TEXTURE_PATH} not found -- run import_ai_textures.py first.")
        return None

    full_path = f"{MATERIAL_PATH_DIR}/{material_name}.{material_name}"
    if unreal.EditorAssetLibrary.does_asset_exist(full_path):
        material = unreal.EditorAssetLibrary.load_asset(full_path)
        mel.delete_all_material_expressions(material)
    else:
        factory = unreal.MaterialFactoryNew()
        material = asset_tools.create_asset(material_name, MATERIAL_PATH_DIR, unreal.Material, factory)

    if material is None:
        unreal.log_error(f"[Water Material] Could not create/load {material_name}.")
        return None

    # ---- UVs: two independently panned, differently-scaled copies (FINE) ----
    texcoord = mel.create_material_expression(material, unreal.MaterialExpressionTextureCoordinate, -1600, -350)

    tile_a = mel.create_material_expression(material, unreal.MaterialExpressionMultiply, -1400, -500)
    tile_a.set_editor_property("const_b", 250.0)
    mel.connect_material_expressions(texcoord, "", tile_a, "A")

    tile_b = mel.create_material_expression(material, unreal.MaterialExpressionMultiply, -1400, -250)
    tile_b.set_editor_property("const_b", 180.0)
    mel.connect_material_expressions(texcoord, "", tile_b, "A")

    time_node = mel.create_material_expression(material, unreal.MaterialExpressionTime, -1400, 0)

    panner_a = mel.create_material_expression(material, unreal.MaterialExpressionPanner, -1200, -500)
    panner_a.set_editor_property("speed_x", 0.02)
    panner_a.set_editor_property("speed_y", 0.012)
    mel.connect_material_expressions(tile_a, "", panner_a, "Coordinate")
    mel.connect_material_expressions(time_node, "", panner_a, "Time")

    panner_b = mel.create_material_expression(material, unreal.MaterialExpressionPanner, -1200, -250)
    panner_b.set_editor_property("speed_x", -0.017)
    panner_b.set_editor_property("speed_y", 0.024)
    mel.connect_material_expressions(tile_b, "", panner_b, "Coordinate")
    mel.connect_material_expressions(time_node, "", panner_b, "Time")

    sample_a = mel.create_material_expression(material, unreal.MaterialExpressionTextureSample, -1000, -500)
    sample_a.set_editor_property("texture", texture)
    mel.connect_material_expressions(panner_a, "", sample_a, "UVs")

    sample_b = mel.create_material_expression(material, unreal.MaterialExpressionTextureSample, -1000, -250)
    sample_b.set_editor_property("texture", texture)
    mel.connect_material_expressions(panner_b, "", sample_b, "UVs")

    # ---- SWELL layer: a second, much coarser and slower panned pair -- big
    # undulating shapes under the fine shimmer above, so the surface doesn't
    # read as one uniform repeating scale. ----
    tile_c = mel.create_material_expression(material, unreal.MaterialExpressionMultiply, -1400, -750)
    tile_c.set_editor_property("const_b", 34.0)
    mel.connect_material_expressions(texcoord, "", tile_c, "A")

    tile_d = mel.create_material_expression(material, unreal.MaterialExpressionMultiply, -1400, -950)
    tile_d.set_editor_property("const_b", 46.0)
    mel.connect_material_expressions(texcoord, "", tile_d, "A")

    panner_c = mel.create_material_expression(material, unreal.MaterialExpressionPanner, -1200, -750)
    panner_c.set_editor_property("speed_x", 0.006)
    panner_c.set_editor_property("speed_y", 0.004)
    mel.connect_material_expressions(tile_c, "", panner_c, "Coordinate")
    mel.connect_material_expressions(time_node, "", panner_c, "Time")

    panner_d = mel.create_material_expression(material, unreal.MaterialExpressionPanner, -1200, -950)
    panner_d.set_editor_property("speed_x", -0.005)
    panner_d.set_editor_property("speed_y", 0.007)
    mel.connect_material_expressions(tile_d, "", panner_d, "Coordinate")
    mel.connect_material_expressions(time_node, "", panner_d, "Time")

    sample_c = mel.create_material_expression(material, unreal.MaterialExpressionTextureSample, -1000, -750)
    sample_c.set_editor_property("texture", texture)
    mel.connect_material_expressions(panner_c, "", sample_c, "UVs")

    sample_d = mel.create_material_expression(material, unreal.MaterialExpressionTextureSample, -1000, -950)
    sample_d.set_editor_property("texture", texture)
    mel.connect_material_expressions(panner_d, "", sample_d, "UVs")

    swell = mel.create_material_expression(material, unreal.MaterialExpressionMultiply, -800, -850)
    mel.connect_material_expressions(sample_c, "R", swell, "A")
    mel.connect_material_expressions(sample_d, "G", swell, "B")
    swell_boost = mel.create_material_expression(material, unreal.MaterialExpressionMultiply, -650, -850)
    swell_boost.set_editor_property("const_b", 1.6)
    mel.connect_material_expressions(swell, "", swell_boost, "A")

    # ---- Base Color: multiply the two FINE panned samples (moire/shimmer),
    # nudge brightness with the SWELL layer, tint dark, then brighten toward a
    # light "sky" tint at grazing angles. ----
    combine = mel.create_material_expression(material, unreal.MaterialExpressionMultiply, -600, -400)
    mel.connect_material_expressions(sample_a, "RGB", combine, "A")
    mel.connect_material_expressions(sample_b, "RGB", combine, "B")

    combine_boost = mel.create_material_expression(material, unreal.MaterialExpressionMultiply, -450, -400)
    combine_boost.set_editor_property("const_b", 2.5)
    mel.connect_material_expressions(combine, "", combine_boost, "A")

    with_swell = mel.create_material_expression(material, unreal.MaterialExpressionMultiply, -300, -550)
    mel.connect_material_expressions(combine_boost, "", with_swell, "A")
    mel.connect_material_expressions(swell_boost, "", with_swell, "B")

    deep_color = mel.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, -450, -150)
    deep_color.set_editor_property("constant", unreal.LinearColor(deep_rgb[0], deep_rgb[1], deep_rgb[2], 1.0))

    tinted = mel.create_material_expression(material, unreal.MaterialExpressionMultiply, -150, -300)
    mel.connect_material_expressions(with_swell, "", tinted, "A")
    mel.connect_material_expressions(deep_color, "", tinted, "B")

    fresnel = mel.create_material_expression(material, unreal.MaterialExpressionFresnel, -450, 100)
    fresnel.set_editor_property("exponent", 3.5)
    fresnel.set_editor_property("base_reflect_fraction", 0.04)

    rim_color = mel.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, -450, 300)
    rim_color.set_editor_property("constant", unreal.LinearColor(rim_rgb[0], rim_rgb[1], rim_rgb[2], 1.0))

    final_color = mel.create_material_expression(material, unreal.MaterialExpressionLinearInterpolate, 50, 0)
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

    # ---- Fake normal: blends the FINE per-pixel tilt (as before) with a
    # weaker, larger-scale tilt from the SWELL samples, so the "bump" reads at
    # two scales instead of one uniform ripple size. ----
    center_a = mel.create_material_expression(material, unreal.MaterialExpressionAdd, -1000, 750)
    center_a.set_editor_property("const_b", -0.5)
    mel.connect_material_expressions(sample_a, "R", center_a, "A")
    strength_a = mel.create_material_expression(material, unreal.MaterialExpressionMultiply, -850, 750)
    strength_a.set_editor_property("const_b", 0.15)
    mel.connect_material_expressions(center_a, "", strength_a, "A")

    center_b = mel.create_material_expression(material, unreal.MaterialExpressionAdd, -1000, 880)
    center_b.set_editor_property("const_b", -0.5)
    mel.connect_material_expressions(sample_b, "G", center_b, "A")
    strength_b = mel.create_material_expression(material, unreal.MaterialExpressionMultiply, -850, 880)
    strength_b.set_editor_property("const_b", 0.15)
    mel.connect_material_expressions(center_b, "", strength_b, "A")

    center_c = mel.create_material_expression(material, unreal.MaterialExpressionAdd, -1000, 1010)
    center_c.set_editor_property("const_b", -0.5)
    mel.connect_material_expressions(sample_c, "R", center_c, "A")
    strength_c = mel.create_material_expression(material, unreal.MaterialExpressionMultiply, -850, 1010)
    strength_c.set_editor_property("const_b", 0.08)  # weaker than the fine layer -- big shapes, gentle tilt
    mel.connect_material_expressions(center_c, "", strength_c, "A")

    center_d = mel.create_material_expression(material, unreal.MaterialExpressionAdd, -1000, 1140)
    center_d.set_editor_property("const_b", -0.5)
    mel.connect_material_expressions(sample_d, "G", center_d, "A")
    strength_d = mel.create_material_expression(material, unreal.MaterialExpressionMultiply, -850, 1140)
    strength_d.set_editor_property("const_b", 0.08)
    mel.connect_material_expressions(center_d, "", strength_d, "A")

    tilt_x = mel.create_material_expression(material, unreal.MaterialExpressionAdd, -650, 780)
    mel.connect_material_expressions(strength_a, "", tilt_x, "A")
    mel.connect_material_expressions(strength_c, "", tilt_x, "B")

    tilt_y = mel.create_material_expression(material, unreal.MaterialExpressionAdd, -650, 1010)
    mel.connect_material_expressions(strength_b, "", tilt_y, "A")
    mel.connect_material_expressions(strength_d, "", tilt_y, "B")

    normal_xy = mel.create_material_expression(material, unreal.MaterialExpressionAppendVector, -450, 900)
    mel.connect_material_expressions(tilt_x, "", normal_xy, "A")
    mel.connect_material_expressions(tilt_y, "", normal_xy, "B")

    normal_z = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -450, 1050)
    normal_z.set_editor_property("r", 1.0)

    normal_full = mel.create_material_expression(material, unreal.MaterialExpressionAppendVector, -250, 950)
    mel.connect_material_expressions(normal_xy, "", normal_full, "A")
    mel.connect_material_expressions(normal_z, "", normal_full, "B")
    mel.connect_material_property(normal_full, "", unreal.MaterialProperty.MP_NORMAL)

    mel.layout_material_expressions(material)
    mel.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material)
    unreal.log(f"[Water Material] Rebuilt {material_name} with fine + swell ripple, animated normal, Fresnel rim shading.")
    return material


def run():
    # Deep, open-water band -- the existing dark teal tint, unchanged.
    build_water_material("M_AI_Water", deep_rgb=(0.02, 0.09, 0.14))
    # Shallow, near-shore band -- lighter and more turquoise, as if light is
    # bouncing back off sand a few meters down. build_carrowgate_mainland.py's
    # build_shoreline() lays this down as a strip right along the beach, with
    # the deep material picking up further out.
    build_water_material("M_AI_Water_Shallow", deep_rgb=(0.06, 0.32, 0.34), rim_rgb=(0.65, 0.78, 0.78))


run()
