"""Assign the generated Kaiju Chitin loot icon to the existing KaijuChitin item definition.

Run with UnrealEditor-Cmd <project> -run=pythonscript -script=<this file> -SCCProvider=None.

Imports Art/MenuSources/kaiju-chitin-v1.png as /Game/Items/Icons/Generated/T_Icon_KaijuChitin
(next to the existing generated weapon icons) and sets ONLY the Icon field of the one
actual KaijuChitin UIBItemDefinition. Every other field, asset, map and save file stays
untouched. Refuses to guess: zero or several candidate definitions abort without changes.
"""
from pathlib import Path
import unreal

ICON_DIR = '/Game/Items/Icons/Generated'
ICON_NAME = 'T_Icon_KaijuChitin'
SOURCE = Path(unreal.Paths.project_dir()) / 'Art/MenuSources/kaiju-chitin-v1.png'
SEARCH_ROOTS = ('/Game/Items', '/Game/IronBreach/Items', '/Game/Weapons')
EAL = unreal.EditorAssetLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()


def log(message):
    unreal.log('[KaijuChitinIcon] ' + message)


def find_definitions():
    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    registry.search_all_assets(synchronous_search=True)
    found = []
    for root in SEARCH_ROOTS:
        for data in registry.get_assets_by_path(root, recursive=True):
            name = str(data.asset_name)
            if 'kaijuchitin' not in name.lower().replace('_', '').replace('-', ''):
                continue
            asset = data.get_asset()
            if isinstance(asset, unreal.IBItemDefinition) and asset not in found:
                found.append(asset)
    return found


def main():
    if not SOURCE.is_file():
        raise SystemExit('[KaijuChitinIcon] source PNG missing: %s' % SOURCE)

    definitions = find_definitions()
    if len(definitions) != 1:
        for definition in definitions:
            log('candidate: ' + definition.get_path_name())
        raise SystemExit('[KaijuChitinIcon] expected exactly one KaijuChitin item definition, found %d; nothing changed'
                         % len(definitions))
    definition = definitions[0]
    category = definition.get_editor_property('category')
    if category != unreal.IBItemCategory.KAIJU_MATERIAL:
        raise SystemExit('[KaijuChitinIcon] %s is not a Kaiju Material definition (%s); nothing changed'
                         % (definition.get_path_name(), category))
    previous = definition.get_editor_property('icon')
    log('definition: %s (current icon: %s)' % (definition.get_path_name(), str(previous) if previous else 'none'))

    task = unreal.AssetImportTask()
    task.set_editor_property('filename', str(SOURCE.resolve()))
    task.set_editor_property('destination_path', ICON_DIR)
    task.set_editor_property('destination_name', ICON_NAME)
    task.set_editor_property('automated', True)
    task.set_editor_property('replace_existing', True)
    task.set_editor_property('save', True)
    AT.import_asset_tasks([task])
    texture = EAL.load_asset(ICON_DIR + '/' + ICON_NAME)
    if not texture:
        raise SystemExit('[KaijuChitinIcon] icon import failed; definition unchanged')
    # Same treatment as the other generated loot icons: UI group, no mips, sRGB.
    texture.set_editor_property('lod_group', unreal.TextureGroup.TEXTUREGROUP_UI)
    texture.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_EDITOR_ICON)
    texture.set_editor_property('mip_gen_settings', unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
    texture.set_editor_property('srgb', True)
    EAL.save_loaded_asset(texture)

    definition.set_editor_property('icon', texture)
    if not EAL.save_loaded_asset(definition):
        raise SystemExit('[KaijuChitinIcon] could not save %s' % definition.get_path_name())
    log('assigned %s -> %s.Icon; no other fields touched' % (texture.get_path_name(), definition.get_path_name()))


main()
