"""
Carrowgate Garrison -- AI 3D model import (Meshy)
====================================================
IRON BREACH / Unreal Engine 5.8

WHAT THIS IS
------------
Pilot for replacing placeholder prop boxes with real Meshy-generated 3D
models. First (only, for now) entry: the Vehicle Bay cargo truck, generated
via Meshy's Model -> Text to 3D tab and downloaded as an FBX with Resize ON,
Height=280cm, Origin=Bottom (so the mesh's local origin sits at its base --
it drops straight onto a pad's top surface with no extra Z offset needed).

The download is untextured (grey clay mesh) -- rather than spend a second
Meshy credit pass on model texturing, this script applies the SAME
MAT_AI_Vehicle material built by import_ai_textures.py (the olive-drab
texture already used on the placeholder boxes), so the real mesh and any
remaining placeholder boxes match.

The mesh itself is very high-poly (~1.4M triangles for the truck) since it
came out of Meshy's high-detail preset uncut. Rather than manually decimate,
this script enables Nanite on import -- UE5's virtualized geometry handles
that face count fine at runtime without a manual LOD/retopo pass.

Raw Meshy exports also have no simple collision, which means UE defaults to
per-triangle COMPLEX collision for physics/overlap queries -- i.e. all 1.4M
faces, every query. That's the actual cause if PIE gets laggy right after
this mesh goes in (Nanite handles the rendering fine; collision doesn't get
the same treatment for free). This script adds a simple box collision and
forces CTF_USE_SIMPLE_AS_COMPLEX so the complex collision is never touched.

HOW TO RUN IT
-------------
1. Download the model from Meshy (Download Settings: Resize ON, Height in
   cm, Origin=Bottom, Format=fbx). It lands in your OS Downloads folder --
   Chrome downloads aren't visible to this project directly.
2. Move/rename the file into:
       X:\\IronBreach\\Content\\LevelPrototyping\\AIModels\\SM_Truck_Cargo.fbx
   (create the AIModels folder if it doesn't exist yet)
3. Run this script from the Output Log console:
       py "X:/IronBreach/Content/Python/import_ai_models.py"
   or the dedicated Python console tab:
       exec(open("X:/IronBreach/Content/Python/import_ai_models.py").read())
4. Re-run build_carrowgate_garrison.py -- it checks for this mesh by path
   and swaps the first Vehicle Bay placeholder box for the real truck if
   found, leaving the other two boxes as-is (pilot scope, per plan).

Safe to re-run: existing mesh assets get re-imported in place rather than
duplicated.
"""

import os
import unreal

SOURCE_DIR = r"X:\IronBreach\Content\LevelPrototyping\AIModels"
DEST_PATH = "/Game/LevelPrototyping/AIModels"

# (source filename, destination asset name, material asset path to apply, or None)
MODELS = [
    ("SM_Truck_Cargo.fbx", "SM_Truck_Cargo", "/Game/LevelPrototyping/AITextures/M_AI_Vehicle.M_AI_Vehicle"),
]

asset_tools = unreal.AssetToolsHelpers.get_asset_tools()


def safe(fn, label):
    """Runs fn(), logging a warning and continuing instead of aborting the whole script on failure."""
    try:
        return fn()
    except Exception as e:  # noqa: BLE001 -- deliberately broad, this is a one-shot editor tool
        unreal.log_warning(f"[AI Models] Skipped '{label}': {e}")
        return None


def import_model(filename, asset_name):
    src = os.path.join(SOURCE_DIR, filename)
    if not os.path.exists(src):
        unreal.log_error(
            f"[AI Models] Missing source file: {src} -- did you move/rename the "
            f"downloaded Meshy FBX into that folder? See this script's docstring."
        )
        return None

    task = unreal.AssetImportTask()
    task.set_editor_property("filename", src)
    task.set_editor_property("destination_path", DEST_PATH)
    task.set_editor_property("destination_name", asset_name)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("automated", True)
    task.set_editor_property("save", True)

    options = unreal.FbxImportUI()
    options.set_editor_property("import_mesh", True)
    options.set_editor_property("import_as_skeletal", False)
    options.set_editor_property("import_materials", False)  # we apply our own AI-texture material instead
    options.set_editor_property("import_textures", False)
    try:
        options.static_mesh_import_data.set_editor_property("combine_meshes", True)
    except Exception:
        pass  # not fatal -- some Fbx exports are already a single mesh
    task.set_editor_property("options", options)

    asset_tools.import_asset_tasks([task])

    mesh = unreal.EditorAssetLibrary.load_asset(f"{DEST_PATH}/{asset_name}.{asset_name}")
    if mesh is None:
        unreal.log_error(f"[AI Models] Import failed for {filename} -- check the Output Log above for the importer's own error.")
    return mesh


def apply_material(mesh, material_path):
    if mesh is None or not material_path:
        return
    mat = unreal.EditorAssetLibrary.load_asset(material_path)
    if mat is None:
        unreal.log_warning(f"[AI Models] Material not found at '{material_path}' -- mesh left with its imported/default material.")
        return
    mesh.set_material(0, mat)


def enable_nanite(mesh):
    """Meshy's high-detail export is ~1.4M tris for the truck -- Nanite handles
    that natively instead of needing a manual decimate/LOD pass."""
    if mesh is None:
        return
    settings = mesh.get_editor_property("nanite_settings")
    settings.set_editor_property("enabled", True)
    mesh.set_editor_property("nanite_settings", settings)


def fix_collision(mesh):
    """Raw Meshy exports have no simple collision defined, so without this UE falls
    back to COMPLEX collision -- literally all 1.4M triangles -- for every physics/
    overlap/line-trace query against this actor. That's almost certainly why PIE got
    laggy the moment the real truck mesh went in. A single box is plenty for a
    background vehicle prop, and forcing CTF_USE_SIMPLE_AS_COMPLEX means the engine
    never touches the per-triangle collision at all, even for traces that would
    normally ask for "complex"."""
    if mesh is None:
        return
    unreal.EditorStaticMeshLibrary.add_simple_collisions(mesh, unreal.ScriptCollisionShapeType.BOX)
    body_setup = mesh.get_editor_property("body_setup")
    if body_setup is not None:
        body_setup.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_SIMPLE_AS_COMPLEX)


def run():
    built = 0
    for filename, asset_name, material_path in MODELS:
        mesh = safe(lambda f=filename, n=asset_name: import_model(f, n), f"import {filename}")
        if mesh is None:
            continue
        safe(lambda m=mesh, mp=material_path: apply_material(m, mp), f"apply material for {asset_name}")
        safe(lambda m=mesh: enable_nanite(m), f"enable Nanite for {asset_name}")
        safe(lambda m=mesh: fix_collision(m), f"fix collision for {asset_name}")
        unreal.EditorAssetLibrary.save_loaded_asset(mesh)
        built += 1
    unreal.log(f"[AI Models] Imported {built}/{len(MODELS)} model(s) at {DEST_PATH}.")


run()
