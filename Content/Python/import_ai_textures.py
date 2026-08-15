"""
Carrowgate Garrison -- AI texture import + material build
============================================================
IRON BREACH / Unreal Engine 5.8

WHAT THIS IS
------------
A one-shot Editor Python script that imports the 4 AI-generated (Meshy)
architectural textures sitting in Content/LevelPrototyping/AITextures/ and
builds a simple Material for each one, replacing the flat prototype-grid
colorways used by build_carrowgate_garrison.py's MAT_WALL/MAT_GROUND/
MAT_RAMP/MAT_FURNITURE with something that actually looks like concrete,
wet pavement, diamond-plate steel, and wood/metal furniture instead of a
UV checker pattern.

These are base-color-only images (no separate normal/roughness maps came out
of the generation), so each material is: TexCoord -> tiled UVs -> texture
sample -> Base Color, plus a flat Roughness (and Metallic for the ramp)
constant tuned by eye per material rather than sampled from a real map. Good
enough for a blockout pass; swap in real PBR sets later if this project goes
further than that.

HOW TO RUN IT
-------------
Same as build_carrowgate_garrison.py -- from the Output Log console:
    py "X:/IronBreach/Content/Python/import_ai_textures.py"
or the dedicated Python console tab:
    exec(open("X:/IronBreach/Content/Python/import_ai_textures.py").read())

Run this BEFORE (re)running build_carrowgate_garrison.py, since that script
loads these materials by path. Safe to re-run: existing textures get
re-imported in place and existing materials get their graph rebuilt from
scratch rather than duplicated.
"""

import os
import unreal

SOURCE_DIR = r"X:\IronBreach\Content\LevelPrototyping\AITextures"
DEST_PATH = "/Game/LevelPrototyping/AITextures"

# (source filename, texture asset name, material asset name, UV tiling repeats,
#  roughness, metallic)
TEXTURES = [
    ("T_Wall_Concrete.png", "T_Wall_Concrete", "M_AI_Wall", 4.0, 0.85, 0.0),
    ("T_Ground_Concrete.png", "T_Ground_Concrete", "M_AI_Ground", 6.0, 0.8, 0.0),
    ("T_Ramp_DiamondPlate.png", "T_Ramp_DiamondPlate", "M_AI_Ramp", 4.0, 0.35, 0.7),
    ("T_Furniture_WoodMetal.png", "T_Furniture_WoodMetal", "M_AI_Furniture", 2.0, 0.55, 0.1),
    # Round 2: water + the Vehicle Bay/Docks/Harbor placeholder props, which
    # were all still using MAT_FURNITURE or a flat dynamic tint. Water's
    # tiling is much higher (250 vs. everything else's single digits) because
    # the water plane is 3000x3000m -- a mesh's UV0 spans 0-1 across the
    # whole scaled face regardless of size, so a small tiling value here would
    # stretch one copy of the image across the entire ocean instead of
    # repeating it. This is still a flat base-color image, not a real water
    # shader -- no waves/refraction/depth, just a low roughness so it at least
    # catches some specular sky reflection instead of looking totally matte.
    ("T_Water_Ocean.png", "T_Water_Ocean", "M_AI_Water", 250.0, 0.15, 0.0),
    ("T_Vehicle_OliveMetal.png", "T_Vehicle_OliveMetal", "M_AI_Vehicle", 2.0, 0.6, 0.3),
    ("T_Ship_Hull.png", "T_Ship_Hull", "M_AI_Ship", 6.0, 0.65, 0.3),
    ("T_Crane_Hazard.png", "T_Crane_Hazard", "M_AI_Crane", 3.0, 0.5, 0.4),
]

asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary


def safe(fn, label):
    """Runs fn(), logging a warning and continuing instead of aborting the whole script on failure."""
    try:
        return fn()
    except Exception as e:  # noqa: BLE001 -- deliberately broad, this is a one-shot editor tool
        unreal.log_warning(f"[AI Textures] Skipped '{label}': {e}")
        return None


def import_texture(filename, asset_name):
    src = os.path.join(SOURCE_DIR, filename)
    if not os.path.exists(src):
        unreal.log_error(f"[AI Textures] Missing source file: {src} -- did you move/rename the downloaded Meshy images into that folder?")
        return None

    task = unreal.AssetImportTask()
    task.set_editor_property("filename", src)
    task.set_editor_property("destination_path", DEST_PATH)
    task.set_editor_property("destination_name", asset_name)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("automated", True)
    task.set_editor_property("save", True)
    asset_tools.import_asset_tasks([task])

    tex = unreal.EditorAssetLibrary.load_asset(f"{DEST_PATH}/{asset_name}.{asset_name}")
    if tex is None:
        unreal.log_error(f"[AI Textures] Import failed for {filename} -- check the Output Log above for the importer's own error.")
    return tex


def get_or_create_material(material_name):
    full_path = f"{DEST_PATH}/{material_name}.{material_name}"
    if unreal.EditorAssetLibrary.does_asset_exist(full_path):
        mat = unreal.EditorAssetLibrary.load_asset(full_path)
        # Idempotent re-run: wipe the graph instead of duplicating nodes on top
        # of whatever was built last time.
        mel.delete_all_material_expressions(mat)
        return mat
    factory = unreal.MaterialFactoryNew()
    return asset_tools.create_asset(material_name, DEST_PATH, unreal.Material, factory)


def build_material(texture, material_name, tiling, roughness, metallic):
    material = get_or_create_material(material_name)
    if material is None:
        unreal.log_error(f"[AI Textures] Could not create/load material {material_name}")
        return None

    # UV tiling: TexCoord * tiling -> feeds the sample's UVs, so the seamless
    # source image repeats across a surface instead of one copy stretching
    # across an entire wall/floor that's tens of meters across.
    texcoord = mel.create_material_expression(material, unreal.MaterialExpressionTextureCoordinate, -500, -150)
    tile_mul = mel.create_material_expression(material, unreal.MaterialExpressionMultiply, -300, -150)
    tile_mul.set_editor_property("const_b", tiling)
    mel.connect_material_expressions(texcoord, "", tile_mul, "A")

    tex_sample = mel.create_material_expression(material, unreal.MaterialExpressionTextureSample, -100, -150)
    tex_sample.set_editor_property("texture", texture)
    mel.connect_material_expressions(tile_mul, "", tex_sample, "UVs")
    mel.connect_material_property(tex_sample, "RGB", unreal.MaterialProperty.MP_BASE_COLOR)

    rough_const = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -300, 100)
    rough_const.set_editor_property("r", roughness)
    mel.connect_material_property(rough_const, "", unreal.MaterialProperty.MP_ROUGHNESS)

    if metallic > 0.0:
        metal_const = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -300, 250)
        metal_const.set_editor_property("r", metallic)
        mel.connect_material_property(metal_const, "", unreal.MaterialProperty.MP_METALLIC)

    mel.layout_material_expressions(material)
    mel.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material)
    return material


def run():
    built = 0
    for filename, tex_name, mat_name, tiling, roughness, metallic in TEXTURES:
        tex = safe(lambda f=filename, n=tex_name: import_texture(f, n), f"import {filename}")
        if tex is None:
            continue
        mat = safe(
            lambda t=tex, m=mat_name, ti=tiling, r=roughness, me=metallic: build_material(t, m, ti, r, me),
            f"build material {mat_name}",
        )
        if mat is not None:
            built += 1
    unreal.log(f"[AI Textures] Built {built}/{len(TEXTURES)} material(s) at {DEST_PATH}.")


run()
