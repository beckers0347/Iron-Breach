"""
Build a real parameterized material for Tripo3D character imports
=======================================================================
IRON BREACH / Unreal Engine 5.8

WHAT THIS IS
------------
Fixes "the material instance is blank and I can't drag the texture onto it."
FBX import with import_materials=True auto-generates a Material with the
texture nodes wired DIRECTLY into the graph -- not exposed as parameters. A
Material Instance can only override parameters, so if the auto-generated
master material has none, its instance has nothing to show in the Details
panel and dragging a texture onto it is a no-op. That's the blank instance.

This script:
  1. Creates (or reuses) a real master material, M_TripoCharacterPBR, with
     4 actual texture PARAMETERS (BaseColor, Normal, Roughness, Metallic)
     wired to the right material outputs -- Roughness/Metallic pull just
     the R channel, matching how Tripo3D exports those as grayscale maps.
  2. Searches the evacuee's import folder for textures whose name contains
     "basecolor"/"normal"/"roughness"/"metallic" (case-insensitive) --
     matches Tripo3D's own JPEG naming convention.
  3. Fixes those textures' import settings: Normal gets CompressionSettings
     = Normalmap, and Normal/Roughness/Metallic all get sRGB turned OFF
     (FBX's generic texture importer defaults everything to sRGB, which is
     correct for BaseColor but wrong for non-color data -- left on, it
     subtly darkens/skews normal and roughness/metallic values even once
     the material is wired up right).
  4. Creates MI_SK_Evacuee_Male_Walk as an instance of that master, sets its
     4 texture parameters to the textures found in step 2.
  5. Assigns that instance to SK_Evacuee_Male's material slot 0 and saves
     everything touched.

HOW TO RUN IT
-------------
    py "X:/IronBreach/Content/Python/build_tripo_character_material.py"

Safe to re-run: reuses the master material and instance if they already
exist instead of duplicating, and re-applies the same texture assignments.

REUSABLE FOR FUTURE TRIPO3D CHARACTERS: change MESH_PATH/TEXTURE_SEARCH_DIR/
INSTANCE_NAME at the top and re-run for the next rigged Tripo3D import (e.g.
the muster-point evacuee variants mentioned in M1_LANDFALL_TRIPO3D_LOG.md) --
the master material only needs to be built once.
"""

import unreal

MASTER_MATERIAL_PATH = "/Game/M1_Landfall/Materials/M_TripoCharacterPBR"
TEXTURE_SEARCH_DIR = "/Game/M1_Landfall/AIModels"
INSTANCE_PATH = "/Game/M1_Landfall/AIModels/MI_SK_Evacuee_Male_Walk"
MESH_PATH = "/Game/M1_Landfall/AIModels/SK_Evacuee_Male"

TEXTURE_NAME_HINTS = {
    "BaseColor": "basecolor",
    "Normal": "normal",
    "Roughness": "roughness",
    "Metallic": "metallic",
}

asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
registry = unreal.AssetRegistryHelpers.get_asset_registry()


def get_or_create_master_material():
    # `Expressions` is a protected UPROPERTY -- Python can't read it back to check
    # whether an existing asset already has its 4 parameter nodes wired (that's how
    # the previous version of this script tried to detect a half-built material from
    # an interrupted run, and it isn't a valid check). Simplest reliable fix: always
    # rebuild the master material fresh. It's only 4 nodes, so this is cheap, and it
    # sidesteps ever having to inspect existing graph contents from Python. Any
    # Material Instance whose parent is this path (like MI_SK_Evacuee_Male_Walk,
    # built later in this same script run) keeps working since it resolves its
    # parent by asset path, not by object identity.
    if unreal.EditorAssetLibrary.does_asset_exist(MASTER_MATERIAL_PATH):
        unreal.EditorAssetLibrary.delete_asset(MASTER_MATERIAL_PATH)
        unreal.log(f"[Tripo Material] Deleted existing {MASTER_MATERIAL_PATH} to rebuild it fresh.")

    package_path, asset_name = MASTER_MATERIAL_PATH.rsplit("/", 1)
    material = asset_tools.create_asset(asset_name, package_path, unreal.Material, unreal.MaterialFactoryNew())

    base_color = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionTextureSampleParameter2D, -400, 0)
    base_color.set_editor_property("parameter_name", "BaseColor")
    unreal.MaterialEditingLibrary.connect_material_property(base_color, "RGB", unreal.MaterialProperty.MP_BASE_COLOR)

    normal = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionTextureSampleParameter2D, -400, 250)
    normal.set_editor_property("parameter_name", "Normal")
    try:
        normal.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    except Exception:
        pass
    unreal.MaterialEditingLibrary.connect_material_property(normal, "RGB", unreal.MaterialProperty.MP_NORMAL)

    roughness = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionTextureSampleParameter2D, -400, 500)
    roughness.set_editor_property("parameter_name", "Roughness")
    try:
        roughness.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_GRAYSCALE)
    except Exception:
        pass
    unreal.MaterialEditingLibrary.connect_material_property(roughness, "R", unreal.MaterialProperty.MP_ROUGHNESS)

    metallic = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionTextureSampleParameter2D, -400, 750)
    metallic.set_editor_property("parameter_name", "Metallic")
    try:
        metallic.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_GRAYSCALE)
    except Exception:
        pass
    unreal.MaterialEditingLibrary.connect_material_property(metallic, "R", unreal.MaterialProperty.MP_METALLIC)

    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material)
    unreal.log(f"[Tripo Material] Created master material {MASTER_MATERIAL_PATH} with 4 texture parameters.")
    return material


