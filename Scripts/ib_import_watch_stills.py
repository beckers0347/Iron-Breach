"""Import the real 16:9 level captures stored beside the Watch textures.

Run with UnrealEditor-Cmd -run=pythonscript -script=<this file>.
Only the three named Watch texture assets are created/saved.
"""
from pathlib import Path
import unreal

project = Path(unreal.Paths.project_dir())
source = project / "Content/IronBreach/Watch/Stills/Source"
destination = "/Game/IronBreach/Watch/Stills"
names = ("T_Recon_CarrowGate", "T_Recon_Plains", "T_Recon_FiringLine")
for name in names:
    if not (source / (name + ".png")).is_file():
        raise FileNotFoundError(source / (name + ".png"))

for name in names:
    task = unreal.AssetImportTask()
    task.filename = str(source / (name + ".png"))
    task.destination_path = destination
    task.destination_name = name
    task.automated = True
    task.replace_existing = True
    task.save = False
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    texture = unreal.load_asset(destination + "/" + name)
    if not isinstance(texture, unreal.Texture2D):
        raise RuntimeError("Texture import failed: " + name)
    texture.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_UI)
    texture.set_editor_property("srgb", True)
    if not unreal.EditorAssetLibrary.save_loaded_asset(texture):
        raise RuntimeError("Texture save failed: " + name)
    unreal.log("IBRECON: imported " + texture.get_path_name())
