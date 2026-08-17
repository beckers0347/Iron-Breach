"""
Carrowgate Garrison -- window glass material
==============================================
IRON BREACH / Unreal Engine 5.8

WHAT THIS IS
------------
Builds M_AI_Glass: a translucent pane material for the window cutouts added to
each building's walls in build_carrowgate_garrison.py (previously just open
holes showing straight through to the exterior). Kept simple and cheap --
this is still a blockout-stage material, same spirit as M_AI_Water:

  - blend_mode = BLEND_TRANSLUCENT, two_sided = True (visible from both
    inside and outside the pane, since a window gets looked through from
    either side).
  - A light blue-grey base color tint, mostly transparent (opacity ~0.12)
    so the exterior is still clearly visible through it.
  - Fresnel-driven opacity boost: nearly invisible dead-on, noticeably more
    reflective/opaque at grazing viewing angles -- the same "reads as glass,
    not as a colored gel" cue used for the water material's rim brightening.
  - Low Roughness + boosted Specular for a sharp, glassy highlight.

Confirmed via Epic's official Python API docs before writing this (same
verification step used for ScriptCollisionShapeType earlier in this project,
after a wrong enum name there silently broke a fix):
https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/BlendMode
  -> unreal.BlendMode.BLEND_TRANSLUCENT
https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/Material
  -> Material.blend_mode / Material.two_sided are real read-write properties.

HOW TO RUN IT
-------------
From the Output Log console:
    py "X:/IronBreach/Content/Python/build_glass_material.py"
or the dedicated Python console tab:
    exec(open("X:/IronBreach/Content/Python/build_glass_material.py").read())

Then re-run build_carrowgate_garrison.py so the window panes pick up this
material (it loads M_AI_Glass by path, same pattern as every other AI
material -- no other code change needed).

Safe to re-run: wipes and rebuilds M_AI_Glass's graph in place.
"""

import unreal

MATERIAL_PATH_DIR = "/Game/LevelPrototyping/AITextures"
MATERIAL_NAME = "M_AI_Glass"

asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary


def run():
    full_path = f"{MATERIAL_PATH_DIR}/{MATERIAL_NAME}.{MATERIAL_NAME}"
    if unreal.EditorAssetLibrary.does_asset_exist(full_path):
        material = unreal.EditorAssetLibrary.load_asset(full_path)
        mel.delete_all_material_expressions(material)
    else:
        factory = unreal.MaterialFactoryNew()
        material = asset_tools.create_asset(MATERIAL_NAME, MATERIAL_PATH_DIR, unreal.Material, factory)

    if material is None:
        unreal.log_error("[Glass Material] Could not create/load M_AI_Glass.")
        return

    material.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    material.set_editor_property("two_sided", True)

    # ---- Base Color: light blue-grey pane tint ----
    base_color = mel.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, -450, -300)
    base_color.set_editor_property("constant", unreal.LinearColor(0.72, 0.82, 0.86, 1.0))
    mel.connect_material_property(base_color, "", unreal.MaterialProperty.MP_BASE_COLOR)

    # ---- Opacity: mostly transparent dead-on, brighter/more opaque at
    # grazing angles (Fresnel) so it reads as glass, not a flat tinted card ----
    fresnel = mel.create_material_expression(material, unreal.MaterialExpressionFresnel, -450, 0)
    fresnel.set_editor_property("exponent", 2.5)
    fresnel.set_editor_property("base_reflect_fraction", 0.04)

    base_opacity = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -450, 150)
    base_opacity.set_editor_property("r", 0.12)

    grazing_opacity = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -450, 250)
    grazing_opacity.set_editor_property("r", 0.55)

    opacity = mel.create_material_expression(material, unreal.MaterialExpressionLinearInterpolate, -200, 100)
    mel.connect_material_expressions(base_opacity, "", opacity, "A")
    mel.connect_material_expressions(grazing_opacity, "", opacity, "B")
    mel.connect_material_expressions(fresnel, "", opacity, "Alpha")
    mel.connect_material_property(opacity, "", unreal.MaterialProperty.MP_OPACITY)

    # ---- Roughness / Specular: low + boosted for a sharp glassy highlight ----
    roughness = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -450, 400)
    roughness.set_editor_property("r", 0.05)
    mel.connect_material_property(roughness, "", unreal.MaterialProperty.MP_ROUGHNESS)

    specular = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -450, 500)
    specular.set_editor_property("r", 0.85)
    mel.connect_material_property(specular, "", unreal.MaterialProperty.MP_SPECULAR)

    mel.layout_material_expressions(material)
    mel.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material)
    unreal.log(f"[Glass Material] Rebuilt {MATERIAL_NAME} (translucent, Fresnel-boosted opacity).")


run()