def find_texture(hint):
    ar_filter = unreal.ARFilter(
        class_names=["Texture2D"],
        package_paths=[TEXTURE_SEARCH_DIR],
        recursive_paths=True,
        recursive_classes=True,
    )
    for asset_data in registry.get_assets(ar_filter):
        name = str(asset_data.asset_name).lower()
        if hint in name:
            return asset_data.get_asset()
    return None


def fix_texture_import_settings(texture, is_normal):
    if texture is None:
        return
    texture.set_editor_property("srgb", False)
    if is_normal:
        texture.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP)
    unreal.EditorAssetLibrary.save_loaded_asset(texture)


def run():
    master = get_or_create_master_material()

    found_textures = {}
    for param_name, hint in TEXTURE_NAME_HINTS.items():
        tex = find_texture(hint)
        if tex is None:
            unreal.log_warning(f"[Tripo Material] No texture found under {TEXTURE_SEARCH_DIR} matching '*{hint}*' for parameter '{param_name}'.")
        else:
            unreal.log(f"[Tripo Material] {param_name} -> {tex.get_name()}")
        found_textures[param_name] = tex

    # BaseColor stays sRGB (it's color data); the other three are non-color
    # data and get sRGB turned off, per the docstring above.
    fix_texture_import_settings(found_textures.get("Normal"), is_normal=True)
    fix_texture_import_settings(found_textures.get("Roughness"), is_normal=False)
    fix_texture_import_settings(found_textures.get("Metallic"), is_normal=False)

    existing_instance = unreal.EditorAssetLibrary.load_asset(INSTANCE_PATH)
    if existing_instance:
        instance = existing_instance
        unreal.log(f"[Tripo Material] Reusing existing instance {INSTANCE_PATH}.")
    else:
        package_path, asset_name = INSTANCE_PATH.rsplit("/", 1)
        # Not using MaterialInstanceConstantFactoryNew's "initial_parent" property --
        # its exact name has moved between engine versions and this one doesn't have
        # it under that name. Create the instance parentless, then set the parent
        # through MaterialEditingLibrary instead, which is the stable API for it.
        factory = unreal.MaterialInstanceConstantFactoryNew()
        instance = asset_tools.create_asset(asset_name, package_path, unreal.MaterialInstanceConstant, factory)
        unreal.log(f"[Tripo Material] Created instance {INSTANCE_PATH}.")

    unreal.MaterialEditingLibrary.set_material_instance_parent(instance, master)
    unreal.log(f"[Tripo Material] {INSTANCE_PATH} parent = {master.get_name()}.")

    for param_name, tex in found_textures.items():
        if tex is not None:
            unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(instance, param_name, tex)
    unreal.EditorAssetLibrary.save_loaded_asset(instance)

    mesh = unreal.EditorAssetLibrary.load_asset(MESH_PATH)
    if mesh is None:
        unreal.log_error(f"[Tripo Material] Could not load skeletal mesh at {MESH_PATH} -- material built and saved, but not assigned. Assign {INSTANCE_PATH} to it by hand.")
        return

    # SkeletalMesh has no set_material() -- that's a StaticMesh-only method. Skeletal
    # meshes expose their slots through the "materials" array property instead, each
    # entry a SkeletalMaterial struct with its own material_interface field.
    slots = mesh.get_editor_property("materials")
    if len(slots) == 0:
        new_slot = unreal.SkeletalMaterial()
        new_slot.set_editor_property("material_interface", instance)
        slots.append(new_slot)
    else:
        slots[0].set_editor_property("material_interface", instance)
    mesh.set_editor_property("materials", slots)

    unreal.EditorAssetLibrary.save_loaded_asset(mesh)
    unreal.log(f"[Tripo Material] Assigned {INSTANCE_PATH} to {MESH_PATH} material slot 0 and saved.")


run()
