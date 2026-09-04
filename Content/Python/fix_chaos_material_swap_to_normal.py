"""
Move Chaos_texture0 from BaseColor to Normal
================================================
IRON BREACH / Unreal Engine 5.8

WHAT THIS IS
------------
fix_chaos_skin_material.py's compression_settings check said Chaos_texture0
wasn't a normal map, so it wired it to BaseColor -- but the material preview
sphere renders flat grey with the texture there, and the texture's own
thumbnail (flat purple/magenta with fine noise) is a textbook tangent-space
normal map. The compression_settings check gave a false negative: whatever
imported this texture (Tripo3D's DCC Bridge plugin, going by this skin's
generic Chaos_texture0/Material naming) never tagged it as a normal map on
import, so the property read "not normal" even though the pixel content is.

This script trusts the visual/content evidence over that property and wires
Normal = Chaos_texture0, plus fixes the texture's own import settings
(CompressionSettings -> Normalmap, sRGB off) so it actually decodes as
normal data instead of color data. It logs a manual step for BaseColor
(no reliable Python call to un-check a single instance parameter override
in this engine version) -- see the warning it prints.

After this runs, the character will show correct surface detail but still no
actual color (flat white-ish, since there's no base color texture at all for
this skin) -- that's expected, not a leftover bug. A real BaseColor texture
needs to be generated/exported for Chaos before this skin has actual color;
this script doesn't invent one.

HOW TO RUN IT
-------------
    py "X:/IronBreach/Content/Python/fix_chaos_material_swap_to_normal.py"
"""

import unreal

TEXTURE_PATH = "/Game/Characters/Infantry/Skins/Chaos/Chaos_texture0"
INSTANCE_PATH = "/Game/Characters/Infantry/Skins/Chaos/Material"


def run():
    texture = unreal.EditorAssetLibrary.load_asset(TEXTURE_PATH)
    instance = unreal.EditorAssetLibrary.load_asset(INSTANCE_PATH)
    if texture is None or instance is None:
        unreal.log_error(f"[Chaos Material] Could not load texture or instance -- checked {TEXTURE_PATH} and {INSTANCE_PATH}.")
        return

    texture.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP)
    texture.set_editor_property("srgb", False)
    unreal.EditorAssetLibrary.save_loaded_asset(texture)
    unreal.log(f"[Chaos Material] {texture.get_name()}: CompressionSettings -> Normalmap, sRGB -> off.")

    unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(instance, "Normal", texture)
    unreal.EditorAssetLibrary.save_loaded_asset(instance)
    unreal.log(f"[Chaos Material] {instance.get_name()}: Normal = {texture.get_name()}.")
    unreal.log_warning(
        "[Chaos Material] BaseColor's override still points at this same normal map (there's no reliable "
        "'clear this one override' Python call in this engine version) -- in the Material Instance editor, "
        "uncheck the BaseColor checkbox (the same one shown checked in your screenshot) to reset it to the "
        "master's default instead of showing this texture as color. Then generate/export a real base color "
        "texture for Chaos and check BaseColor back on with that instead, once one exists."
    )


run()
