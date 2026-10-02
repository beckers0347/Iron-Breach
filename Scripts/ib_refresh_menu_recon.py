"""Refresh the shared Watch/Missions Carrow thumbnail from the captured current fortress."""
from pathlib import Path
import unreal

task = unreal.AssetImportTask()
task.set_editor_property('filename', str((Path(unreal.Paths.project_dir()) / 'Art/MenuSources/carrow-gate-recon-v1.png').resolve()))
task.set_editor_property('destination_path','/Game/IronBreach/Watch/Stills')
task.set_editor_property('destination_name','T_Recon_CarrowGate')
task.set_editor_property('automated',True)
task.set_editor_property('replace_existing',True)
task.set_editor_property('save',True)
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
texture=unreal.EditorAssetLibrary.load_asset('/Game/IronBreach/Watch/Stills/T_Recon_CarrowGate')
assert texture
texture.set_editor_property('lod_group',unreal.TextureGroup.TEXTUREGROUP_UI)
texture.set_editor_property('mip_gen_settings',unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
unreal.EditorAssetLibrary.save_loaded_asset(texture)
unreal.log('REFERENCE MENUS: current fortress recon saved')
