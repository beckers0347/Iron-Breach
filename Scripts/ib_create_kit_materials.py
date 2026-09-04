"""
Iron Breach -- kit zone material (headless).
UnrealEditor-Cmd ... -run=pythonscript -script=Scripts/ib_create_kit_materials.py

Creates /Game/IronBreach/Classes/M_IBKitZone: unlit, translucent, two-sided.
    Color (vector)  * Glow (scalar)  -> Emissive
    Opacity (scalar)                 -> Opacity
AIBKitZone picks it up by path (disc = trade color at 35 %, post = solid) and
falls back to the engine BasicShapeMaterial when it is missing.
Idempotent: an existing asset is left alone (delete it to regenerate).
"""
import unreal

def log(msg):
    unreal.log(f"IBPY: {msg}")

PATH = "/Game/IronBreach/Classes"
NAME = "M_IBKitZone"
FULL = f"{PATH}/{NAME}"
EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary

log("=== kit materials starting ===")
if EAL.does_asset_exist(FULL):
    log(f"OK   exists, left alone: {FULL}")
else:
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    mat = tools.create_asset(NAME, PATH, unreal.Material, unreal.MaterialFactoryNew())
    if mat is None:
        raise RuntimeError(f"create_asset failed for {FULL}")
    mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    mat.set_editor_property("two_sided", True)

    color = MEL.create_material_expression(mat, unreal.MaterialExpressionVectorParameter, -700, -150)
    color.set_editor_property("parameter_name", "Color")
    color.set_editor_property("default_value", unreal.LinearColor(1.0, 0.55, 0.12, 1.0))

    glow = MEL.create_material_expression(mat, unreal.MaterialExpressionScalarParameter, -700, 80)
    glow.set_editor_property("parameter_name", "Glow")
    glow.set_editor_property("default_value", 2.0)

    mul = MEL.create_material_expression(mat, unreal.MaterialExpressionMultiply, -350, -60)
    MEL.connect_material_expressions(color, "", mul, "A")
    MEL.connect_material_expressions(glow, "", mul, "B")
    MEL.connect_material_property(mul, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)

    opacity = MEL.create_material_expression(mat, unreal.MaterialExpressionScalarParameter, -700, 300)
    opacity.set_editor_property("parameter_name", "Opacity")
    opacity.set_editor_property("default_value", 0.35)
    MEL.connect_material_property(opacity, "", unreal.MaterialProperty.MP_OPACITY)

    MEL.recompile_material(mat)
    ok = EAL.save_asset(FULL)
    log(f"{'OK  ' if ok else 'FAIL'} created {FULL}")

log("KIT MATERIALS DONE")
