"""
Surf / foam material -- waves crashing on the shore
=====================================================
IRON BREACH / Unreal Engine 5.8

WHAT THIS IS
------------
Shane: "make the water look more realistic and maybe crash up on shore."
build_water_material.py covers the "more realistic" half (fine + swell
ripple, Fresnel rim, a lighter shallow band near the beach). This file covers
the "crash up on shore" half: an animated, pulsing whitewater material
(M_AI_Foam) that build_carrowgate_mainland.py's build_shoreline() lays down
as a few overlapping strips right where the beach meets the water.

There's no Water plugin on this project, so this isn't a real wave
simulation -- same pixel-shader-only approach as the water material:

  - Reuses T_Water_Ocean (same texture the water material samples), tiled
    much tighter and panned faster in two layers so it reads as streaky
    whitewater instead of open-ocean ripples.
  - The streak pattern is boosted and clamped into patchy foam clumps rather
    than a smooth grey wash.
  - A slow Sine wave on Time drives a surge pulse -- foam mostly sits low/
    faint and brightens in a sharp swell, then fades back, instead of just
    sitting there at a constant brightness. That pulse is what actually
    reads as "a wave crashing" rather than "a foam decal."
  - A "PhaseOffset" scalar parameter is added into the clock before anything
    else reads it. build_carrowgate_mainland.py creates a few Material
    Instance Constants off this one parent material, each with a different
    PhaseOffset, so the multiple surf strips it places don't all surge in
    perfect unison.
  - Unlit + translucent, bright near-white emissive so it reads clearly
    layered over both the beach and the water it overlaps.

HOW TO RUN IT
-------------
    py "X:/IronBreach/Content/Python/build_foam_material.py"

Then re-run build_carrowgate_mainland.py so build_shoreline()'s surf strips
pick it up (loads M_AI_Foam by path and builds the phase-offset instances
from it, same auto-pickup convention as everything else in this project).

Safe to re-run: wipes and rebuilds M_AI_Foam's graph in place. Doesn't touch
any Material Instance Constants build_carrowgate_mainland.py builds off it --
those just get re-pointed at the freshly rebuilt parent automatically.
"""

import unreal

TEXTURE_PATH = "/Game/LevelPrototyping/AITextures/T_Water_Ocean.T_Water_Ocean"
MATERIAL_PATH_DIR = "/Game/LevelPrototyping/AITextures"
MATERIAL_NAME = "M_AI_Foam"

asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary


