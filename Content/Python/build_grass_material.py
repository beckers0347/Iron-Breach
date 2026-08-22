"""
Build a tiled grass ground material from the Iceland landscaping pack
========================================================================
IRON BREACH / Unreal Engine 5.8

WHAT THIS IS
------------
build_carrowgate_mainland.py's MountainGroundPad (and CityGroundPad) use a
flat, untextured fallback ground material (M_AI_Ground) -- fine as a
blockout, but Shane asked for the ground around the mountains to actually
read as grass. The Iceland landscaping pack already ships grass textures
(T_Iceland_Grass_BaseColor/_Normal/_ORM under
/Game/Landscaping/IcelandEnviroment/Textures/T_Iceland_Grass) but no
standalone Material wired up to use them on an ordinary StaticMeshComponent
-- the pack's own materials (M_AutoLandscape, M_Iceland_Mountains, etc.) are
built for UE's Landscape terrain system (weightmap/RVT-blended layers), not a
flat ground plane, so this builds a plain, simple Material instead: same
from-scratch MaterialEditingLibrary approach build_water_material.py already
uses successfully in this project for M_AI_Water.

  - BaseColor <- T_Iceland_Grass_BaseColor, tiled (repeated) across UV space
    so it doesn't stretch into a single blurry smear across a ground pad
    that's hundreds of meters across.
  - Normal <- T_Iceland_Grass_Normal (same tiling).
  - T_Iceland_Grass_ORM is a packed Occlusion(R)/Roughness(G)/Metallic(B)
    texture (standard UE packing) -- wired to AmbientOcclusion/Roughness/
    Metallic respectively.

Saved as M_AI_Grass alongside the project's other AI-blockout materials at
/Game/LevelPrototyping/AITextures/M_AI_Grass, so build_carrowgate_mainland.py
can load it the same way it already loads M_AI_Ground/M_AI_Wall.

HOW TO RUN IT
-------------
    py "X:/IronBreach/Content/Python/build_grass_material.py"

Then re-run build_carrowgate_mainland.py to pick it up.

Safe to re-run: wipes and rebuilds M_AI_Grass's graph in place.
"""

import unreal

TEXTURE_DIR = "/Game/Landscaping/IcelandEnviroment/Textures/T_Iceland_Grass"
BASECOLOR_PATH = f"{TEXTURE_DIR}/T_Iceland_Grass_BaseColor.T_Iceland_Grass_BaseColor"
NORMAL_PATH = f"{TEXTURE_DIR}/T_Iceland_Grass_Normal.T_Iceland_Grass_Normal"
ORM_PATH = f"{TEXTURE_DIR}/T_Iceland_Grass_ORM.T_Iceland_Grass_ORM"

MATERIAL_PATH_DIR = "/Game/LevelPrototyping/AITextures"
MATERIAL_NAME = "M_AI_Grass"

TILE_COUNT = 60.0  # how many times the texture repeats across the ground pad's UV space

asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary


def run():
    basecolor_tex = unreal.EditorAssetLibrary.load_asset(BASECOLOR_PATH)
    normal_tex = unreal.EditorAssetLibrary.load_asset(NORMAL_PATH)
    orm_tex = unreal.EditorAssetLibrary.load_asset(ORM_PATH)
    if basecolor_tex is None or normal_tex is None or orm_tex is None:
        unreal.log_error(
            f"[Grass Material] One or more grass textures not found under {TEXTURE_DIR} -- "
            f"basecolor={basecolor_tex is not None} normal={normal_tex is not None} orm={orm_tex is not None}.")
        return

    full_path = f"{MATERIAL_PATH_DIR}/{MATERIAL_NAME}.{MATERIAL_NAME}"
    if unreal.EditorAssetLibrary.does_asset_exist(full_path):
        material = unreal.EditorAssetLibrary.load_asset(full_path)
        mel.delete_all_material_expressions(material)
    else:
        factory = unreal.MaterialFactoryNew()
        material = asset_tools.create_asset(MATERIAL_NAME, MATERIAL_PATH_DIR, unreal.Material, factory)

    if material is None:
        unreal.log_error("[Grass Material] Could not create/load M_AI_Grass.")
        return

    # ---- Shared tiled UVs ----
    texcoord = mel.create_material_expression(material, unreal.MaterialExpressionTextureCoordinate, -900, 0)
    tiled_uv = mel.create_material_expression(material, unreal.MaterialExpressionMultiply, -700, 0)
    tiled_uv.set_editor_property("const_b", TILE_COUNT)
    mel.connect_material_expressions(texcoord, "", tiled_uv, "A")

    # ---- BaseColor ----
    basecolor_sample = mel.create_material_expression(material, unreal.MaterialExpressionTextureSample, -450, -250)
    basecolor_sample.set_editor_property("texture", basecolor_tex)
    mel.connect_material_expressions(tiled_uv, "", basecolor_sample, "UVs")
    mel.connect_material_property(basecolor_sample, "RGB", unreal.MaterialProperty.MP_BASE_COLOR)

    # ---- Normal ----
    normal_sample = mel.create_material_expression(material, unreal.MaterialExpressionTextureSample, -450, 50)
    normal_sample.set_editor_property("texture", normal_tex)
    normal_sample.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    mel.connect_material_expressions(tiled_uv, "", normal_sample, "UVs")
    mel.connect_material_property(normal_sample, "RGB", unreal.MaterialProperty.MP_NORMAL)

    # ---- ORM: standard UE packing, R=AO G=Roughness B=Metallic ----
    orm_sample = mel.create_material_expression(material, unreal.MaterialExpressionTextureSample, -450, 350)
    orm_sample.set_editor_property("texture", orm_tex)
    orm_sample.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR)
    mel.connect_material_expressions(tiled_uv, "", orm_sample, "UVs")
    mel.connect_material_property(orm_sample, "R", unreal.MaterialProperty.MP_AMBIENT_OCCLUSION)
    mel.connect_material_property(orm_sample, "G", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.connect_material_property(orm_sample, "B", unreal.MaterialProperty.MP_METALLIC)

    mel.layout_material_expressions(material)
    mel.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material)
    unreal.log(f"[Grass Material] Built {MATERIAL_NAME} at {full_path} (tiled {TILE_COUNT}x).")


run()
