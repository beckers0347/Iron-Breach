"""Import the reference-menu background and a UI material for the live operative capture.
Run with UnrealEditor-Cmd -run=pythonscript -script=<this file> -SCCProvider=None.
Only owns /Game/IronBreach/UI/Hangar; no map edits or save-game mutations.
"""
from pathlib import Path
import unreal

ROOT = '/Game/IronBreach/UI/Hangar'
EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
source = Path(unreal.Paths.project_dir()) / 'Art/MenuSources/hangar-v1.png'
task = unreal.AssetImportTask()
task.set_editor_property('filename', str(source.resolve()))
task.set_editor_property('destination_path', ROOT)
task.set_editor_property('destination_name', 'T_MenuHangar')
task.set_editor_property('automated', True)
task.set_editor_property('replace_existing', True)
task.set_editor_property('save', True)
AT.import_asset_tasks([task])
texture = EAL.load_asset(ROOT + '/T_MenuHangar')
assert texture, 'Hangar import failed'
texture.set_editor_property('lod_group', unreal.TextureGroup.TEXTUREGROUP_UI)
texture.set_editor_property('compression_settings', unreal.TextureCompressionSettings.TC_EDITOR_ICON)
texture.set_editor_property('mip_gen_settings', unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
texture.set_editor_property('srgb', True)
EAL.save_loaded_asset(texture)

target = EAL.load_asset(ROOT + '/RT_PortraitDefault') if EAL.does_asset_exist(ROOT + '/RT_PortraitDefault') else AT.create_asset('RT_PortraitDefault',ROOT,unreal.TextureRenderTarget2D,unreal.TextureRenderTargetFactoryNew())
target.set_editor_property('render_target_format',unreal.TextureRenderTargetFormat.RTF_RGBA16F)
target.set_editor_property('force_linear_gamma',True)
target.set_editor_property('srgb',False)
target.set_editor_property('clear_color',unreal.LinearColor(0,0,0,1))
EAL.save_loaded_asset(target)
material = EAL.load_asset(ROOT+'/M_OperativePortrait') if EAL.does_asset_exist(ROOT+'/M_OperativePortrait') else AT.create_asset('M_OperativePortrait',ROOT,unreal.Material,unreal.MaterialFactoryNew())
MEL.delete_all_material_expressions(material)
material.set_editor_property('material_domain',unreal.MaterialDomain.MD_UI)
material.set_editor_property('blend_mode',unreal.BlendMode.BLEND_TRANSLUCENT)
sample = MEL.create_material_expression(material,unreal.MaterialExpressionTextureSampleParameter2D)
sample.set_editor_property('parameter_name','Portrait')
sample.set_editor_property('texture',target)
sample.set_editor_property('sampler_type',unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR)
alpha = MEL.create_material_expression(material,unreal.MaterialExpressionOneMinus)
assert MEL.connect_material_expressions(sample,'A',alpha,'')
assert MEL.connect_material_property(alpha,'',unreal.MaterialProperty.MP_OPACITY)
# Tone-map only the isolated HDR capture; the backdrop is already display-referred.
tone = MEL.create_material_expression(material,unreal.MaterialExpressionCustom)
tone.set_editor_property('code','float3 x=max(Color,0); return saturate((x*(2.51*x+0.03))/(x*(2.43*x+0.59)+0.14));')
tone.set_editor_property('output_type',unreal.CustomMaterialOutputType.CMOT_FLOAT3)
inp=unreal.CustomInput(); inp.set_editor_property('input_name','Color')
tone.set_editor_property('inputs',[inp])
assert MEL.connect_material_expressions(sample,'RGB',tone,'Color')
assert MEL.connect_material_property(tone,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR)
MEL.layout_material_expressions(material)
MEL.recompile_material(material)
EAL.save_loaded_asset(material)
unreal.log('REFERENCE MENUS: background and transparent portrait material saved')