def run():
    texture = unreal.EditorAssetLibrary.load_asset(TEXTURE_PATH)
    if texture is None:
        unreal.log_error(f"[Foam Material] {TEXTURE_PATH} not found -- run import_ai_textures.py first.")
        return

    full_path = f"{MATERIAL_PATH_DIR}/{MATERIAL_NAME}.{MATERIAL_NAME}"
    if unreal.EditorAssetLibrary.does_asset_exist(full_path):
        material = unreal.EditorAssetLibrary.load_asset(full_path)
        mel.delete_all_material_expressions(material)
    else:
        factory = unreal.MaterialFactoryNew()
        material = asset_tools.create_asset(MATERIAL_NAME, MATERIAL_PATH_DIR, unreal.Material, factory)

    if material is None:
        unreal.log_error("[Foam Material] Could not create/load M_AI_Foam.")
        return

    material.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    material.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    material.set_editor_property("two_sided", True)

    # ---- Phase offset -- lets build_carrowgate_mainland.py spin up a few
    # Material Instance Constants off this one parent, each surging at a
    # different moment (see the Sine-driven pulse further down). ----
    phase_param = mel.create_material_expression(material, unreal.MaterialExpressionScalarParameter, -1400, 0)
    phase_param.set_editor_property("parameter_name", "PhaseOffset")
    phase_param.set_editor_property("default_value", 0.0)

    time_node = mel.create_material_expression(material, unreal.MaterialExpressionTime, -1400, -150)
    phased_time = mel.create_material_expression(material, unreal.MaterialExpressionAdd, -1200, -75)
    mel.connect_material_expressions(time_node, "", phased_time, "A")
    mel.connect_material_expressions(phase_param, "", phased_time, "B")

    # ---- Two tightly-tiled, fast-panned samples of the same ocean texture --
    # streakier and busier than the open-water material's own tiling, which
    # is the visual difference between "ripples" and "whitewater." ----
    texcoord = mel.create_material_expression(material, unreal.MaterialExpressionTextureCoordinate, -1000, 200)

    tile_a = mel.create_material_expression(material, unreal.MaterialExpressionMultiply, -900, 100)
    tile_a.set_editor_property("const_b", 40.0)
    mel.connect_material_expressions(texcoord, "", tile_a, "A")

    tile_b = mel.create_material_expression(material, unreal.MaterialExpressionMultiply, -900, 350)
    tile_b.set_editor_property("const_b", 55.0)
    mel.connect_material_expressions(texcoord, "", tile_b, "A")

    panner_a = mel.create_material_expression(material, unreal.MaterialExpressionPanner, -700, 100)
    panner_a.set_editor_property("speed_x", 0.11)
    panner_a.set_editor_property("speed_y", -0.05)
    mel.connect_material_expressions(tile_a, "", panner_a, "Coordinate")
    mel.connect_material_expressions(phased_time, "", panner_a, "Time")

    panner_b = mel.create_material_expression(material, unreal.MaterialExpressionPanner, -700, 350)
    panner_b.set_editor_property("speed_x", -0.08)
    panner_b.set_editor_property("speed_y", 0.13)
    mel.connect_material_expressions(tile_b, "", panner_b, "Coordinate")
    mel.connect_material_expressions(phased_time, "", panner_b, "Time")

    sample_a = mel.create_material_expression(material, unreal.MaterialExpressionTextureSample, -500, 100)
    sample_a.set_editor_property("texture", texture)
    mel.connect_material_expressions(panner_a, "", sample_a, "UVs")

    sample_b = mel.create_material_expression(material, unreal.MaterialExpressionTextureSample, -500, 350)
    sample_b.set_editor_property("texture", texture)
    mel.connect_material_expressions(panner_b, "", sample_b, "UVs")

    streaks = mel.create_material_expression(material, unreal.MaterialExpressionMultiply, -300, 220)
    mel.connect_material_expressions(sample_a, "R", streaks, "A")
    mel.connect_material_expressions(sample_b, "G", streaks, "B")

    # Push the streak pattern toward pure white/pure-gone -- patchy foam
    # clumps instead of a smooth grey wash -- via boost + clamp (avoids
    # relying on a Power node's exact property names).
    streak_boost = mel.create_material_expression(material, unreal.MaterialExpressionMultiply, -150, 220)
    streak_boost.set_editor_property("const_b", 3.2)
    mel.connect_material_expressions(streaks, "", streak_boost, "A")
    streak_clamp = mel.create_material_expression(material, unreal.MaterialExpressionClamp, 0, 220)
    streak_clamp.set_editor_property("min_default", 0.0)
    streak_clamp.set_editor_property("max_default", 1.0)
    mel.connect_material_expressions(streak_boost, "", streak_clamp, "Input")

    # ---- Surge pulse -- a slow Sine on the (phase-shifted) clock, remapped
    # from [-1,1] to [0,1], then sharpened via boost + clamp so the foam
    # mostly sits low/faint and brightens in a brief pulse when a "wave"
    # breaks, instead of a smooth continuous breathing glow. ----
    sine = mel.create_material_expression(material, unreal.MaterialExpressionSine, -1200, 500)
    sine.set_editor_property("period", 4.5)
    mel.connect_material_expressions(phased_time, "", sine, "Input")

    sine_unit = mel.create_material_expression(material, unreal.MaterialExpressionMultiply, -1000, 500)
    sine_unit.set_editor_property("const_b", 0.5)
    mel.connect_material_expressions(sine, "", sine_unit, "A")
    sine_bias = mel.create_material_expression(material, unreal.MaterialExpressionAdd, -850, 500)
    sine_bias.set_editor_property("const_b", 0.5)
    mel.connect_material_expressions(sine_unit, "", sine_bias, "A")

    pulse_boost = mel.create_material_expression(material, unreal.MaterialExpressionMultiply, -700, 500)
    pulse_boost.set_editor_property("const_b", 2.4)
    mel.connect_material_expressions(sine_bias, "", pulse_boost, "A")
    pulse_shift = mel.create_material_expression(material, unreal.MaterialExpressionAdd, -550, 500)
    pulse_shift.set_editor_property("const_b", -0.7)
    mel.connect_material_expressions(pulse_boost, "", pulse_shift, "A")
    pulse = mel.create_material_expression(material, unreal.MaterialExpressionClamp, -400, 500)
    pulse.set_editor_property("min_default", 0.0)
    pulse.set_editor_property("max_default", 1.0)
    mel.connect_material_expressions(pulse_shift, "", pulse, "Input")

    # ---- Combine: streak pattern * surge pulse -> Opacity + Emissive. ----
    opacity = mel.create_material_expression(material, unreal.MaterialExpressionMultiply, 200, 350)
    mel.connect_material_expressions(streak_clamp, "", opacity, "A")
    mel.connect_material_expressions(pulse, "", opacity, "B")
    opacity_boost = mel.create_material_expression(material, unreal.MaterialExpressionMultiply, 400, 350)
    opacity_boost.set_editor_property("const_b", 1.5)
    mel.connect_material_expressions(opacity, "", opacity_boost, "A")
    mel.connect_material_property(opacity_boost, "", unreal.MaterialProperty.MP_OPACITY)

    base_color = mel.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, 200, 600)
    base_color.set_editor_property("constant", unreal.LinearColor(0.92, 0.97, 1.0, 1.0))
    emissive = mel.create_material_expression(material, unreal.MaterialExpressionMultiply, 400, 600)
    mel.connect_material_expressions(base_color, "", emissive, "A")
    mel.connect_material_expressions(pulse, "", emissive, "B")
    emissive_boost = mel.create_material_expression(material, unreal.MaterialExpressionMultiply, 600, 600)
    emissive_boost.set_editor_property("const_b", 1.8)
    mel.connect_material_expressions(emissive, "", emissive_boost, "A")
    mel.connect_material_property(emissive_boost, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)

    mel.layout_material_expressions(material)
    mel.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material)
    unreal.log(f"[Foam Material] Built {MATERIAL_NAME} at {full_path} (phase-offsettable, pulsing surf/foam).")


run()
