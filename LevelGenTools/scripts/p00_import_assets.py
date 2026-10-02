"""p00_import_assets.py - import the Blender/Tripo FBX files and PBR textures into Content.

Run once (safe to re-run: existing assets are skipped unless FORCE = True).
In the UE Output Log:   py "X:/IronBreach/LevelGenTools/scripts/p00_import_assets.py"

Look for:
  [Thornfield] Imported <key>: <n> asset(s)
  [Thornfield] VERIFY: import_buildings PASS
  [Thornfield] VERIFY: import_nature PASS
  [Thornfield] VERIFY: import_textures PASS
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import unreal
import importlib
import gen_common as G
importlib.reload(G)   # UE keeps Python modules loaded between runs; pick up edits

LEGACY = False  # set in main()
FORCE = False   # True = re-import and overwrite existing assets


def _prefer_legacy_fbx():
    """UE 5.8 imports FBX through Interchange, which ignores the FbxImportUI options (and drops
    UCX_ hulls unless its mesh pipeline says otherwise). Switch FBX back to the legacy importer."""
    for cmd in ("Interchange.FeatureFlags.Import.FBX 0",):
        try:
            unreal.SystemLibrary.execute_console_command(None, cmd)
        except Exception as e:
            G.warn("console command failed %s: %r" % (cmd, e))
    try:
        still_on = unreal.SystemLibrary.get_console_variable_bool_value("Interchange.FeatureFlags.Import.FBX")
    except Exception:
        still_on = None
    G.log("Interchange FBX import flag after switch: %s (False = legacy importer active)" % still_on)
    return still_on is False


def _interchange_pipeline():
    """Fallback when Interchange stays active: build a generic pipeline asking for collision."""
    try:
        pipe = unreal.InterchangeGenericAssetsPipeline()
    except Exception as e:
        G.warn("InterchangeGenericAssetsPipeline unavailable: %r" % e)
        return None
    targets = [pipe]
    for sub in ("mesh_pipeline", "common_meshes_properties"):
        try:
            targets.append(pipe.get_editor_property(sub))
        except Exception:
            pass
    wanted = {"import_collision": True, "one_convex_hull_per_ucx": True, "combine_static_meshes": True,
              "force_all_mesh_as_type": None, "build_nanite": True, "generate_lightmap_u_vs": False}
    applied = []
    for t in targets:
        for prop, val in wanted.items():
            if val is None:
                continue
            try:
                t.set_editor_property(prop, val)
                applied.append(prop)
            except Exception:
                pass
    G.log("Interchange pipeline properties applied: %s" % sorted(set(applied)))
    if "import_collision" not in applied:
        G.warn("Could not find import_collision on the Interchange pipeline. Properties on pipeline: %s"
               % [p for p in dir(pipe) if "coll" in p.lower() or "mesh" in p.lower()][:40])
    return pipe


def _split(path):
    folder, name = path.rsplit("/", 1)
    return folder, name


def _fbx_options(is_building):
    ui = unreal.FbxImportUI()
    ui.set_editor_property("import_mesh", True)
    ui.set_editor_property("import_as_skeletal", False)
    ui.set_editor_property("import_animations", False)
    ui.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_STATIC_MESH)
    # Buildings: materials are built in Phase 7. Tripo models: keep their embedded textures.
    ui.set_editor_property("import_materials", not is_building)
    ui.set_editor_property("import_textures", not is_building)
    sm = ui.static_mesh_import_data
    # Buildings keep door meshes as separate assets (so they can be animated).
    sm.set_editor_property("combine_meshes", not is_building)
    sm.set_editor_property("auto_generate_collision", False)   # UCX_ meshes supply collision
    sm.set_editor_property("one_convex_hull_per_ucx", True)
    sm.set_editor_property("generate_lightmap_u_vs", False)
    sm.set_editor_property("import_uniform_scale", 1.0)
    for prop, val in (("build_nanite", True),):
        try:
            sm.set_editor_property(prop, val)
        except Exception as e:
            G.warn("Could not set %s (%s) - enable Nanite by hand on these meshes" % (prop, e))
    return ui


def _simple_collision_count(mesh):
    try:
        agg = mesh.get_editor_property("body_setup").get_editor_property("agg_geom")
        return sum(len(agg.get_editor_property(p)) for p in ("convex_elems", "box_elems", "sphere_elems", "sphyl_elems"))
    except Exception:
        return 0


def _import_body(key, entry):
    """Re-import the main mesh from the body-only FBX (body + UCX hulls) as ONE mesh,
    because UE ignores UCX_ hulls when the FBX is imported with Combine Meshes OFF."""
    src = os.path.join(G.project_dir(), entry["body_source"].replace("/", os.sep))
    if not os.path.isfile(src):
        raise G.GenError("Body FBX missing: %s" % src)
    main_path = "%s/%s" % (entry["dest"], entry["main_mesh"])
    existing = unreal.EditorAssetLibrary.load_asset(main_path)
    if existing is not None and not FORCE and _simple_collision_count(existing) > 0:
        G.log("Skip body %s (collision already present)" % key)
        return True
    ui = _fbx_options(False)
    ui.set_editor_property("import_materials", False)
    ui.set_editor_property("import_textures", False)
    options = ui if LEGACY else (_interchange_pipeline() or ui)
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", src)
    task.set_editor_property("destination_path", entry["dest"])
    task.set_editor_property("destination_name", entry["main_mesh"])
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("automated", True)
    task.set_editor_property("save", False)
    task.set_editor_property("options", options)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    mesh = unreal.EditorAssetLibrary.load_asset(main_path)
    n = _simple_collision_count(mesh) if mesh else 0
    G.log("Body import %s: %s collision primitives" % (key, n))
    unreal.EditorAssetLibrary.save_directory(entry["dest"], only_if_is_dirty=False, recursive=True)
    return n > 0


def _import_fbx(key, entry, is_building):
    src = os.path.join(G.project_dir(), entry["source"].replace("/", os.sep))
    if not os.path.isfile(src):
        raise G.GenError("Source FBX missing: %s" % src)
    dest = entry["dest"]
    probe = entry.get("ue_path") or (dest + "/" + entry.get("main_mesh", ""))
    if not FORCE and unreal.EditorAssetLibrary.does_asset_exist(probe):
        G.log("Skip %s (already imported)" % key)
        return True
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", src)
    task.set_editor_property("destination_path", dest)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("automated", True)
    task.set_editor_property("save", False)
    task.set_editor_property("options", _fbx_options(is_building))
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    paths = [str(p) for p in task.get_editor_property("imported_object_paths")]
    G.log("Imported %s: %d asset(s)" % (key, len(paths)))
    for p in paths:
        G.log("    %s" % p)
    if not paths:
        return False
    if not is_building:
        # Tripo node names are random; rename the (single) static mesh to the key.
        meshes = [p for p in paths if isinstance(unreal.EditorAssetLibrary.load_asset(p), unreal.StaticMesh)]
        if len(meshes) >= 1:
            target = entry["ue_path"]
            if meshes[0].split(".")[0] != target:
                if not unreal.EditorAssetLibrary.rename_asset(meshes[0].split(".")[0], target):
                    G.warn("Rename to %s failed" % target)
    unreal.EditorAssetLibrary.save_directory(dest, only_if_is_dirty=False, recursive=True)
    return True


def _import_textures(cfg):
    ok = True
    src_dir = os.path.join(G.project_dir(), cfg["source_dir"].replace("/", os.sep))
    dest = cfg["dest"]
    suffixes = cfg["suffixes"]
    tasks = []
    for s in cfg["sets"]:
        for suf in suffixes:
            f = os.path.join(src_dir, "T_%s_%s.png" % (s, suf))
            asset_path = "%s/T_%s_%s" % (dest, s, suf)
            if not os.path.isfile(f):
                G.err("Texture file missing: %s" % f)
                ok = False
                continue
            if not FORCE and unreal.EditorAssetLibrary.does_asset_exist(asset_path):
                continue
            t = unreal.AssetImportTask()
            t.set_editor_property("filename", f)
            t.set_editor_property("destination_path", dest)
            t.set_editor_property("replace_existing", True)
            t.set_editor_property("automated", True)
            t.set_editor_property("save", False)
            tasks.append(t)
    if tasks:
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
    # Per-type texture settings
    for s in cfg["sets"]:
        for suf in suffixes:
            tex = unreal.EditorAssetLibrary.load_asset("%s/T_%s_%s" % (dest, s, suf))
            if tex is None:
                G.err("Texture not found after import: T_%s_%s" % (s, suf))
                ok = False
                continue
            if suf == "BC":
                tex.set_editor_property("srgb", True)
            elif suf == "N":
                tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP)
                tex.set_editor_property("srgb", False)
                tex.set_editor_property("flip_green_channel", True)   # files are OpenGL, UE wants DirectX
            elif suf == "ORM":
                tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_MASKS)
                tex.set_editor_property("srgb", False)
    unreal.EditorAssetLibrary.save_directory(dest, only_if_is_dirty=False, recursive=True)
    return ok


def main():
    global LEGACY
    G.init_log("p00_import_assets")
    LEGACY = _prefer_legacy_fbx()
    try:
        assets = G.load_json("assets.json")
        ok_b = True
        for key, entry in assets["buildings"].items():
            try:
                ok_b &= _import_fbx(key, entry, True)
                ok_b &= _import_body(key, entry)
            except G.GenError as e:
                G.err(str(e)); ok_b = False
        G.verify("import_buildings", ok_b, "%d buildings" % len(assets["buildings"]))

        ok_n = True
        for key, entry in assets["nature"].items():
            try:
                ok_n &= _import_fbx(key, entry, False)
            except G.GenError as e:
                G.err(str(e)); ok_n = False
        G.verify("import_nature", ok_n, "%d models" % len(assets["nature"]))

        G.verify("import_textures", _import_textures(assets["textures"]),
                 "%d textures" % (len(assets["textures"]["sets"]) * len(assets["textures"]["suffixes"])))
    except G.GenError as e:
        G.err(str(e))
        G.verify("p00_fatal", False, str(e))
    except Exception as e:
        G.err("Unexpected: %r" % e)
        G.verify("p00_unexpected", False, repr(e))
    G.summary()


main()
