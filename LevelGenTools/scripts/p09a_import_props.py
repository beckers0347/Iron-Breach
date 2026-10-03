"""p09a_import_props.py - import the 10 Blender prop FBX files and assign their materials.

Run (after p07 has built the M_* materials - re-run p07 first so M_Wood exists):
  py "X:/IronBreach/LevelGenTools/scripts/p09a_import_props.py"

Each FBX is ONE mesh plus a UCX_ box, imported with Combine Meshes on so UE keeps the collision.

Look for:
  [Thornfield] VERIFY: props_imported PASS (10 of 10)
  [Thornfield] VERIFY: props_collision PASS
  [Thornfield] VERIFY: props_materials PASS
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib
import unreal
import gen_common as G
importlib.reload(G)

FORCE = False


def _prim_count(mesh):
    try:
        agg = mesh.get_editor_property("body_setup").get_editor_property("agg_geom")
        return sum(len(agg.get_editor_property(p)) for p in ("convex_elems", "box_elems", "sphere_elems", "sphyl_elems"))
    except Exception:
        return 0


def _options():
    ui = unreal.FbxImportUI()
    ui.set_editor_property("import_mesh", True)
    ui.set_editor_property("import_as_skeletal", False)
    ui.set_editor_property("import_animations", False)
    ui.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_STATIC_MESH)
    ui.set_editor_property("import_materials", False)
    ui.set_editor_property("import_textures", False)
    sm = ui.static_mesh_import_data
    sm.set_editor_property("combine_meshes", True)
    sm.set_editor_property("auto_generate_collision", False)
    sm.set_editor_property("one_convex_hull_per_ucx", True)
    sm.set_editor_property("generate_lightmap_u_vs", False)
    try:
        sm.set_editor_property("build_nanite", False)    # tiny props: no Nanite needed
    except Exception:
        pass
    return ui


def main():
    G.init_log("p09a_import_props")
    try:
        # legacy FBX importer (Interchange drops UCX collision) - same switch as p00
        try:
            unreal.SystemLibrary.execute_console_command(None, "Interchange.FeatureFlags.Import.FBX 0")
        except Exception as e:
            G.warn("console command failed: %r" % e)
        assets = G.load_json("assets.json")
        mcfg = G.load_json("materials.json")
        props = assets["props"]
        dest = None
        ok, no_collision, bad_mat = 0, [], []
        for key, e in props.items():
            src = os.path.join(G.project_dir(), e["source"].replace("/", os.sep))
            if not os.path.isfile(src):
                G.err("Prop FBX missing: %s" % src)
                continue
            dest = e["dest"]
            name = e["ue_path"].rsplit("/", 1)[1]
            if FORCE or not unreal.EditorAssetLibrary.does_asset_exist(e["ue_path"]):
                t = unreal.AssetImportTask()
                t.set_editor_property("filename", src)
                t.set_editor_property("destination_path", dest)
                t.set_editor_property("destination_name", name)
                t.set_editor_property("replace_existing", True)
                t.set_editor_property("automated", True)
                t.set_editor_property("save", False)
                t.set_editor_property("options", _options())
                unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
            mesh = unreal.EditorAssetLibrary.load_asset(e["ue_path"])
            if mesh is None:
                G.err("Import failed: %s" % key)
                continue
            ok += 1
            n = _prim_count(mesh)
            if n <= 0:
                no_collision.append(key)
            for i, sm in enumerate(mesh.static_materials):
                slot = str(sm.material_slot_name)
                mat = unreal.EditorAssetLibrary.load_asset("%s/%s" % (mcfg["dest"], slot))
                if mat is None:
                    bad_mat.append("%s:%s" % (key, slot))
                    continue
                mesh.set_material(i, mat)
            mesh.modify()
            unreal.EditorAssetLibrary.save_loaded_asset(mesh)
            size, origin = G.get_bounds(mesh)
            G.log("%s: bounds %s, %d collision primitives, %d slots" % (key, G.fmt_size(size), n, len(mesh.static_materials)))
        G.verify("props_imported", ok == len(props), "%d of %d" % (ok, len(props)))
        G.verify("props_collision", not no_collision, "all have UCX collision" if not no_collision else "none on %s" % no_collision)
        G.verify("props_materials", not bad_mat, "all slots mapped" if not bad_mat else "missing materials %s (re-run p07_materials.py)" % sorted(set(bad_mat)))
    except G.GenError as e:
        G.err(str(e))
        G.verify("p09a_fatal", False, str(e))
    except Exception as e:
        G.err("Unexpected: %r" % e)
        G.verify("p09a_unexpected", False, repr(e))
    G.summary()


main()
