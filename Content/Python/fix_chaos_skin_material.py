"""
Fix the blank Chaos skin material
=====================================
IRON BREACH / Unreal Engine 5.8

WHAT THIS IS
------------
Same root cause as the evacuee's blank material (see build_tripo_character_
material.py): the "Chaos" skin's Material Instance has a parent with no
texture PARAMETERS to override, so it shows blank and dragging Chaos_texture0
onto it in the Details panel does nothing. This skin looks like it came in
through Tripo3D's DCC Bridge plugin rather than manual FBX+JPEG import
(generic names -- Chaos_texture0, a Material Instance just called "Material"
-- versus the evacuee's Tripo-named PBR set), and only has ONE texture where
the evacuee had four.

That texture's thumbnail (flat purple/magenta with fine noise) looks like a
tangent-space NORMAL map, not a base color texture -- this script checks the
texture's actual CompressionSettings property (set by whatever imported it)
rather than trusting the thumbnail, and wires it to the right material slot
either way:
  - If it's a normal map: plugs into Normal. BaseColor is left unset (white),
    so the character will render as flat white WITH correct surface detail --
    better than solid grey, but if this is genuinely all that exported, the
    skin still needs a real base color texture generated/exported before it
    looks right. This script tells you which case it hit.
  - If it's NOT a normal map: plugs into BaseColor as originally guessed.

Reuses M_TripoCharacterPBR (built for the evacuee -- same 4 parameters:
BaseColor/Normal/Roughness/Metallic) rather than building a second master
material, since one parameterized character material covers both skins.

HOW TO RUN IT
-------------
    py "X:/IronBreach/Content/Python/fix_chaos_skin_material.py"

Safe to re-run.
"""

import unreal

MASTER_MATERIAL_PATH = "/Game/M1_Landfall/Materials/M_TripoCharacterPBR"
TEXTURE_PATH = "/Game/Characters/Infantry/Skins/Chaos/Chaos_texture0"
INSTANCE_PATH = "/Game/Characters/Infantry/Skins/Chaos/Material"
MESH_PATH = "/Game/Characters/Infantry/Skins/Chaos/Chaos"


def run():
    master = unreal.EditorAssetLibrary.load_asset(MASTER_MATERIAL_PATH)
    if master is None:
        unreal.log_error(
            f"[Chaos Material] Could not load {MASTER_MATERIAL_PATH} -- run "
            f"build_tripo_character_material.py first, it creates this master material."
        )
        return

    texture = unreal.EditorAssetLibrary.load_asset(TEXTURE_PATH)
    if texture is None:
        unreal.log_error(f"[Chaos Material] Could not load texture at {TEXTURE_PATH}.")
        return

    compression = texture.get_editor_property("compression_settings")
    is_normal_map = (compression == unreal.TextureCompressionSettings.TC_NORMALMAP)
    target_param = "Normal" if is_normal_map else "BaseColor"

    unreal.log(
        f"[Chaos Material] {texture.get_name()}: compression_settings={compression} -> "
        f"treating as {'a NORMAL map' if is_normal_map else 'a BASE COLOR texture'}, "
        f"wiring to the '{target_param}' parameter."
    )
    if is_normal_map:
        unreal.log_warning(
            "[Chaos Material] Only a normal map was found for this skin -- no base color "
            "texture exists to assign. The character will render flat white with correct "
            "surface detail, not full color, until a base color texture is generated/exported "
            "for Chaos and assigned to the 'BaseColor' parameter too."
        )
        texture.set_editor_property("srgb", False)  # non-color data
        unreal.EditorAssetLibrary.save_loaded_asset(texture)

    instance = unreal.EditorAssetLibrary.load_asset(INSTANCE_PATH)
    if instance is None:
        unreal.log_error(f"[Chaos Material] Could not load Material Instance at {INSTANCE_PATH}.")
        return

    unreal.MaterialEditingLibrary.set_material_instance_parent(instance, master)
    unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(instance, target_param, texture)
    unreal.EditorAssetLibrary.save_loaded_asset(instance)
    unreal.log(f"[Chaos Material] {INSTANCE_PATH}: parent set to {master.get_name()}, {target_param} = {texture.get_name()}.")

    mesh = unreal.EditorAssetLibrary.load_asset(MESH_PATH)
    if mesh is None:
        unreal.log_error(f"[Chaos Material] Could not load skeletal mesh at {MESH_PATH} -- material fixed but not assigned. Assign {INSTANCE_PATH} to it by hand.")
        return

    slots = mesh.get_editor_property("materials")
    if len(slots) == 0:
        new_slot = unreal.SkeletalMaterial()
        new_slot.set_editor_property("material_interface", instance)
        slots.append(new_slot)
    else:
        slots[0].set_editor_property("material_interface", instance)
    mesh.set_editor_property("materials", slots)
    unreal.EditorAssetLibrary.save_loaded_asset(mesh)

    unreal.log(f"[Chaos Material] Assigned {INSTANCE_PATH} to {MESH_PATH} material slot 0 and saved.")


run()
