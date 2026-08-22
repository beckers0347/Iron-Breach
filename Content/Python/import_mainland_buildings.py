"""
Import the 9 Tripo3D building models into /Game/Environment/CGMainland/AIModels
====================================================================================
IRON BREACH / Unreal Engine 5.8

WHAT THIS IS
------------
The 9 building models for build_carrowgate_mainland.py's BUILDING_ASSET_KIT were
generated in Tripo3D (Text-to-3D) and exported as FBX+textures, downloaded to
X:/Downloads/SM_Building_*.zip, then unzipped locally into
X:/Downloads/TripoExports/SM_Building_<Name>/ (one .fbx + one .fbm texture
folder per building -- the .fbx filename itself is a random Tripo UUID, not the
building name, so this script finds it by globbing for *.fbx inside each
building's folder rather than hardcoding it).

This script imports each FBX as a StaticMesh with materials+textures, combined
into a single mesh per building (Rowhouse in particular came out of Tripo as 3
separate townhouse meshes -- combine_meshes=True merges them into one
SM_Building_Rowhouse asset, matching what build_carrowgate_mainland.py expects
at a single asset path), and saves it at:

    /Game/Environment/CGMainland/AIModels/SM_Building_<Name>

Once these exist, build_carrowgate_mainland.py's real_or_placeholder() picks
them up automatically on the next run -- no changes needed to that script.

Letting Unreal's own FBX importer wire the materials (import_materials=True)
rather than post-processing textures by filename: Tripo's texture filenames
here are mostly generic hashes (only Roughness/Metallic are labeled), but the
FBX's own material definition already tells Unreal which texture is BaseColor
vs Normal vs Roughness vs Metallic, so the auto-generated per-mesh Material
comes out correctly wired without us needing to guess from filenames.

HOW TO RUN IT
-------------
    py "X:/IronBreach/Content/Python/import_mainland_buildings.py"

Safe to re-run: skips any building whose asset already exists at its target
path unless FORCE_REIMPORT is set to True below.
"""

import glob
import os

import unreal

SOURCE_ROOT = "X:/Downloads/TripoExports"
DEST_PACKAGE_PATH = "/Game/Environment/CGMainland/AIModels"

BUILDING_NAMES = [
    "Cottage", "Apartment", "Warehouse", "Tower", "Shopfront",
    "Rowhouse", "Spire", "Garage", "Ruin",
]

FORCE_REIMPORT = False  # set True to re-import and overwrite even if the asset already exists

asset_tools = unreal.AssetToolsHelpers.get_asset_tools()


def find_fbx(building_name):
    folder = f"{SOURCE_ROOT}/SM_Building_{building_name}"
    matches = glob.glob(os.path.join(folder, "*.fbx"))
    if not matches:
        unreal.log_error(f"[Mainland Buildings] No .fbx found in {folder} for '{building_name}'.")
        return None
    if len(matches) > 1:
        unreal.log_warning(f"[Mainland Buildings] Multiple .fbx files in {folder} -- using {matches[0]}.")
    return matches[0].replace("\\", "/")


def import_building(building_name):
    asset_name = f"SM_Building_{building_name}"
    dest_path = f"{DEST_PACKAGE_PATH}/{asset_name}"

    if not FORCE_REIMPORT and unreal.EditorAssetLibrary.does_asset_exist(dest_path):
        unreal.log(f"[Mainland Buildings] {asset_name} already exists -- skipping (set FORCE_REIMPORT=True to redo).")
        return True

    fbx_path = find_fbx(building_name)
    if fbx_path is None:
        return False

    options = unreal.FbxImportUI()
    options.import_mesh = True
    options.import_as_skeletal = False
    options.import_materials = True
    options.import_textures = True
    options.import_animations = False
    options.create_physics_asset = False

    try:
        mesh_data = options.static_mesh_import_data
        mesh_data.combine_meshes = True
        mesh_data.generate_lightmap_u_vs = True
        mesh_data.auto_generate_collision = True
    except Exception as exc:
        unreal.log_warning(f"[Mainland Buildings] {asset_name}: couldn't set static_mesh_import_data options ({exc}) -- continuing with defaults.")

    task = unreal.AssetImportTask()
    task.filename = fbx_path
    task.destination_path = DEST_PACKAGE_PATH
    task.destination_name = asset_name
    task.replace_existing = True
    task.automated = True
    task.save = True
    task.options = options

    asset_tools.import_asset_tasks([task])

    if unreal.EditorAssetLibrary.does_asset_exist(dest_path):
        unreal.log(f"[Mainland Buildings] Imported {asset_name} -> {dest_path}")
        return True
    else:
        unreal.log_error(f"[Mainland Buildings] Import task ran but {dest_path} doesn't exist -- check the Output Log above for FBX import errors/warnings.")
        return False


def run():
    ok, failed = [], []
    for name in BUILDING_NAMES:
        if import_building(name):
            ok.append(name)
        else:
            failed.append(name)

    unreal.log(f"[Mainland Buildings] Done. {len(ok)}/{len(BUILDING_NAMES)} imported: {', '.join(ok)}")
    if failed:
        unreal.log_error(f"[Mainland Buildings] Failed: {', '.join(failed)} -- see errors above.")
    else:
        unreal.log("[Mainland Buildings] All 9 buildings imported. Re-run build_carrowgate_mainland.py to swap placeholders for these.")


run()
